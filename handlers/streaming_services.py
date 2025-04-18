from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.json_manager import load_data
from utils.keyboards import add_back_button

async def streaming_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available streaming services (first menu level)."""
    data = load_data()
    keyboard = [[service] for service in data["streaming_services"].keys()]
    keyboard = add_back_button(keyboard, back_to="main")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose a Streaming Service:", reply_markup=reply_markup)

async def streaming_plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscription plans for the selected service (second menu level)."""
    selected = update.message.text
    data = load_data()
    plans = data["streaming_services"].get(selected, [])
    
    if not plans:  # Handle invalid selections gracefully
        await update.message.reply_text("No plans found. Please try again.")
        return
    
    keyboard = [[plan] for plan in plans]
    keyboard = add_back_button(keyboard, back_to="streaming_services")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"{selected} Plans:", reply_markup=reply_markup)