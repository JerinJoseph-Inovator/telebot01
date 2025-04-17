from telegram import Update
from telegram.ext import ContextTypes

async def referrals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Referral system coming soon!")
