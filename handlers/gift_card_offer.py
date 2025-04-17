from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.json_manager import load_data
from utils.keyboards import add_back_button

async def gift_card_offer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected = update.message.text
    data = load_data()
    offers = data["gift_cards"].get(selected, [])
    keyboard = [[offer] for offer in offers]
    keyboard = add_back_button(keyboard, back_to="gift_cards")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"{selected} Offers:", reply_markup=reply_markup)
