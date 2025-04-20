# handlers/coupons/coupons.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

async def apply_coupon_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for upcoming coupon feature"""
    await update.message.reply_text(
        "🎟️ Coupon Feature Coming Soon!\n\n"
        "We're working hard to bring you coupon/discount functionality.\n"
        "Stay tuned for updates!",
        reply_markup=ReplyKeyboardMarkup(
            [[ "🔙 Back to Main Menu" ]],
            resize_keyboard=True
        )
    )