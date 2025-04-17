from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.json_manager import load_data
from utils.keyboards import add_back_button

async def gift_cards_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    keyboard = [[brand] for brand in data["gift_cards"].keys()]
    keyboard = add_back_button(keyboard, back_to="main")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose a Gift Card brand:", reply_markup=reply_markup)
