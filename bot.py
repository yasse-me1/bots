import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
import json
import os
from datetime import datetime

# =======================
#        LOGGING
# =======================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =======================
#     BOT TOKEN
# =======================
BOT_TOKEN = "8367866601:AAGW7lbzG70aNYujDtC53zKYawYwu0HdCmU"   # ⛔️ BU YERGA YANGI TOKEN QO‘YING

# =======================
#   CONVERSATION STATES
# =======================
(
    ENTERING_NAME,
    ENTERING_AGE,
    ENTERING_PRICE,
    ENTERING_PHONE,
    ENTERING_ADDRESS,
    ENTERING_DESCRIPTION
) = range(6)

# =======================
#   JSON DATABASE FILE
# =======================
DATA_FILE = "pets_database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    return {"pets": [], "favorites": {}, "users": {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# GLOBAL DATA
data = load_data()

# =======================
#      KEYBOARDS
# =======================
def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            ['🐕 Itlar', '🐈 Mushuklar'],
            ['🦜 Qushlar', '🐠 Baliqlar'],
            ['➕ E\'lon qo\'shish', '🔍 Qidirish'],
            ['❤️ Sevimlilar', '📊 Statistika'],
            ['📋 Mening e\'lonlarim', '❓ Yordam']
        ],
        resize_keyboard=True
    )

def cancel_keyboard():
    return ReplyKeyboardMarkup([['❌ Bekor qilish']], resize_keyboard=True)

