from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.json_manager import load_data
from utils.keyboards import add_back_button

async def streaming_plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected = update.message.text
    data = load_data()
    plans = data["streaming_services"].get(selected, [])
    keyboard = [[plan] for plan in plans]
    keyboard = add_back_button(keyboard, back_to="main")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"{selected} Plans:", reply_markup=reply_markup)
