from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🎁 Gift Cards", "🎬 Streaming Services"],
        ["💳 Balance Top Up", "🏷️ Apply Coupon"],
        ["👥 Referrals"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)