# =======================
#       /start
# =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)

    if uid not in data['users']:
        data['users'][uid] = {
            "name": user.first_name,
            "username": user.username,
            "joined_date": datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        save_data(data)

    await update.message.reply_text(
        f"🐾 Assalomu alaykum, *{user.first_name}*!\n\n"
        f"*Pet Tashkent* botiga xush kelibsiz!\n"
        f"👇 Quyidagi tugmalardan foydalaning:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

# =======================
#    PET FORMATTER
# =======================
def format_pet(pet):
    return (
        f"🐾 *{pet['nomi']}*\n\n"
        f"📋 Turi: {pet['tur']}\n"
        f"🎂 Yoshi: {pet['yoshi']} yosh\n"
        f"💰 Narxi: *{pet['narxi']:,} so'm*\n"
        f"📍 Manzil: {pet['manzil']}\n"
        f"👤 Egasi: {pet['owner_name']}\n\n"
        f"📝 {pet['tavsif']}\n\n"
        f"🆔 ID: `#{pet['id']}`"
    )

# =======================
#  INLINE BUTTONS
# =======================
def get_pet_keyboard(pid, delete=False):
    keyboard = [
        [
            InlineKeyboardButton("📞 Bog'lanish", callback_data=f"contact_{pid}"),
            InlineKeyboardButton("❤️ Saqlash", callback_data=f"fav_{pid}")
        ],
        [InlineKeyboardButton("📤 Ulashish", callback_data=f"share_{pid}")]
    ]

    if delete:
        keyboard.append([InlineKeyboardButton("🗑 O'chirish", callback_data=f"delete_{pid}")])

    return InlineKeyboardMarkup(keyboard)

# =======================
#   CATEGORY SHOWING
# =======================
async def show_category(update, context, category):
    items = [p for p in data['pets'] if p['tur'] == category]


    if not items:
        await update.message.reply_text(
            f"❌ *{category}lar* bo‘yicha e'lonlar hali yo‘q.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        return
    await update.message.reply_text(
        f"🔍 *{category}lar ro‘yxati*",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

    for p in items:
        owner = (p['owner_id'] == update.effective_user.id)
        await update.message.reply_text(
            format_pet(p),
            parse_mode="Markdown",
            reply_markup=get_pet_keyboard(p['id'], delete=owner)
        )

async def show_dogs(update, context):   await show_category(update, context, "It")
async def show_cats(update, context):   await show_category(update, context, "Mushuk")
async def show_birds(update, context):  await show_category(update, context, "Qush")
async def show_fish(update, context):   await show_category(update, context, "Baliq")

# =======================
#   ADD PET START
# =======================
async def start_add_pet(update, context):
    keyboard = [
        [
            InlineKeyboardButton("🐕 It", callback_data="addpet_It"),
            InlineKeyboardButton("🐈 Mushuk", callback_data="addpet_Mushuk"),
        ],
        [
            InlineKeyboardButton("🦜 Qush", callback_data="addpet_Qush"),
            InlineKeyboardButton("🐠 Baliq", callback_data="addpet_Baliq"),
        ],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="addpet_cancel")]
    ]
    
    await update.message.reply_text(
        "➕ *Yangi e'lon qo‘shish*\n\n1️⃣ Hayvon turini tanlang:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ENTERING_NAME

# ==========================
#   SEARCH
# ==========================
async def search_pets(update, context):
    context.user_data['searching'] = True
    await update.message.reply_text(
        "🔍 Qidiruv uchun matn kiriting:",
        reply_markup=cancel_keyboard()
    )

async def handle_search(update, context):
    if not context.user_data.get("searching"):
        return

    text = update.message.text.lower()

    if text == "❌ bekor qilish":
        context.user_data['searching'] = False
        await update.message.reply_text("❌ Qidiruv bekor qilindi.", reply_markup=main_menu_keyboard())
        return

    results = []
    for p in data['pets']:
        if text in p['nomi'].lower() or text in p['tavsif'].lower() or text in p['manzil'].lower():
            results.append(p)

    context.user_data['searching'] = False

    if not results:
        await update.message.reply_text(
            "❌ Hech narsa topilmadi.",
            reply_markup=main_menu_keyboard()
        )
        return

    await update.message.reply_text(
        f"🔍 Topildi: {len(results)} ta",
        reply_markup=main_menu_keyboard()
    )

    for p in results:
        is_owner = (p["owner_id"] == update.effective_user.id)
        await update.message.reply_text(
            format_pet(p),
            parse_mode="Markdown",
            reply_markup=get_pet_keyboard(p["id"], delete=is_owner)
        )

# =======================
#   CALLBACK HANDLER
# =======================
async def button_callback(update, context):
    query = update.callback_query
    data_c = query.data
    uid = str(query.from_user.id)
    await query.answer()

    # --- TUR TANLASH ---
    if data_c.startswith("addpet_"):
        pet_type = data_c.split("_")[1]

        if pet_type == "cancel":
            await query.edit_message_text("❌ E'lon qo‘shish bekor qilindi.")
            return ConversationHandler.END

        context.user_data["new_pet"] = {"tur": pet_type}

        await query.edit_message_text(f"🐾 Tanlandi: *{pet_type}*", parse_mode='Markdown')
        await query.message.reply_text("2️⃣ Hayvon nomini kiriting:", reply_markup=cancel_keyboard())
        return ENTERING_NAME


    # --- BOG‘LANISH ---
    if data_c.startswith("contact_"):
        pid = int(data_c.split("_")[1])
        pet = next((p for p in data['pets'] if p['id'] == pid), None)

        if pet:
            await query.message.reply_text(
                f"📞 Bog‘lanish:\n👤 {pet['owner_name']}\n📱 {pet['telefon']}",
                parse_mode="Markdown"
            )

    # --- SEVIMLIGA QO‘SHISH ---
    if data_c.startswith("fav_"):
        pid = int(data_c.split("_")[1])
        
        if uid not in data["favorites"]:
            data["favorites"][uid] = []

        if pid not in data["favorites"][uid]:
            data["favorites"][uid].append(pid)
            save_data(data)
            await query.answer("❤️ Sevimlilarga qo‘shildi", show_alert=True)
        else:
            await query.answer("⚠️ Allaqachon qo‘shilgan", show_alert=True)

    # --- DELETE REQUEST ---
    if data_c.startswith("delete_"):
        pid = int(data_c.split("_")[1])
        pet = next((p for p in data["pets"] if p["id"] == pid), None)

        if pet and pet["owner_id"] == query.from_user.id:
            keyboard = [
                [
                    InlineKeyboardButton("Ha", callback_data=f"confirm_delete_{pid}"),
                    InlineKeyboardButton("Yo‘q", callback_data="cancel_delete")
                ]
            ]
            await query.message.reply_text("O‘chirishni tasdiqlaysizmi?", reply_markup=InlineKeyboardMarkup(keyboard))

    if data_c.startswith("confirm_delete_"):
        pid = int(data_c.split("_")[2])
        data["pets"] = [p for p in data["pets"] if p["id"] != pid]

        for favs in data["favorites"].values():
            if pid in favs:
                favs.remove(pid)

        save_data(data)

        await query.edit_message_text("✅ O‘chirildi.")

    if data_c == "cancel_delete":
        await query.edit_message_text("❌ Bekor qilindi.")

# =======================
#   ADD PET STEPS
# =======================
async def enter_name(update, context):
    if update.message.text == "❌ Bekor qilish":
        await update.message.reply_text("Bekor qilindi.", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    context.user_data['new_pet']['nomi'] = update.message.text
    await update.message.reply_text("3️⃣ Yoshini kiriting:")
    return ENTERING_AGE

async def enter_age(update, context):
    try:
        age = int(update.message.text)
        if age < 0 or age > 50:
            raise ValueError

        context.user_data['new_pet']['yoshi'] = age
        await update.message.reply_text("4️⃣ Narxini kiriting:")
        return ENTERING_PRICE

    except:
        await update.message.reply_text("❌ Raqam kiriting!")
        return ENTERING_AGE

async def enter_price(update, context):
    try:
        price = int(update.message.text)
        context.user_data['new_pet']['narxi'] = price
        await update.message.reply_text("5️⃣ Telefon raqamingizni kiriting:")
        return ENTERING_PHONE

    except:
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return ENTERING_PRICE

async def enter_phone(update, context):
    context.user_data['new_pet']['telefon'] = update.message.text
    await update.message.reply_text("6️⃣ Manzil kiriting:")
    return ENTERING_ADDRESS

async def enter_address(update, context):
    context.user_data['new_pet']['manzil'] = update.message.text
    await update.message.reply_text("7️⃣ Tavsif kiriting:")
    return ENTERING_DESCRIPTION

async def enter_description(update, context):
    user = update.effective_user
    pet = context.user_data['new_pet']

    pet['tavsif'] = update.message.text
    pet['owner_id'] = user.id
    pet['owner_name'] = user.first_name
    pet['id'] = max([p["id"] for p in data["pets"]], default=0) + 1
    pet['sana'] = datetime.now().strftime('%Y-%m-%d %H:%M')

    data["pets"].append(pet)
    save_data(data)

    await update.message.reply_text(
        "✅ E'lon qo‘shildi!\n\n" + format_pet(pet),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

    return ConversationHandler.END


# =======================
#   FAVORITES
# =======================
async def show_favorites(update, context):
    uid = str(update.effective_user.id)

    if uid not in data["favorites"] or not data["favorites"][uid]:
        await update.message.reply_text("❤️ Sevimlilar bo‘sh.")
        return

    pets = [p for p in data["pets"] if p["id"] in data["favorites"][uid]]

    for p in pets:
        keyboard = [[
            InlineKeyboardButton("📞 Bog'lanish", callback_data=f"contact_{p['id']}"),
            InlineKeyboardButton("💔 O‘chirish", callback_data=f"unfav_{p['id']}")
        ]]
        await update.message.reply_text(
            format_pet(p), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# =======================
#   MY PETS
# =======================
async def show_my_pets(update, context):
    uid = update.effective_user.id
    pets = [p for p in data['pets'] if p['owner_id'] == uid]

    if not pets:
        await update.message.reply_text("📋 Sizda e'lonlar yo‘q.")
        return

    for p in pets:
        await update.message.reply_text(
            format_pet(p),
            parse_mode="Markdown",
            reply_markup=get_pet_keyboard(p["id"], delete=True)
        )


# =======================
#   HELP
# =======================
async def show_help(update, context):
    await update.message.reply_text(
        "❓ *Yordam bo‘limi*\n\n"
        "• Kategoriyalardan birini tanlang\n"
        "• E’lonlarni ko‘ring\n"
        "• ‘Bog‘lanish’ tugmasi orqali sotuvchiga murojaat qiling\n"
        "• ‘➕ E’lon qo‘shish’ orqali o‘z e’loningizni joylang",
        parse_mode="Markdown"
    )


# =======================
#      RUN BOT
# =======================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("➕ E'lon qo'shish"), start_add_pet)],
        states={
            ENTERING_NAME: [MessageHandler(filters.TEXT, enter_name)],
            ENTERING_AGE: [MessageHandler(filters.TEXT, enter_age)],
            ENTERING_PRICE: [MessageHandler(filters.TEXT, enter_price)],
            ENTERING_PHONE: [MessageHandler(filters.TEXT, enter_phone)],
            ENTERING_ADDRESS: [MessageHandler(filters.TEXT, enter_address)],
            ENTERING_DESCRIPTION: [MessageHandler(filters.TEXT, enter_description)],
        },
        fallbacks=[MessageHandler(filters.Regex("❌ Bekor qilish"), enter_name)]
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button_callback))

    # Commands
    app.add_handler(CommandHandler("start", start))

    # Menu handlers
    app.add_handler(MessageHandler(filters.Regex("🐕 Itlar"), show_dogs))
    app.add_handler(MessageHandler(filters.Regex("🐈 Mushuklar"), show_cats))
    app.add_handler(MessageHandler(filters.Regex("🦜 Qushlar"), show_birds))
    app.add_handler(MessageHandler(filters.Regex("🐠 Baliqlar"), show_fish))
    app.add_handler(MessageHandler(filters.Regex("❤️ Sevimlilar"), show_favorites))
    app.add_handler(MessageHandler(filters.Regex("🔍 Qidirish"), search_pets))
    app.add_handler(MessageHandler(filters.Regex("📋 Mening e'lonlarim"), show_my_pets))
    app.add_handler(MessageHandler(filters.Regex("❓ Yordam"), show_help))
    app.add_handler(MessageHandler(filters.Regex("📊 Statistika"), show_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
