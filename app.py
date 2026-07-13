from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import requests

app = Flask(__name__)
CORS(app)

MONGO_URL = "mongodb+srv://Rahul2242669:Rahul8955@cluster0.ot3slvg.mongodb.net/?appName=Cluster0"
BOT_TOKEN = "8748256683:AAFhr_cxEFWR3a71e6AQQtb8S-bAGFPTvGE"
client = MongoClient(MONGO_URL)
db = client['rozkamao_db']
users_collection = db['users']

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "running"}), 200

@app.route('/api/telegram', methods=['POST'])
def telegram_webhook():
    update = request.json
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")
        if text == "/start":
            reply_markup = {
                "inline_keyboard": [[{"text": "🚀 Open RozKamao App", "web_app": {"url": "https://r2242669-creator.github.io/rozkamao-backend/"}}]]
            }
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                "chat_id": chat_id, "text": "Welcome! Niche se app kholein.", "reply_markup": reply_markup
            })
    return jsonify({"ok": True})

@app.route('/api/user', methods=['POST'])
def user_route():
    data = request.json
    uid = data.get('user_id')
    if data.get('action') == "watch_ad":
        users_collection.update_one({"user_id": uid}, {"$inc": {"balance": 5, "total_earned": 5}}, upsert=True)
    user = users_collection.find_one({"user_id": uid})
    return jsonify({"balance": user.get('balance', 0)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
        
