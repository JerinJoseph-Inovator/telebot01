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
from utils.user_manager import load_user, save_user
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
    app.add_handler(CallbackQueryHandler(handle_admin_callback))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), handle_admin_input))
    # app.add_handler(CommandHandler("pending", list_pending))
    # Change this in your main bot file
    app.add_handler(CommandHandler("pendingdeposits", list_pending))

    app.run_polling()

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approve/reject actions with amount input"""
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data.split(":")
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
            await query.message.reply_text(f"❌ Rejected TXID: {txid}")
            await context.bot.send_message(
                pending[0]["user_id"],
                "❌ Your deposit was rejected. Contact support."
            )
            
    except Exception as e:
        logging.error(f"Callback error: {e}")
        await query.message.reply_text("❌ Error processing request")

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process admin amount input"""
    admin_id = update.effective_user.id
    if admin_id not in pending_approvals:
        return

    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError
            
        approval_data = pending_approvals.pop(admin_id)
        txid = approval_data["txid"]
        user_id = approval_data["user_id"]
        
        # Update user balance
        user = load_user(user_id)
        user["balance"] = user.get("balance", 0.0) + amount
        user.setdefault("transactions", []).append({
            "txid": txid,
            "amount": amount,
            "status": "approved"
        })
        save_user(user_id, user)
        
        # Remove from pending
        pending = [p for p in load_pending() if p["txid"] != txid]
        save_pending(pending)
        
        # Notify parties
        await update.message.reply_text(f"✅ Approved ${amount:.2f} for TXID {txid}")
        await context.bot.send_message(
            user_id,
            f"🎉 Your deposit of ${amount:.2f} has been approved!"
        )
        
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Enter positive number.")
        logging.warning(f"Admin {admin_id} entered invalid amount: {update.message.text}")

async def list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List pending deposits with action buttons (admin only)"""
    if update.effective_user.id != ADMIN_ID:
        return

    pending = load_pending()
    if not pending:
        await update.message.reply_text("✅ No pending deposits")
        return

    for deposit in pending:
        try:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve:{deposit['txid']}:{deposit['user_id']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject:{deposit['txid']}")
                ]
            ])
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📝 Pending Deposit\n\n"
                     f"User: @{deposit.get('username', 'Unknown')}\n"
                     f"TXID: <code>{deposit['txid']}</code>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except KeyError as e:
            logging.error(f"Malformed pending deposit: {e}")
        except Exception as e:
            logging.error(f"Error showing pending deposit: {e}")

    await update.message.reply_text(f"ℹ️ Sent {len(pending)} pending deposits to your PM")

if __name__ == "__main__":
    main()