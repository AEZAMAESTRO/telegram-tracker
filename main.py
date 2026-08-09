import os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8831936655:AAER2-XEGPVAbBETQToaIzbSVoaJWV7w8Ts"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("📍 Check Photo Location", callback_data="loc_check"),
        InlineKeyboardButton("🔍 Digital Footprint Audit", callback_data="footprint_audit")
    )
    bot.send_message(
        message.chat.id, 
        "Welcome to your CV Project Bot! Choose an option below:", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "loc_check":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Send me a photo now to check its location metadata!")
    elif call.data == "footprint_audit":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Send me an email address or a photo to start your digital footprint audit.")

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def index():
    return "Bot is alive!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))