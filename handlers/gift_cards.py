from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.json_manager import load_data
from utils.keyboards import add_back_button

async def gift_cards_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available gift card brands (first menu level)."""
    data = load_data()
    keyboard = [[brand] for brand in data["gift_cards"].keys()]
    keyboard = add_back_button(keyboard, back_to="main")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose a Gift Card brand:", reply_markup=reply_markup)

async def gift_card_offer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show payment options for the selected gift card brand (second menu level)."""
    selected = update.message.text
    data = load_data()
    offers = data["gift_cards"].get(selected, [])
    
    if not offers:  # Handle invalid selections gracefully
        await update.message.reply_text("No offers found. Please try again.")
        return
    
    keyboard = [[offer] for offer in offers]
    keyboard = add_back_button(keyboard, back_to="gift_cards")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"{selected} Offers:", reply_markup=reply_markup)