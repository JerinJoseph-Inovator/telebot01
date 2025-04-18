import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)

# bot.py
from handlers.pending import register_pending_handlers
from handlers.main_menu import main_menu
from handlers.gift_cards import gift_cards_handler, gift_card_offer_handler
from handlers.streaming_services import streaming_handler, streaming_plan_handler
from handlers.top_up import top_up_handler, deposit_method_handler, available_balance_handler
from handlers.referrals import referrals_handler
from utils.pending import load_pending, save_pending
from config import BOT_TOKEN

ADMIN_ID = 1188902990  # Your admin ID

# Add at the top with other imports
import logging

# Configure logging properly
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main() -> None:
    """Start the bot."""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ===== Core Commands =====
    app.add_handler(CommandHandler("start", main_menu))
    app.add_handler(CommandHandler("menu", main_menu))

    # ===== Main Menu Handlers =====
    menu_buttons = {
        "🎁 Gift Cards": gift_cards_handler,
        "🎬 Streaming Services": streaming_handler,
        "💳 Balance Top Up": top_up_handler,
        "Available Balance": available_balance_handler,
        "👥 Referrals": referrals_handler
    }

    for button_text, handler in menu_buttons.items():
        app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(f"^{button_text}$"),
            handler
        ))

    # ===== Back Button Handlers =====
    back_buttons = {
        "🔙 Back to Main Menu": main_menu,
        "🔙 Back to Gift Cards": gift_cards_handler,
    }

    for button_text, handler in back_buttons.items():
        app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(f"^{button_text}$"),
            handler
        ))

    # ===== Dynamic Option Handlers =====
    # Gift Card Brands
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^(Amazon|Apple|Steam|Visa)$"),
        gift_card_offer_handler
    ))

    # Streaming Services
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^(Netflix|Prime|Spotify|Disney\+)$"),
        streaming_plan_handler
    ))

    # Deposit Methods
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^Deposit "),
        deposit_method_handler
    ))

    # TXID Submissions
    # Change this in Dynamic Option Handlers section
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^[a-zA-Z0-9\-_=+/]{20,}$"),  # Added = and +
        available_balance_handler
    ))

    # ===== Admin Functions =====
    app.add_handler(CallbackQueryHandler(admin_approval_handler))
    app.add_handler(CommandHandler("pendingdeposits", list_pending))

    # Start the bot
    app.run_polling()

async def admin_approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin approve/reject actions."""
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

async def list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List pending deposits (admin only)."""
    if update.effective_user.id != ADMIN_ID:
        return
        
    pending = load_pending()
    if not pending:
        await update.message.reply_text("✅ No pending deposits.")
        return
        
    text = "\n\n".join([f"@{p['username']} | {p['txid']}" for p in pending])
    await update.message.reply_text(f"📝 Pending Deposits:\n\n{text}")

if __name__ == "__main__":
    main()