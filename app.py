from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import requests
import time

app = Flask(__name__)
CORS(app)

# 🔥 TERA REAL MONGODB LINK AUR REAL TELEGRAM BOT TOKEN
MONGO_URL = "mongodb+srv://Rahul2242669:Rahul8955@cluster0.ot3slvg.mongodb.net/?appName=Cluster0"
BOT_TOKEN = "8748256683:AAFhr_cxEFWR3a71e6AQQtb8S-bAGFPTvGE"  
ADMIN_PASSWORD = "MERA_SECRET_PASSWORD_123"

# MongoDB Database Connection Setup
client = MongoClient(MONGO_URL)
db = client['rozkamao_db']
users_collection = db['users']

def get_user_db(uid):
    user = users_collection.find_one({"user_id": uid})
    if not user:
        user = {
            "user_id": uid, 
            "balance": 0, 
            "total_earned": 0, 
            "ads_watched": 0
        }
        users_collection.insert_one(user)
    return user

@app.route('/', methods=['GET', 'POST'])
def home():
    return jsonify({"status": "running", "database": "MongoDB Connected Successfully"}), 200

# --- 🤖 TELEGRAM BOT CONTROLLER (FOR /START COMMAND) ---
@app.route('/api/telegram', methods=['GET', 'POST'])
def telegram_webhook():
    # Agar Telegram se koi request aaye
    if request.method == 'POST':
        try:
            update = request.json or {}
            
            # Agar data sahi format mein na ho toh error block karein
            if not isinstance(update, dict):
                return jsonify({"status": "invalid format"}), 200
                
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")
                
                if text.startswith("/start"):
                    # Tere Frontend ka Main GitHub Pages link
                    mini_app_url = "https://r2242669-creator.github.io/rozkamao-backend/" 
                    
                    reply_markup = {
                        "inline_keyboard": [[
                            {"text": "🚀 Open RozKamao App", "web_app": {"url": mini_app_url}}
                        ]]
                    }
                    
                    payload = {
                        "chat_id": chat_id,
                        "text": "👋 Welcome to RozKamao Elite!\n\nNiche diye gaye button par click karke App kholein, Ads dekhein aur earning shuru karein!",
                        "reply_markup": reply_markup
                    }
                    
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload, timeout=5)
        except Exception as e:
            print(f"Webhook Error: {e}")
            
        return jsonify({"status": "ok"}), 200

    # Normal GET request par status check dikhaye
    return jsonify({"status": "webhook route is active"}), 200

# --- USER BALANCES & DATA MANAGEMENT ---
@app.route('/api/user', methods=['GET', 'POST'])
def user_route():
    if request.method == 'GET':
        uid = request.args.get('user_id')
        if not uid:
            return jsonify({"error": "Missing user_id"}), 400
        user = get_user_db(uid)
        user.pop('_id', None)
        return jsonify(user)
        
    elif request.method == 'POST':
        data = request.json or {}
        uid = data.get('user_id') or request.args.get('user_id')
        action = data.get('action') or request.args.get('action')
        amount = int(data.get('amount') or request.args.get('add_balance') or 0)
        
        if not uid:
            return jsonify({"error": "Missing user_id"}), 400
            
        if action == "watch_ad" or request.args.get('add_balance'):
            add_val = amount if amount else 5
            users_collection.update_one(
                {"user_id": uid},
                {"$inc": {"balance": add_val, "total_earned": add_val, "ads_watched": 1}}
            )
            
        elif action == "join_channel":
            users_collection.update_one(
                {"user_id": uid},
                {"$inc": {"balance": 10, "total_earned": 10}}
            )
            
        updated_user = get_user_db(uid)
        updated_user.pop('_id', None)
        return jsonify(updated_user)

# --- 📢 ADMIN TELEGRAM BROADCAST SYSTEM ---
@app.route('/api/admin/broadcast', methods=['POST'])
def broadcast():
    data = request.json
    if not data or data.get("secret_key") != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized Access"}), 403
        
    msg = data.get("message")
    if not msg:
        return jsonify({"error": "Blank Message"}), 400
        
    success = 0
    all_users = users_collection.find({})
    
    for u in all_users:
        uid = u.get("user_id")
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            res = requests.post(url, json={"chat_id": uid, "text": msg}, timeout=4)
            if res.status_code == 200:
                success += 1
            time.sleep(0.05) 
        except:
            pass
            
    return jsonify({"status": "success", "sent_to": success})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
