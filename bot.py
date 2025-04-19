import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)

from handlers.main_menu import main_menu
from handlers.gift_cards import gift_cards_handler, gift_card_offer_handler
from handlers.streaming_services import streaming_handler, streaming_plan_handler
from handlers.top_up import top_up_handler, deposit_method_handler, available_balance_handler
from handlers.referrals import referrals_handler
from utils.pending import load_pending, save_pending
from utils.user_manager import load_user, save_user, add_deposit  # Updated import
from config import BOT_TOKEN

ADMIN_ID = 1188902990
pending_approvals = {}  # Track admin approval states {admin_id: {txid, user_id}}

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

def main() -> None:
    """Start the bot with proper handlers"""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ===== Core Handlers =====
    app.add_handler(CommandHandler("start", main_menu))
    app.add_handler(CommandHandler("menu", main_menu))

    # ===== Menu Handlers =====
    menu_items = {
        "🎁 Gift Cards": gift_cards_handler,
        "🎬 Streaming Services": streaming_handler,
        "💳 Balance Top Up": top_up_handler,
        "Available Balance": available_balance_handler,
        "👥 Referrals": referrals_handler
    }
    
    for text, handler in menu_items.items():
        app.add_handler(MessageHandler(filters.TEXT & filters.Regex(f"^{text}$"), handler))

    # ===== Back Buttons =====
    back_buttons = {
        "🔙 Back to Main Menu": main_menu,
        "🔙 Back to Gift Cards": gift_cards_handler,
    }
    
    for text, handler in back_buttons.items():
        app.add_handler(MessageHandler(filters.TEXT & filters.Regex(f"^{text}$"), handler))

    # ===== Dynamic Handlers =====
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^(Amazon|Apple|Steam|Visa)$"), gift_card_offer_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^(Netflix|Prime|Spotify|Disney\+)$"), streaming_plan_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^Deposit "), deposit_method_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^[a-zA-Z0-9\-_=+/]{20,}$"), available_balance_handler))

    # ===== Admin Workflows =====
    app.add_handler(CommandHandler("pending", list_pending))  # Changed to "pending"
    app.add_handler(CallbackQueryHandler(handle_admin_callback))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.User(ADMIN_ID) & ~filters.COMMAND,
        handle_admin_input
    ))

    app.run_polling()

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approve/reject callback queries"""
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data.split(':')
        action = data[0]
        
        if action == "approve" and len(data) == 3:
            txid, user_id = data[1], int(data[2])
            pending_approvals[query.from_user.id] = {
                "txid": txid,
                "user_id": user_id
            }
            await query.message.reply_text(f"💰 Enter amount for TXID {txid}:")
            
        elif action == "reject" and len(data) == 2:
            txid = data[1]
            pending = [p for p in load_pending() if p["txid"] != txid]
            save_pending(pending)
            
            # Find the user_id for the rejected transaction
            rejected_tx = next((p for p in load_pending() if p["txid"] == txid), None)
            if rejected_tx:
                await context.bot.send_message(
                    rejected_tx["user_id"],
                    "❌ Your deposit was rejected. Please contact support."
                )
            
            await query.message.reply_text(f"❌ Rejected TXID: {txid}")

    except Exception as e:
        logging.error(f"Callback error: {e}")
        await query.message.reply_text("❌ Error processing request")

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process admin amount input for approved deposits"""
    admin_id = update.effective_user.id
    if admin_id not in pending_approvals:
        return

    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        tx_data = pending_approvals.pop(admin_id)
        
        # Use the centralized add_deposit function
        add_deposit(
            user_id=tx_data["user_id"],
            amount=amount,
            txid=tx_data["txid"],
            service="top_up"
        )
        
        # Remove from pending
        pending = [p for p in load_pending() if p["txid"] != tx_data["txid"]]
        save_pending(pending)
        
        # Notify both parties
        await update.message.reply_text(
            f"✅ Approved ${amount:.2f} deposit for user {tx_data['user_id']}"
        )
        await context.bot.send_message(
            tx_data["user_id"],
            f"🎉 Your deposit of ${amount:.2f} has been approved and added to your balance!"
        )

    except ValueError:
        await update.message.reply_text("❌ Please enter a valid positive number")
    except Exception as e:
        logging.error(f"Deposit approval error: {e}")
        await update.message.reply_text("❌ Failed to process deposit approval")

async def list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all pending deposits with action buttons"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You don't have permission to view pending deposits")
        return

    pending = load_pending()
    if not pending:
        await update.message.reply_text("✅ No pending deposits at this time")
        return

    # Send summary first
    await update.message.reply_text(f"📋 Found {len(pending)} pending deposits:")
    
    # Send each pending deposit with buttons
    for deposit in pending:
        try:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{deposit['txid']}:{deposit['user_id']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{deposit['txid']}")
            ]])
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🧾 Deposit Request\n\n"
                     f"👤 User: @{deposit.get('username', 'unknown')}\n"
                     f"🆔 TXID: <code>{deposit['txid']}</code>\n"
                     f"🕒 Submitted: {deposit.get('timestamp', 'unknown')}",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Error displaying pending deposit: {e}")
            await update.message.reply_text(f"⚠️ Error displaying one of the pending deposits")

if __name__ == "__main__":
    main()