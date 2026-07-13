from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import requests
import time

app = Flask(__name__)
CORS(app)

# 🚨 APNA REAL MONGODB LINK DALEIN AUR <db_password> KO HATA KAR REAL PASSWORD LIKHEIN
MONGO_URL = "mongodb+srv://Rahul2242669:APNA_PASSWORD_YAHAN_LIKH@cluster0.ot3slvg.mongodb.net/?appName=Cluster0"
BOT_TOKEN = "7334751430:AAElb8W_aN42b-W0m85yS5g6j8s_Xexample"  # <-- REAL TG BOT TOKEN HERE
ADMIN_PASSWORD = "MERA_SECRET_PASSWORD_123"

# MongoDB Database Connector Setup
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

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "running", "database": "MongoDB Connected"})

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
            
        # 1. Action Watch Ad -> Increments Balance + Ads Count 
        if action == "watch_ad" or request.args.get('add_balance'):
            add_val = amount if amount else 5
            users_collection.update_one(
                {"user_id": uid},
                {"$inc": {"balance": add_val, "total_earned": add_val, "ads_watched": 1}}
            )
            
        # 2. Action Join Channel Task -> Rewards 10 Rs
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
            time.sleep(0.05) # Safe gap to avoid Telegram Ban
        except:
            pass
            
    return jsonify({"status": "success", "sent_to": success})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
