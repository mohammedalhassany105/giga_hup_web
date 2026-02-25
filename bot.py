import psycopg2
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- الإعدادات ---
TOKEN = "8661416877:AAHekEPVunPAqrRo00vtiXSu0wMIKgjj9u4"
ADMIN_ID = "7605888782"
# ملاحظة: psycopg2 يستخدم الرابط المباشر من Supabase كما هو
DB_URI = "postgresql://postgres.otsyexflfhwzklnojiev:Qrv5.N%2B_*gAmek6@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"
BASE_URL = "http://127.0.0.1:5000"

def get_db_connection():
    return psycopg2.connect(DB_URI)

# --- المهام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    # حفظ المستخدم في القاعدة السحابية
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO telegram_user (chat_id) VALUES (%s) ON CONFLICT DO NOTHING", (chat_id,))
    conn.commit(); cur.close(); conn.close()
    
    await update.message.reply_text("👋 مرحباً بك في GIGA HUB!\nأرسل اسم البرنامج للبحث عنه، أو استقبل الإشعارات هنا.")

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT id, name, tagline, image_url FROM app_entry WHERE name ILIKE %s", (f'%{query}%',))
    results = cur.fetchall()
    cur.close(); conn.close()

    if not results:
        keyboard = [[InlineKeyboardButton(f"🙋‍♂️ طلب إضافة {query}", callback_data=f"req_{query}")]]
        await update.message.reply_text("❌ لم يتم العثور عليه. هل تود طلبه؟", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    for app in results:
        app_url = f"{BASE_URL}/app/{app[0]}"
        share_text = f"🚀 وجدت لك تطبيق {app[1]} في GIGA HUB!\n🔗 {app_url}"
        keyboard = [
            [InlineKeyboardButton("📥 صفحة التحميل", url=app_url)],
            [InlineKeyboardButton("📢 مشاركة مع صديق", switch_inline_query=share_text)]
        ]
        await update.message.reply_photo(photo=app[3], caption=f"✅ *{app[1]}*\n{app[2]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("req_"):
        app_name = query.data.split("_")[1]
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 طلب برنامج جديد: {app_name}\nمن: {update.effective_user.first_name}")
        await query.edit_message_text(f"✅ تم إرسال طلبك لإضافة '{app_name}'.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__": main()