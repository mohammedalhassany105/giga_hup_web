import os
import threading
import asyncio
import requests
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- إعدادات الموقع (Flask) ---
app = Flask(__name__)
app.secret_key = "GIGA_HUB_2026_SECURE"

# الرابط الخاص بك لـ Supabase
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.otsyexflfhwzklnojiev:Qrv5.N%2B_*gAmek6@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- الجداول (نفس التي في app.py الخاص بك) ---
class AppEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    tagline = db.Column(db.String(200))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    download_link = db.Column(db.String(500))
    badge = db.Column(db.String(30))
    version = db.Column(db.String(20))
    file_size = db.Column(db.String(20))

class TelegramUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), unique=True, nullable=False)

# --- دالة إرسال الإشعارات الجماعية (كما هي) ---
def broadcast_new_app(new_app):
    BOT_TOKEN = "8661416877:AAHekEPVunPAqrRo00vtiXSu0wMIKgjj9u4"
    BASE_URL = "https://giga-hub.onrender.com" 
    users = TelegramUser.query.all()
    
    message = (
        f"🚀 *تم إضافة تطبيق جديد!*\n\n"
        f"📦 *الاسم:* {new_app.name}\n"
        f"✨ *الوصف:* {new_app.tagline}\n\n"
        f"🔗 [اضغط هنا للتحميل]({BASE_URL}/app/{new_app.id})"
    )
    
    for user in users:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {"chat_id": user.chat_id, "caption": message, "parse_mode": "Markdown", "photo": new_app.image_url}
        try: requests.post(url, data=payload)
        except: pass

# --- المسارات (Routes) ---
@app.route('/')
def index():
    apps = AppEntry.query.order_by(AppEntry.id.desc()).all()
    return render_template('index.html', apps=apps)

@app.route('/app/<int:id>')
def app_details(id):
    target_app = AppEntry.query.get_or_404(id)
    return render_template('details.html', app=target_app)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin_auth'):
        if request.method == 'POST' and request.form.get('key') == 'KING@2026':
            session['admin_auth'] = True
        else: return render_template('login.html')
    
    apps = AppEntry.query.all()
    return render_template('admin.html', apps=apps)

@app.route('/add', methods=['POST'])
def add():
    if not session.get('admin_auth'): return redirect(url_for('admin'))
    new_app = AppEntry(
        name=request.form['name'], category=request.form['category'],
        tagline=request.form['tagline'], description=request.form['description'],
        image_url=request.form['image_url'], download_link=request.form['download_link'],
        badge=request.form['badge'], version=request.form['version'], 
        file_size=request.form['file_size']
    )
    db.session.add(new_app)
    db.session.commit()
    broadcast_new_app(new_app) 
    return redirect(url_for('admin'))

# --- [قسم البوت المدمج] (كود bot.py الخاص بك بدون أي تغيير) ---
TOKEN = "8661416877:AAHekEPVunPAqrRo00vtiXSu0wMIKgjj9u4"
ADMIN_ID = "7605888782"
DB_URI = "postgresql://postgres.otsyexflfhwzklnojiev:Qrv5.N%2B_*gAmek6@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"
BASE_URL = "https://giga-hub.onrender.com/"

def get_db_connection():
    return psycopg2.connect(DB_URI)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
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

    for app_info in results:
        app_url = f"{BASE_URL}/app/{app_info[0]}"
        share_text = f"🚀 وجدت لك تطبيق {app_info[1]} في GIGA HUB!\n🔗 {app_url}"
        keyboard = [
            [InlineKeyboardButton("📥 صفحة التحميل", url=app_url)],
            [InlineKeyboardButton("📢 مشاركة مع صديق", switch_inline_query=share_text)]
        ]
        await update.message.reply_photo(photo=app_info[3], caption=f"✅ *{app_info[1]}*\n{app_info[2]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("req_"):
        app_name = query.data.split("_")[1]
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 طلب برنامج جديد: {app_name}\nمن: {update.effective_user.first_name}")
        await query.edit_message_text(f"✅ تم إرسال طلبك لإضافة '{app_name}'.")

# دالة لتشغيل البوت في مسار منفصل (Thread) لضمان عدم توقف الموقع
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.run_polling(close_loop=False)

# --- التشغيل النهائي ---
if __name__ == '__main__':
    # تشغيل البوت في الخلفية
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # تشغيل الموقع
    app.run(host='0.0.0.0', port=5000, debug=False)
