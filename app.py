import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
CORS(app)

DB_FILE = "users_db.json"
BOT_TOKEN = "8748256683:AAFhr_cxEFWR3a71e6AQQtb8S-bAGFPTvGE"

# Render App URL
WEBHOOK_URL = "https://rozkamao-backend.onrender.com"

# Initialize Telegram Application properly
application = Application.builder().token(BOT_TOKEN).build()

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

# Telegram Webhook Route - Isey Telegram hit karega
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        try:
            update = Update.de_json(request.get_json(force=True), application.bot)
            import asyncio
            asyncio.run(application.process_update(update))
        except Exception as e:
            logging.error(f"Error processing update: {e}")
    return "OK", 200

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    args = context.args
    db = load_db()
    
    if user_id not in db:
        db[user_id] = {"balance": 0, "refers": 0}
        if args and args[0] != user_id and args[0] in db:
            referrer = args[0]
            db[referrer]['balance'] = int(db[referrer].get('balance', 0)) + 10
            db[referrer]['refers'] = int(db[referrer].get('refers', 0)) + 1
            try: await context.bot.send_message(chat_id=int(referrer), text="🎉 **New Referral!** Aapko ₹10 mile.")
            except: pass
        save_db(db)

    keyboard = [
        [InlineKeyboardButton("🚀 Open RozKamao App", web_app={"url": "https://reliable-biscuit-867102.netlify.app"})],
        [InlineKeyboardButton("👥 Refer Link Get", callback_data="get_link"),
         InlineKeyboardButton("💰 Wallet", callback_data="get_wallet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"👋 Welcome {user.first_name} to RozKamao App!\n\n👇 Niche se app kholo:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    db = load_db()
    
    if query.data == "get_wallet":
        bal = db.get(user_id, {}).get('balance', 0)
        ref = db.get(user_id, {}).get('refers', 0)
        await query.message.reply_text(f"💰 **WALLET**\n💵 Balance: ₹{bal}\n📊 Refers: {ref}")
    elif query.data == "get_link":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.message.reply_text(f"👥 **Aapki Referral Link:**\n{ref_link}\n\nPer refer ₹10 milenge!")

# Handlers register karein
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_click))

if __name__ == '__main__':
    import asyncio
    # Startup par webhook register karne ka jugad
    try:
        asyncio.run(application.initialize())
        asyncio.run(application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook"))
        logging.info("Webhook set successfully!")
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
