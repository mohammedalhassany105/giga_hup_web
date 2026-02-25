from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import psycopg2  # هذه هي المكتبة التي تربطك بـ Supabase
import os

app = Flask(__name__)
app.secret_key = "GIGA_HUB_2026_SECURE"

# --- الربط بقاعدة البيانات السحابية (Supabase) ---
# تأكد من إضافة 'ql' بعد 'postgres' في الرابط
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.otsyexflfhwzklnojiev:Qrv5.N%2B_*gAmek6@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- الجداول ---
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

# --- دالة إرسال الإشعارات الجماعية ---
def broadcast_new_app(new_app):
    BOT_TOKEN = "8661416877:AAHekEPVunPAqrRo00vtiXSu0wMIKgjj9u4"
    BASE_URL = "رابط_موقعك_بعد_الرفع" # مثلاً https://gigahub.render.com
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
    broadcast_new_app(new_app) # إرسال إشعار فوري
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) # جرب debug=False مؤقتاً