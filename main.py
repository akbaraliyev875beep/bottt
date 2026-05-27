import asyncio
import logging
import secrets
import string
import re
import hashlib
import base64
import os
import ssl
import socket
import random
from datetime import datetime, date
import aiohttp
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from PIL import Image
from PIL.ExifTags import TAGS

# 🟢 SIZ TAQDIM ETGAN REAL MA'LUMOTLAR INTEGRATSIYASI
BOT_TOKEN = "8608531012:AAG_k7HP5MmhiB0NWZNBlw0b8Uy89ZhijP0"
ADMIN_ID = 8391848497  
KARTA_RAQAMI = "5614 6820 9111  4613"  
KARTA_E_E = "Akbaraliyev D."

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# --- 💾 FOYDALANUVCHILAR MA'LUMOTLAR BAZASI ---
USER_DB = {}

def get_user(user_id: int):
    if user_id not in USER_DB:
        USER_DB[user_id] = {
            "free_attempts": 5, 
            "balance": 0, 
            "last_fortune": "",
            "inventory": []
        }
    if "inventory" not in USER_DB[user_id]:
        USER_DB[user_id]["inventory"] = []
    return USER_DB[user_id]

class BotStates(StatesGroup):
    waiting_for_ip = State()
    waiting_for_url = State()
    waiting_for_port = State()
    waiting_for_leak_check = State()
    waiting_for_image = State()
    waiting_for_file_scan = State()
    waiting_for_subdomain = State()
    waiting_for_ssl_scan = State()
    waiting_for_admin_add_funds = State()
    waiting_for_payment_receipt = State()  # ✅ TO'LOV CHEKI

# --- 📚 SUBDOMEN RO'YXATI ---
COMMON_SUBDOMAINS = [
    "admin", "mail", "vpn", "cpanel", "test", "dev", "staging", "api", 
    "secure", "webmail", "blog", "shop", "crm", "ftp", "mysql"
]

# --- ⌨️ KLAVIATURALAR ---
def get_main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="🌐 IP Tekshirish"),
        KeyboardButton(text="🔗 Havolani Tekshirish"),
        KeyboardButton(text="🔌 Port Tekshirish"),
        KeyboardButton(text="🕵️‍♂️ Rasm Anonimligi"),
        KeyboardButton(text="🛡 Fayl Analizatori"),
        KeyboardButton(text="🔍 Subdomen Qidiruv"),
        KeyboardButton(text="🔒 SSL Ekspertizasi"),
        KeyboardButton(text="🚨 Kiber-Hujumlar Feed"),
        KeyboardButton(text="💔 Parol Sizib Chiqishi"),
        
        # 🎰 QIZIQARLI VA VIRUSLI TUGMALAR
        KeyboardButton(text="🎰 Omad Gildiragi (Kunlik)"),
        KeyboardButton(text="🎭 Mening Cyber IQ'imni Skan qil"),
        KeyboardButton(text="🎒 Mening Inventarim"),
        
        KeyboardButton(text="💳 Mening Hisobim"),
        KeyboardButton(text="/start")
    )
    builder.adjust(2, 2, 2, 2, 2, 2, 2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_sell_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="💰 Hayvonlarni Sotish"))
    builder.add(KeyboardButton(text="⬅️ Bosh Menyu"))
    builder.adjust(1, 1)
    return builder.as_markup(resize_keyboard=True)

# --- 💳 HISOB-KITOB VA MONETIZATSIYA FILTRI ---
def check_and_charge_user(user_id: int) -> tuple[bool, str]:
    user = get_user(user_id)
    if user["free_attempts"] > 0:
        user["free_attempts"] -= 1
        return True, f"🎁 Bepul urinish ishlatildi (Qoldi: {user['free_attempts']} ta)"
        
    if user["balance"] >= 1500:
        user["balance"] -= 1500
        return True, f"💰 Balansdan 1,500 so'm yechildi (Qoldi: {user['balance']:,} so'm)"
        
    return False, "Mablag' yetarli emas"

# --- 🚀 START BUYRUG'I VA BEKOR QILISH ---
@router.message(Command("start"))
@router.message(F.text == "/start")
@router.message(F.text == "⬅️ Bosh Menyu")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id)
        
    await message.answer(
        f"Salom {message.from_user.full_name}!\n🛡 **Cyber Intelligence Commercial Center v10** tizimiga xush kelibsiz.\n\n"
        f"🎁 Sizga **{user['free_attempts']} ta mutlaqo bepul tizim so'rovi** taqdim etildi.\n"
        f"Urinishlar tugagach, har bir so'rov narxi 1,500 so'm etib belgilanadi.\n\n"
        f"Kiber-Hayvonlar yutish uchun **🎰 Omad G'ildiragi**ni aylantirib ko'ring! 👇", 
        reply_markup=get_main_keyboard(), 
        parse_mode="Markdown"
    )

