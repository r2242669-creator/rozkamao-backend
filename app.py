import os
import json
import logging
import requests
from threading import Thread
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
CORS(app)

DB_FILE = "users_db.json"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8748256683:AAFhr_cxEFWR3a71e6AQQtb8S-bAGFPTvGE")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "running", "bot": "RozKamao"}), 200

@app.route('/api/user', methods=['GET', 'POST'])
def sync_user():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    db = load_db()
    
    if user_id not in db:
        db[user_id] = {"balance": 0, "refers": 0}
        save_db(db)
        
    if request.method == 'POST':
        req_data = request.get_json()
        if req_data and 'add_balance' in req_data:
            db[user_id]['balance'] = int(db[user_id].get('balance', 0)) + int(req_data['add_balance'])
            save_db(db)
            
    return jsonify(db[user_id])

def handle_bot_logic():
    offset = 0
    # Pehle se koi webhook set ho toh clear karo taaki polling chale
    try:
        requests.get(f"{TELEGRAM_API}/deleteWebhook")
    except:
        pass

    while True:
        try:
            url = f"{TELEGRAM_API}/getUpdates?offset={offset}&timeout=20"
            response = requests.get(url).json()
            
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    
                    # 1. Handle Command Messages (/start)
                    if "message" in update and "text" in update["message"]:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg["text"]
                        user_id = str(msg["from"]["id"])
                        first_name = msg["from"].get("first_name", "User")
                        
                        if text.startswith("/start"):
                            db = load_db()
                            if user_id not in db:
                                db[user_id] = {"balance": 0, "refers": 0}
                                
                                # Referral check
                                parts = text.split()
                                if len(parts) > 1:
                                    referrer = parts[1]
                                    if referrer != user_id and referrer in db:
                                        db[referrer]['balance'] = int(db[referrer].get('balance', 0)) + 10
                                        db[referrer]['refers'] = int(db[referrer].get('refers', 0)) + 1
                                        try:
                                            ref_url = f"{TELEGRAM_API}/sendMessage"
                                            requests.post(ref_url, json={"chat_id": int(referrer), "text": "🎉 **New Referral!** Aapko ₹10 mile."})
                                        except:
                                            pass
                                save_db(db)
                            
                            # Welcome markup button template
                            welcome_text = f"👋 Welcome {first_name} to RozKamao App!\n\n👇 Niche se app kholo:"
                            reply_markup = {
                                "inline_keyboard": [
                                    [{"text": "🚀 Open RozKamao App", "web_app": {"url": "https://reliable-biscuit-867102.netlify.app"}}],
                                    [{"text": "👥 Refer Link Get", "add_to_menu": False, "callback_data": "get_link"},
                                     {"text": "💰 Wallet", "callback_data": "get_wallet"}]
                                ]
                            }
                            
                            send_url = f"{TELEGRAM_API}/sendMessage"
                            requests.post(send_url, json={"chat_id": chat_id, "text": welcome_text, "reply_markup": reply_markup})
                    
                    # 2. Handle Inline Button Clicks
                    elif "callback_query" in update:
                        query = update["callback_query"]
                        query_id = query["id"]
                        chat_id = query["message"]["chat"]["id"]
                        user_id = str(query["from"]["id"])
                        data = query["data"]
                        
                        # Acknowledge callback immediately to stop loading spinner
                        requests.post(f"{TELEGRAM_API}/answerCallbackQuery", json={"callback_query_id": query_id})
                        
                        db = load_db()
                        if data == "get_wallet":
                            bal = db.get(user_id, {}).get('balance', 0)
                            ref = db.get(user_id, {}).get('refers', 0)
                            wallet_text = f"💰 **WALLET**\n\n💵 Balance: ₹{bal}\n📊 Refers: {ref}"
                            requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": wallet_text})
                            
                        elif data == "get_link":
                            # Dynamically fetch bot name safely
                            try:
                                bot_info = requests.get(f"{TELEGRAM_API}/getMe").json()
                                bot_username = bot_info["result"]["username"]
                            except:
                                bot_username = "RozKamaoLoot_bot"
                                
                            ref_link = f"https://t.me/{bot_username}?start={user_id}"
                            link_text = f"👥 **Aapki Referral Link:**\n{ref_link}\n\nPer refer ₹10 milenge!"
                            requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": link_text})
                            
        except Exception as e:
            logging.error(f"Bot Loop Error: {e}")
        time.sleep(1)

if __name__ == '__main__':
    # Ekdum pure independent native python thread bina kisi library loop conflict ke
    bot_worker = Thread(target=handle_bot_logic, daemon=True)
    bot_worker.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    
