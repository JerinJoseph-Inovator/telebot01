import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update

from handlers.main_menu import main_menu
from handlers.gift_cards import gift_cards_handler
from handlers.gift_card_offer import gift_card_offer_handler
from handlers.streaming import streaming_handler
from handlers.top_up import top_up_handler, deposit_method_handler, available_balance_handler
from handlers.referrals import referrals_handler
from handlers.streaming_plan_handler import streaming_plan_handler
from utils.pending import load_pending, save_pending

from config import BOT_TOKEN
ADMIN_ID = 1188902990

logging.basicConfig(level=logging.INFO)

app = ApplicationBuilder().token(BOT_TOKEN).build()

# Menu commands
app.add_handler(CommandHandler("start", main_menu))
app.add_handler(CommandHandler("menu", main_menu))

# Add handler for the streaming plans
app.add_handler(MessageHandler(
    filters.TEXT & filters.Regex("^(Netflix|Prime)$"),
    streaming_plan_handler
))

# Back button handler
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🔙 Back to Main Menu"), main_menu))

# Main menu button handlers
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🎁 Gift Cards"), gift_cards_handler))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🎬 Streaming Services"), streaming_handler))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("💳 Balance Top Up"), top_up_handler))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Available Balance"), available_balance_handler))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Deposit "), deposit_method_handler))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("👥 Referrals"), referrals_handler))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🔙 Back to Main Menu"), main_menu))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🔙 Back to Gift Cards"), gift_cards_handler))

# Dynamic gift card brand handler (Amazon, Apple, etc.)
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Amazon|Apple|Steam|Visa)$"), gift_card_offer_handler))

# Admin approval handler for deposit approval/rejection
async def admin_approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, txid = query.data.split(":", 1)
    pending = load_pending()
    tx = next((p for p in pending if p["txid"] == txid), None)

    if not tx:
        await query.edit_message_text("❌ TXID not found or already handled.")
        return

    pending.remove(tx)
    save_pending(pending)

    if action == "approve":
        await query.edit_message_text(f"✅ Approved TXID: {txid}")
        await context.bot.send_message(tx["user_id"], "✅ Your deposit has been approved.")
    else:
        await query.edit_message_text(f"❌ Rejected TXID: {txid}")
        await context.bot.send_message(tx["user_id"], "❌ Your deposit was rejected. Please contact support.")

# List all pending deposits with /pendingdeposits command
async def list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:  # Replace with your admin ID
        return
    pending = load_pending()
    if not pending:
        await update.message.reply_text("✅ No pending deposits.")
        return
    text = "\n\n".join([f"@{p['username']} | {p['txid']}" for p in pending])
    await update.message.reply_text(f"📝 Pending Deposits:\n\n{text}")

# Register the handler for callback queries (approve/reject actions)
app.add_handler(CallbackQueryHandler(admin_approval_handler))

# Register the /pendingdeposits command
app.add_handler(CommandHandler("pendingdeposits", list_pending))

if __name__ == "__main__":
    app.run_polling()