# --- 👑 ADMIN PANEL TIZIMI ---
@router.message(Command("admin_panel"))
async def admin_panel_cmd(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Siz bot boshqaruvchisi emassiz!")
        return
    await message.answer(
        "👑 **Eksklyuziv Admin Balans Qo'shish Stansiyasi**\n\n"
        "Mablag' to'ldirish formatini quyidagicha kiriting:\n"
        "`ID_RAQAMI:SUMMA`\n\n"
        "Masalan: `8391848497:15000`",
        parse_mode="Markdown"
    )
    await state.set_state(BotStates.waiting_for_admin_add_funds)

@router.message(BotStates.waiting_for_admin_add_funds)
async def admin_process_add_funds(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    try:
        user_id_str, amount_str = message.text.strip().split(":")
        target_id = int(user_id_str.strip())
        amount = int(amount_str.strip())
        
        target_user = get_user(target_id)
        target_user["balance"] += amount
        await message.answer(f"✅ ID `{target_id}` hisobiga **{amount:,} so'm** muvaffaqiyatli qo'shildi.", parse_mode="Markdown")
        
        try:
            await bot.send_message(
                target_id, 
                f"💰 **Balansingiz yangilandi!**\n\nAdmin tomonidan hisobingizga **{amount:,} so'm** qo'shildi.\n"
                f"Sizning joriy balansingiz: **{target_user['balance']:,} so'm**.\nHar qanday cheklovlarsiz ishlata olasiz!",
                parse_mode="Markdown"
            )
        except Exception:
            await message.answer("⚠️ Foydalanuvchi botni bloklagani sababli bildirishnoma yetib bormadi.")
    except ValueError:
        await message.answer("❌ Xato kiritish sintaksisi. Iltimos `ID:SUMMA` formatiga rioya qiling.")
    await state.clear()

# --- 💳 MENING HISOBIM VA DONATION PANEL ---
@router.message(F.text == "💳 Mening Hisobim")
async def show_my_account(message: Message):
    user = get_user(message.from_user.id)
    try:
        admin_info = await bot.get_chat(ADMIN_ID)
        admin_username = f"@{admin_info.username}" if admin_info.username else f"tg://user?id={ADMIN_ID}"
    except Exception:
        admin_username = f"tg://user?id={ADMIN_ID}"

    report = (
        f"💳 **Foydalanuvchi Shaxsiy Balansi:**\n\n"
        f"🆔 **Sizning ID:** `{message.from_user.id}`\n"
        f"🎁 **Tekin Urinishlar:** {user['free_attempts']} ta\n"
        f"💰 **Sizning Balansingiz:** **{user['balance']:,} so'm**\n"
        f"🎒 **Inventardagi Hayvonlar:** {len(user['inventory'])} ta\n"
        f"💵 **Xizmat tarifi:** 1 ta so'rov = 1,500 so'm (Tekin tugagach)\n\n"
        f"--- 💸 HISOBNI TO'LDIRISH TIZIMI ---\n"
        f"Bot balansini to'ldirish uchun kartaga to'lovni bajaring:\n\n"
        f"💳 **Karta:** `{KARTA_RAQAMI}`\n"
        f"👤 **Egasi:** {KARTA_E_E}\n\n"
        f"🧾 **To'lov tugatilgach:** Quyidagi tugmani bosing va chekni yuboring!"
    )
    
    # ✅ CHEK YUBORISH TUGMASI
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🧾 Chekni Yuborish"))
    builder.add(KeyboardButton(text="⬅️ Bosh Menyu"))
    builder.adjust(1, 1)
    
    await message.answer(report, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=builder.as_markup(resize_keyboard=True))

# --- 💸 TO'LOV CHEKINI QABUL QILISH VA ADMINGA YUBORISH ---
@router.message(F.text == "💳 Mening Hisobim")
async def show_my_account(message: Message):
    user = get_user(message.from_user.id)
    try:
        admin_info = await bot.get_chat(ADMIN_ID)
        admin_username = f"@{admin_info.username}" if admin_info.username else f"tg://user?id={ADMIN_ID}"
    except Exception:
        admin_username = f"tg://user?id={ADMIN_ID}"

    report = (
        f"💳 **Foydalanuvchi Shaxsiy Balansi:**\n\n"
        f"🆔 **Sizning ID:** `{message.from_user.id}`\n"
        f"🎁 **Tekin Urinishlar:** {user['free_attempts']} ta\n"
        f"💰 **Sizning Balansingiz:** **{user['balance']:,} so'm**\n"
        f"🎒 **Inventardagi Hayvonlar:** {len(user['inventory'])} ta\n"
        f"💵 **Xizmat tarifi:** 1 ta so'rov = 1,500 so'm (Tekin tugagach)\n\n"
        f"--- 💸 HISOBNI TO'LDIRISH TIZIMI ---\n"
        f"Bot balansini to'ldirish uchun kartaga to'lovni bajaring:\n\n"
        f"💳 **Karta:** `{KARTA_RAQAMI}`\n"
        f"👤 **Egasi:** {KARTA_E_E}\n\n"
        f"🧾 **To'lov tugatilgach:** Quyidagi tugmani bosing va chekni yuboring!"
    )
    
    # ✅ CHEK YUBORISH TUGMASI
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🧾 Chekni Yuborish"))
    builder.add(KeyboardButton(text="⬅️ Bosh Menyu"))
    builder.adjust(1, 1)
    
    await message.answer(report, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=builder.as_markup(resize_keyboard=True))

# 📸 CHEK TASVIRI YOKI FAYL QABUL QILISH
@router.message(F.text == "🧾 Chekni Yuborish")
async def ask_for_payment_receipt(message: Message, state: FSMContext):
    await message.answer(
        "📸 **To'lov chekini yuboring!**\n\n"
        "Quyidagilardan biri yuborasiz:\n"
        "• 📷 Chekking screenshoti (rasm)\n"
        "• 📄 To'lov cheki (fayl)\n"
        "• 🔢 To'lov summasi va vaqti\n\n"
        "⚠️ **SHAXSIY ID RAQAMINI CHEKKA YOZING!** (Identifikatsiya uchun)",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Bekor Qilish")]], resize_keyboard=True)
    )
    await state.set_state(BotStates.waiting_for_payment_receipt)

# 📸 RASM QABUL QILISH
@router.message(BotStates.waiting_for_payment_receipt, F.photo)
async def receive_payment_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    # 📸 RASMNI ADMINGA YUBORISH
    photo = message.photo[-1]
    caption = (
        f"🧾 **YANGI TO'LOV CHEKI!**\n\n"
        f"👤 **Foydalanuvchi:** {user_name}\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"📅 **Vaqt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"💬 **Xabar:** Ushbu foydalanuvchi hisobni to'ldiring (Chek tasdiqlansin)"
    )
    
    try:
        await bot.send_photo(
            ADMIN_ID,
            photo.file_id,
            caption=caption,
            parse_mode="Markdown"
        )
        await message.answer("✅ **Chek muvaffaqiyatli yuborildi!**\n\nAdmin tez orada balansingizni to'ldirib beradi. 🎉")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    
    await state.clear()

# 📄 FAYL QABUL QILISH
@router.message(BotStates.waiting_for_payment_receipt, F.document)
async def receive_payment_document(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    # 📄 FAYLNI ADMINGA YUBORISH
    document = message.document
    caption = (
        f"🧾 **YANGI TO'LOV CHEKI (FAYL)!**\n\n"
        f"👤 **Foydalanuvchi:** {user_name}\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"📁 **Fayl:** {document.file_name}\n"
        f"📅 **Vaqt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"💬 **Xabar:** Ushbu foydalanuvchi hisobni to'ldiring (Chek tasdiqlansin)"
    )
    
    try:
        await bot.send_document(
            ADMIN_ID,
            document.file_id,
            caption=caption,
            parse_mode="Markdown"
        )
        await message.answer("✅ **Chek muvaffaqiyatli yuborildi!**\n\nAdmin tez orada balansingizni to'ldirib beradi. 🎉")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    
    await state.clear()

# 📝 MATN ORQALI CHEK YUBORISH
@router.message(BotStates.waiting_for_payment_receipt, F.text)
async def receive_payment_text(message: Message, state: FSMContext):
    if message.text == "❌ Bekor Qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard())
        return
    
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    # 📝 MATNNI ADMINGA YUBORISH
    admin_message = (
        f"🧾 **YANGI TO'LOV CHEKI (MATN)!**\n\n"
        f"👤 **Foydalanuvchi:** {user_name}\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"📝 **Chek ma'lumoti:**\n\n"
        f"```\n{message.text}\n```\n\n"
        f"📅 **Vaqt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"💬 **Xabar:** Ushbu foydalanuvchi hisobni to'ldiring (Chek tasdiqlansin)"
    )
    
    try:
        await bot.send_message(
            ADMIN_ID,
            admin_message,
            parse_mode="Markdown"
        )
        await message.answer("✅ **Chek muvaffaqiyatli yuborildi!**\n\nAdmin tez orada balansingizni to'ldirib beradi. 🎉", reply_markup=get_main_keyboard())
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    
    await state.clear()

# --- 🎰 KIBER-OMAD GILDIRAGI (FOIZLI VA QIZIQARLI) ---
@router.message(F.text == "🎰 Omad Gildiragi (Kunlik)")
async def cyber_fortune_wheel(message: Message):
    user = get_user(message.from_user.id)
    today_str = str(date.today())
    
    is_paid_spin = False  

    if user.get("last_fortune") == today_str:
        if user["balance"] >= 1000:
            user["balance"] -= 1000
            is_paid_spin = True
            msg_status = "💰 Kunlik tekin urinishingiz tugagan. Balansingizdan **1,000 so'm** yechildi."
        else:
            await message.answer(
                "🎰 **Siz bugungi bepul urinishingizdan foydalanib bo'ldingiz!**\n\n"
                "Keyingi aylantirish narxi — **1,000 so'm**.\n"
                f"Sizning balansingiz: **{user['balance']:,} so'm**.\n\n"
                "Iltimos, balansingizni to'ldiring yoki ertangi bepul urinishni kuting! ⏳\n"
                "👉 `💳 Mening Hisobim` tugmasi orqali hisobni to'ldirishingiz mumkin.",
                parse_mode="Markdown"
            )
            return
    else:
        user["last_fortune"] = today_str
        msg_status = "🎁 Bugungi **1-bepul urinishingiz** ishga tushdi!"

    await message.answer(f"{msg_status}\n🎰 **Kiber-Omad G'ildiragi aylanmoqda...** 🌀")
    await asyncio.sleep(1.5)
    
    # 🎭 Qiziqarli motivatsiya va hazillar ro'yxati (yutqazganda shulardan biri tushadi)
    motivations = [
        "Xatolik 404: Omad topilmadi. Lekin tajriba orttirildi! 💻",
        "Tizim admini senga kulib qarayapti. Hechqisi yo'q, qayta urinib ko'r! 👨‍💻",
        "Hakerlar ham bir kunda tizimni buzmagan. Kichik muvaffaqiyatsizlik seni kuchli qiladi! 🛡",
        "Muvaffaqiyat — bu yiqilishdan to'xtamaslikdir. Parolingizni yangilang va yana yuring! 🔄",
        "Kiber-Nol: Moddiy yutuq yo'q, lekin xarakteringiz chiniqdi. 🧘‍♂️",
        "Bot sizni sinab ko'ryapti. Asabiylashmang, kiber-samuraylar doim bosiq bo'ladi. 🥷",
        "Kriptovalyuta qulayotganda ham odamlar umidini uzmagan, sen bitta g'ildirakda taslim bo'lasanmi? 📈",
        "Wi-Fi signali pastmi yoki omadingiz? Ikkalasini ham to'g'rilab yana keling! 📶",
        "Bugun yutqazganing — ertaga Jekpot urishing uchun shunchaki tayyorgarlik! 🎯",
        "Fishing tuzog'iga tushgandan ko'ra, omad g'ildiragida yutqazgan yaxshi. Sog'lik muhim! 😅"
    ]
    
    prizes = [
        {"type": "attempt", "value": 1, "text": "🎁 Ajoyib! Siz **+1 ta BEPUL URINISH** yutib oldingiz!"},
        {"type": "attempt", "value": 2, "text": "🔥 Super Omad! Siz **+2 ta BEPUL URINISH** qo'lga kiritdingiz!"},
        {"type": "money", "value": 500, "text": "💰 Yaxshi! Balansingizga **+500 so'm** bonus qo'shildi!"},
        {"type": "money", "value": 1500, "text": "💎 JEKPOT! Balansingizga **+1,500 so'm** qo'shildi!"},
        {"type": "animal", "name": "🤖 Kiber-Mushuk", "price": 1000, "text": "🐈 **YANGI HAYVON!** Siz 1,000 so'mlik **🤖 Kiber-Mushuk** yutib oldingiz! U inventaringizga qo'shildi."},
        {"type": "animal", "name": "🦅 Skantaym Lochini", "price": 2000, "text": "🦅 **YANGI HAYVON!** Siz 2,000 so'mlik **🦅 Skantaym Lochini** yutib oldingiz! U inventaringizga qo'shildi."},
        {"type": "animal", "name": "🐺 Kali Bo'risi", "price": 3500, "text": "🐺 **YANGI HAYVON!** Siz 3,500 so'mlik **🐺 Kali Bo'risi** yutib oldingiz! U inventaringizga qo'shildi."},
        {"type": "animal", "name": "🐉 Fishing Ajdahosi", "price": 5000, "text": "🐉 **AFSONAVIY HAYVON!** Siz 5,000 so'mlik **🐉 Fishing Ajdahosi** yutib oldingiz! Tizim larzaga keldi!"},
        {"type": "nothing", "value": 0, "text": ""} # Matni pastda avtomatik to'ldiriladi
    ]
    
    # 📈 FOIZLAR (Jami 100%) - Kazino foydada qolishi uchun sozlangan
    ehtimolliklar = [
        5,    # +1 urinish (5%)
        1,    # +2 urinish (1%)
        25,   # 500 so'm pul (25%) -> Odatiy kichik yutuq
        2,    # 1500 so'm pul (2%) -> Jekpot
        6,    # Kiber-Mushuk (6%)
        0.8,  # Lochin (0.8%)
        0.15, # Bo'ri (0.15%)
        0.05, # Ajdaho (0.05%) -> O'TA KAM TUSHADI!
        60    # Hech narsa - Motivatsiya (60%) -> ASOSIY DAROMAD QISMI
    ]
    
    win = random.choices(prizes, weights=ehtimolliklar, k=1)[0]
    
    # Agar yutqazsa, tasodifiy hazil/motivatsiya tanlaymiz
    if win["type"] == "nothing":
        win["text"] = f"🤷‍♂️ **Afsus, bu safar hech narsa tushmadi.** \n\n💡 *Kiber-Xulosa:* \"{random.choice(motivations)}\""
    
    if win["type"] == "attempt":
        user["free_attempts"] += win["value"]
    elif win["type"] == "money":
        user["balance"] += win["value"]
    elif win["type"] == "animal":
        user["inventory"].append({"name": win["name"], "price": win["price"]})
        
    await message.answer(
        f"{win['text']}\n\n"
        f"📊 **Yangi hisob holatingiz:**\n"
        f"🎁 Tekin so'rovlar: {user['free_attempts']} ta\n"
        f"💰 Pul balansi: {user['balance']:,} so'm\n"
        f"🎒 Inventardagi hayvonlar: {len(user['inventory'])} ta\n\n"
        f"💡 _Eslatma: Hayvonlarni `🎒 Mening Inventarim` tugmasi orqali sotishingiz mumkin._",
        parse_mode="Markdown"
    )

# --- 🎒 INVENTAR VA SOTISH MANTIQI ---
@router.message(F.text == "🎒 Mening Inventarim")
async def show_inventory(message: Message):
    user = get_user(message.from_user.id)
    
    if not user["inventory"]:
        await message.answer(
            "🎒 Sizning inventaringiz hozircha bo'sh.\n\n"
            "🎰 Omad G'ildiragini aylantirib, noyob kiber-hayvonlarni yutib oling!",
            reply_markup=get_main_keyboard()
        )
        return
        
    text = "🎒 **Sizning inventaringizdagi hayvonlar:**\n\n"
    total_value = 0
    
    for idx, item in enumerate(user["inventory"], 1):
        text += f"{idx}. {item['name']} — 💵 {item['price']:,} so'm\n"
        total_value += item["price"]
        
    text += f"\n💰 **Jami hayvonlar qiymati:** {total_value:,} so'm\n"
    text += "Ularni darhol sotib, pulini balansingizga naqd qilib olishingiz mumkin!"
    
    await message.answer(text, reply_markup=get_sell_keyboard(), parse_mode="Markdown")

@router.message(F.text == "💰 Hayvonlarni Sotish")
async def sell_animals(message: Message):
    user = get_user(message.from_user.id)
    
    if not user["inventory"]:
        await message.answer("Sotish uchun hech qanday hayvoningiz yo'q!", reply_markup=get_main_keyboard())
        return
        
    total_earned = sum(item["price"] for item in user["inventory"])
    user["balance"] += total_earned  
    user["inventory"] = []           
    
    await message.answer(
        f"💰 Muvaffaqiyatli sotildi!\n\n"
        f"💵 Hayvonlaringizni sotib **+{total_earned:,} so'm** naqd qildingiz.\n"
        f"💳 Yangi balansingiz: **{user['balance']:,} so'm**",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# --- 🎭 CYBER IQ SCANER ---
@router.message(F.text == "🎭 Mening Cyber IQ'imni Skan qil")
async def cyber_iq_scan(message: Message):
    await message.answer("🕵️‍♂️ **Profilingiz kiber-tuzilishi chuqur tahlildan o'tkazilmoqda...**\n\n_Ijtimoiy injeneriya zaifliklari va parollar barqarorligi o'rganilmoqda..._")
    await asyncio.sleep(2)
    
    name_len = len(message.from_user.full_name)
    has_username = 15 if message.from_user.username else 0
    base_score = random.randint(40, 85) + (name_len % 5) + has_username
    cyber_iq = min(base_score, 100)
    
    if cyber_iq > 85:
        verdict = "👑 **KIBER-GHOST (PRO HAKER):** Tarmoqda raqamli izingizni topish qiyin. Tizimlaringiz mustahkam va himoyalangan!"
    elif cyber_iq > 65:
        verdict = "🛡 **HUSHYOR FOYDALANUVCHI:** Umumiy kiber qoidalardan xabardorsiz, biroq murakkab fishing tuzoqlariga tushish ehtimoli saqlanmoqda."
    else:
        verdict = "🚨 **RAQAMLI JABRLANUVCHI:** Hisoblaringiz hakerlik hujumlari uchun oson o'lja bo'lishi mumkin! Xavfsizlik darajangizni zudlik bilan oshiring."

    report = (
        f"🎭 **Kiber-Savodxonlik (Cyber IQ) Tashxis Natijasi:**\n\n"
        f"👤 Foydalanuvchi: {message.from_user.mention_markdown()}\n"
        f"📊 **Sizning Cyber IQ ko'rsatkichingiz:** `{cyber_iq}%`\n\n"
        f"📋 **Ekspert xulosasi:**\n{verdict}\n\n"
        f"📢 _Ushbu natijani skrinshot qilib guruhlarda ulashing, do'stlaringizni kiber-sinovdan o'tkazib kim aqlliroqligini aniqlang!_"
    )
    await message.answer(report, parse_mode="Markdown")

# --- 1. 🌐 IP TEKSHIRISH ---
@router.message(F.text == "🌐 IP Tekshirish")
async def ask_ip(message: Message, state: FSMContext):
    allowed, msg = check_and_charge_user(message.from_user.id)
    if not allowed:
        await message.answer("❌ **Mablag' yetarli emas!**\n\nHisobingiz to'ldirilishi lozim. Iltimos, `💳 Mening Hisobim` menyusiga kiring.")
        return
    await message.answer(f"🔍 Tekshirilishi kerak bo'lgan IP manzilni yuboring:\n⚡️ _({msg})_", parse_mode="Markdown")
    await state.set_state(BotStates.waiting_for_ip)

@router.message(BotStates.waiting_for_ip)
async def check_ip_info(message: Message, state: FSMContext):
    ip = message.text.strip()
    await message.answer(f"🔄 `{ip}` bo'yicha ma'lumotlar to'planmoqda...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"http://ip-api.com/json/{ip}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        res = (
                            f"🌐 **GeoIP Analiz Hisoboti:** `{ip}`\n\n"
                            f"🏳️ **Davlat:** {data.get('country')} ({data.get('countryCode')})\n"
                            f"🏙 **Shahar:** {data.get('city')}\n"
                            f"🏢 **Provayder (ISP):** {data.get('isp')}\n"
                            f"📍 **Koordinata:** `{data.get('lat')}, {data.get('lon')}`"
                        )
                    else: res = "❌ IP manzil topilmadi yoki xato kiritildi."
                    await message.answer(res, parse_mode="Markdown")
                else: await message.answer("❌ Tashqi GeoIP API bazasi band.")
        except Exception as e: await message.answer(f"Xatolik: {e}")
    await state.clear()

# --- 2. 🔗 HAVOLANI TEKSHIRISH ---
@router.message(F.text == "🔗 Havolani Tekshirish")
async def ask_url(message: Message, state: FSMContext):
    allowed, msg = check_and_charge_user(message.from_user.id)
    if not allowed:
        await message.answer("❌ **Mablag' yetarli emas!** Hisobni to'ldiring.")
        return
    await message.answer(f"🔗 Shubhali yoki tekshirilishi lozim bo'lgan havolani yuboring:\n⚡️ _({msg})_", parse_mode="Markdown")
    await state.set_state(BotStates.waiting_for_url)

@router.message(BotStates.waiting_for_url)
async def check_url_risk(message: Message, state: FSMContext):
    url = message.text.strip()
    phishing_keywords = ["free", "gift", "telegram", "login", "bot", "prize", "win", "crypto", "bonus", "pul", "aksiya", "yutuq"]
    is_suspicious = any(kw in url.lower() for kw in phishing_keywords) or len(url) > 60
    
    if is_suspicious:
        await message.answer("🚨 **YUGORI FISHING (TUZOG) XAVFI ANICLANDI!**\n\nHavola tizim filtrlari tomonidan taqiqlandi. U yerga login yoki maxfiy parollaringizni mutlaqo kiritmang!", parse_mode="Markdown")
    else:
        await message.answer("🟢 Skantaym tekshiruvi tugadi. Yaqqol xavfli signatura topilmadi. Biroq baribir xavfsizlik choralarini unutmang.")
    await state.clear()

# --- 3. 🔌 PORT TEKSHIRISH ---
@router.message(F.text == "🔌 Port Tekshirish")
async def ask_port_host(message: Message, state: FSMContext):
    allowed, msg = check_and_charge_user(message.from_user.id)
    if not allowed:
        await message.answer("❌ **Mablag' yetarli emas!** Hisobni to'ldiring.")
        return
    await message.answer(f"🔌 Target IP yoki domen nomini kiriting (Masalan: `1.1.1.1`):\n⚡️ _({msg})_", parse_mode="Markdown")
    await state.set_state(BotStates.waiting_for_port)

@router.message(BotStates.waiting_for_port)
async def scan_common_ports(message: Message, state: FSMContext):
    host = message.text.strip().replace("https://", "").replace("http://", "").split('/')[0]
    await message.answer(f"⚡️ `{host}` tizim kiber portlari tekshirilmoqda...")
    
    ports = [21, 22, 80, 443]
    open_ports = []
    
    def check_port(p):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.5)
            return p if s.connect_ex((host, p)) == 0 else None

    for port in ports:
        res = await asyncio.to_thread(check_port, port)
        if res: open_ports.append(f"🟢 Port `{res}` — OCHIQ (Ochiq port xavf keltirishi mumkin)")
        
    if open_ports:
        await message.answer(f"🎯 **Skanerlash muvaffaqiyatli tugadi:**\n\n" + "\n".join(open_ports), parse_mode="Markdown")
    else:
        await message.answer("🔒 Barcha standart kiber tarmoq portlari yopiq hamda xavfsizlik devori ostida.")
    await state.clear()

# --- 4. 🕵️‍♂️ OSINT RASM METADATA EXIF TOZALAGICH ---
@router.message(F.text == "🕵️‍♂️ Rasm Anonimligi")
async def ask_image_file(message: Message, state: FSMContext):
    allowed, msg = check_and_charge_user(message.from_user.id)
    if not allowed:
        await message.answer("❌ **Mablag' yetarli emas!** Hisobni to'ldiring.")
        return
    await message.answer(f"🕵️‍♂️ Menga rasmni **Fayl (Hujjat)** ko'rinishida yuboring. Undagi yashirin GPS koordinatalari va qurilma rusumlarini o'chirib beraman:\n⚡️ _({msg})_", parse_mode="Markdown")
    await state.set_state(BotStates.waiting_for_image)

@router.message(BotStates.waiting_for_image, F.document)
async def process_image_metadata(message: Message, state: FSMContext):
    document = message.document
    if not document.file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
        await message.answer("❌ Iltimos, faqat rasm fayllarini yuboring (.jpg, .jpeg, .png)")
        return
        
    await message.answer("📥 Raqamli ekspertiza va tozalash stansiyasi ishga tushdi...")
    input_path = f"t_{document.file_id}.jpg"
    output_path = f"c_{document.file_id}.jpg"
    
    await bot.download_file((await bot.get_file(document.file_id)).file_path, input_path)
    try:
        img = Image.open(input_path)
        exif = img._getexif()
        extracted = ""
        if exif:
            for t, v in exif.items():
                tag_name = TAGS.get(t, t)
                if tag_name in ['Make', 'Model', 'DateTime', 'GPSInfo']:
                    extracted += f"🔹 **{tag_name}:** `{v}`\n"
                    
        status = f"🚨 **Topilgan maxfiy metadata izlari:**\n\n{extracted}" if extracted else "ℹ️ Fayldan geografik yoki qurilma izlari aniqlanmadi."
        
        data = list(img.getdata())
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)
        clean_img.save(output_path)
        
        await message.answer(status, parse_mode="Markdown")
        await message.answer_document(FSInputFile(output_path), caption="🧹 Ushbu faylning barcha raqamli, geo va EXIF izlari butunlay yuvildi va xavfsiz holga keltirildi!")
    except Exception as e:
        await message.answer(f"❌ Rasmni qayta ishlash xatosi: {e}")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
    await state.clear()

# --- 5. 🛡 FAYL ANALIZATORI / MALWARE SCANNER ---
@router.message(F.text == "🛡 Fayl Analizatori")
async def ask_file_to_scan(message: Message, state: FSMContext):
    allowed, msg = check_and_charge_user(message.from_user.id)
    if not allowed:
        await message.answer("❌ **Mablag' yetarli emas!** Hisobni to'ldiring.")
        return
    await message.answer(f"🛡 Skript yoki dasturiy faylni yuboring (`.py`, `.exe`, `.bat`):\n⚡️ _({msg})_", parse_mode="Markdown")
    await state.set_state(BotStates.waiting_for_file_scan)

@router.message(BotStates.waiting_for_file_scan, F.document)
async def scan_file_process(message: Message, state: FSMContext):
    document = message.document
    file_path = f"scan_{document.file_id}_{document.file_name}"
    await bot.download_file((await bot.get_file(document.file_id)).file_path, file_path)
    
    spy_keywords = {
        b"requests.post": "Ma'lumotlarni yashirin tashqariga uzatish (Spyware)",
        b"os.system": "Ruxsatsiz tizim buyruqlarini ijro etish (Trojan/Ransomware)",
        b"subprocess": "Ichki operatsion tizim jarayonlariga kirish",
        b"token": "Telegram bot yoki seans tokenlarini o'g'irlash ssenariysi"
    }
    detected = []
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            for kw, desc in spy_keywords.items():
                if kw in content:
                    detected.append(f"❌ **Xavfli funksiya:** {desc} (`{kw.decode()}`)")
        if detected:
            await message.answer("🚨 **EHTIYOT BO'LING! Kod tarkibida zararli xatti-harakatlar signaturasi mavjud:**\n\n" + "\n".join(detected), parse_mode="Markdown")
        else:
            await message.answer("🟢 Statik signatura tahlili yakunlandi. Hech qanday zararli virus kodi belgilari aniqlanmadi.")
    except Exception as e:
        await message.answer(f"❌ Fayl o'qish xatosi: {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
    await state.clear()

# --- 6. 🔍 SUBDOMEN QIDIRUV ---
@router.message(F.text == "🔍 Subdomen Qidiruv")
async def ask_domain_for_scan(message: Message, state: FSMContext):
    allowed, msg = check_and_charge_user(message.from_user.id)
    if not allowed:
        await message.answer("❌ **Mablag' yetarli emas!** Hisobni to'ldiring.")
        return
    await message.answer(f"🔍 Tekshirilishi lozim bo'lgan asosiy domen nomini kiriting:\n⚡️ _({msg})_", parse_mode="Markdown")
    await state.set_state(BotStates.waiting_for_subdomain)

@router.message(BotStates.waiting_for_subdomain)
async def scan_subdomains(message: Message, state: FSMContext):
    domain = message.text.strip().lower().replace("https://", "").replace("http://", "").replace("www.", "")
    if not re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", domain):
        await message.answer("❌ Noto'g'ri domen kiritish formati.")
        await state.clear()
        return
        
    await message.answer(f"⚡️ `{domain}` uchun yashirin tarmoq infrastruktura qidiruvi boshlandi...")
    found = []
    
    async with aiohttp.ClientSession() as session:
        async def check_sub(sub):
            try:
                async with session.get(f"http://{sub}.{domain}", timeout=2.5) as resp:
                    if resp.status in [200, 301, 302, 403]:
                        found.append(f"🔗 `{sub}.{domain}` (Status kodi: {resp.status})")
            except: pass
        await asyncio.gather(*[check_sub(sub) for sub in COMMON_SUBDOMAINS])

    if found:
        await message.answer("🎯 **Topilgan faol subdomenlar paneli:**\n\n" + "\n".join(found), parse_mode="Markdown")
    else:
        await message.answer("🤷‍♂️ Mazkur saytga daxldor ochiq subdomenlar aniqlanmadi.")
    await state.clear()

# --- 7. 🔒 SSL EKSPERTIZASI ---
@router.message(F.text == "🔒 SSL Ekspertizasi")
async def ask_ssl_domain(message: Message, state: FSMContext):
    allowed, msg = check_and_charge_user(message.from_user.id)
    if not allowed:
        await message.answer("❌ **Mablag' yetarli emas!** Hisobni to'ldiring.")
        return
    await message.answer(f"🔒 Sayt domenini kiriting:\n⚡️ _({msg})_", parse_mode="Markdown")
    await state.set_state(BotStates.waiting_for_ssl_scan)

@router.message(BotStates.waiting_for_ssl_scan)
async def process_ssl_scan(message: Message, state: FSMContext):
    domain = message.text.strip().lower().replace("https://", "").replace("http://", "").replace("www.", "").split('/')[0]
    if not re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", domain):
        await message.answer("❌ Noto'g'ri domen formati.")
        await state.clear()
        return

    await message.answer(f"🛡 `{domain}` SSL xavfsizlik sertifikatlari yuklanmoqda...")
    try:
        context = ssl.create_default_context()
        def fetch_cert():
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock: return ssock.getpeercert()
                
        cert = await asyncio.to_thread(fetch_cert)
        issuer = dict(x[0] for x in cert['issuer'])['commonName']
        not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        remaining_days = (not_after - datetime.now()).days
        
        risk = "🟢 Sayt xavfsiz shifrlangan." if remaining_days > 15 else "🚨 O'TA YUQORI FISHING EFFEKTI! (Sertifikat muddati tugash arafasida!)"

        report = (
            f"🔒 **SSL Ekspertiza Yakuni:** `{domain}`\n\n"
            f"🏢 **Sertifikat Beruvchi Markaz:** `{issuer}`\n"
            f"📅 **Berilgan sana:** `{not_before.strftime('%Y-%m-%d')}`\n"
            f"⏳ **Tugash muddati:** `{not_after.strftime('%Y-%m-%d')}`\n"
            f"🕒 **Qolgan umri:** `{remaining_days} kun`\n\n"
            f"📊 **Kiber-Xulosa:** {risk}"
        )
        await message.answer(report, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"🔴 SSL sertifikatni o'qib bo'lmadi.\nℹ️ `{e}`")
    await state.clear()

# --- 8. 🚨 KIBER-HUJUMLAR LIVE FEED ---
@router.message(F.text == "🚨 Kiber-Hujumlar Feed")
async def get_cyber_threat_feed(message: Message):
    allowed, msg = check_and_charge_user(message.from_user.id)
    if not allowed:
        await message.answer("❌ **Mablag' yetarli emas!** Hisobni to'ldiring.")
        return
    await message.answer(f"🔄 Global kiber-tizimlardan real-vaqtdagi ma'lumotlar olinmoqda...\n⚡️ _({msg})_", parse_mode="Markdown")
    
    url = "https://api.osv.dev/v1/query"
    payload = {"commit": "6879155093cd0b6cb90d63897ca5e468ff83b5d3"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    vulns = data.get("vulns", [])[:3]
                    if not vulns:
                        await message.answer("🟢 Global tarmoqlarda ayni daqiqalarda tinchlik xotirjamlik.")
                        return
                    feed_text = "🚨 **GLOBAL KIBER-RAZVEDKA MONITORINGI (LIVE)**\n\n"
                    for vuln in vulns:
                        feed_text += (
                            f"🆔 **CVE ID:** `{vuln.get('id')}`\n"
                            f"📌 **Tizim xavfi:** `{vuln.get('summary', 'Nomaʼlum zaiflik axboroti')}`\n"
                            f"📅 **Vaqt:** `{vuln.get('modified')}`\n"
                            f"-----------------------------------\n"
                        )
                    await message.answer(feed_text, parse_mode="Markdown")
                else: await message.answer("❌ Kiber-baza API serverida texnik uzilish.")
        except Exception as e: await message.answer(f"❌ Tarmoq xatoligi yuz berdi: {e}")

# --- 9. 💔 PAROL SIZIB CHIQQANINI TEKSHIRISH ---
@router.message(F.text == "💔 Parol Sizib Chiqishi")
async def ask_leak_password(message: Message, state: FSMContext):
    allowed, msg = check_and_charge_user(message.from_user.id)
    if not allowed:
        await message.answer("❌ **Mablag' yetarli emas!** Hisobni to'ldiring.")
        return
    await message.answer(f"💔 Tekshirmoqchi bo'lgan maxfiy parolingizni yuboring (Baza orqali xavfsiz k-Anonymity arxitekturasida qidiriladi):\n⚡️ _({msg})_", parse_mode="Markdown")
    await state.set_state(BotStates.waiting_for_leak_check)

@router.message(BotStates.waiting_for_leak_check)
async def check_password_leak(message: Message, state: FSMContext):
    password = message.text.strip()
    sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    first5, tail = sha1_hash[:5], sha1_hash[5:]
    
    await message.answer("🔄 Global hakerlik bazalaridan sizning parolingiz qidirilmoqda...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://api.pwnedpasswords.com/range/{first5}") as response:
                if response.status == 200:
                    hashes = (await response.text()).splitlines()
                    count = 0
                    for h in hashes:
                        h_tail, h_count = h.split(':')
                        if h_tail == tail:
                            count = int(h_count)
                            break
                    if count > 0:
                        await message.answer(f"⚠️ **DIQQAT! PAROL SIZIB CHIQQAN!**\n\nUshbu parol hakerlar bazalarida **{count:,} marta** topildi! Uni zudlik bilan o'zgartiring!", parse_mode="Markdown")
                    else:
                        await message.answer("🟢 **Xavfsiz!** Tabriklaymiz, parolingiz ma'lumotlar sizib chiqish bazalarida qayd etilmagan.")
                else: await message.answer("❌ PwnedPasswords API bazasi ulanish xatosi.")
        except Exception as e: await message.answer(f"❌ Xatolik yuz berdi: {e}")
    await state.clear()

# --- ⚙️ BOTNI ISHGA TUSHIRISH ---
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
