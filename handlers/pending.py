# handlers/pending.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

from utils.pending import load_pending, save_pending
from utils.user_manager import load_user, save_user
from utils.json_manager import load_data
from config import ADMIN_ID

# Temporary storage for admin approvals
pending_approvals = {}  # {admin_id: {txid: str, user_id: int}}

async def pending_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pending command for admins"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized access.")
        return

    pending = load_pending()
    if not pending:
        await update.message.reply_text("✅ No pending deposits.")
        return

    for deposit in pending:
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{deposit['txid']}:{deposit['user_id']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{deposit['txid']}")
            ]
        ]
        
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📝 Pending Deposit\n\n"
                     f"User: @{deposit.get('username', 'Unknown')}\n"
                     f"TXID: <code>{deposit['txid']}</code>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Failed to send pending deposit: {e}")

async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approve/reject callback queries"""
    query = update.callback_query
    await query.answer()

    try:
        action, *rest = query.data.split(':')
        if action == "approve" and len(rest) == 2:
            txid, user_id = rest
            pending_approvals[query.from_user.id] = {
                "txid": txid,
                "user_id": int(user_id)
            }
            await query.message.reply_text(f"💵 Enter amount for TXID {txid}:")
            
        elif action == "reject" and len(rest) == 1:
            txid = rest[0]
            pending = [p for p in load_pending() if p['txid'] != txid]
            save_pending(pending)
            await query.message.reply_text(f"❌ Rejected TXID: {txid}")

    except Exception as e:
        logging.error(f"Callback handling error: {e}")
        await query.message.reply_text("❌ Error processing request")

async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin's amount input for approvals"""
    admin_id = update.effective_user.id
    if admin_id != ADMIN_ID or admin_id not in pending_approvals:
        return

    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Please enter a positive number.")
        return

    # Get transaction data
    tx_data = pending_approvals.pop(admin_id)
    
    # Update user balance
    user_data = load_user(tx_data['user_id'])
    user_data.setdefault('balance', 0.0)
    user_data['balance'] += amount
    
    # Add transaction history
    user_data.setdefault('transactions', [])
    user_data['transactions'].append({
        'txid': tx_data['txid'],
        'amount': amount,
        'status': 'approved'
    })
    
    save_user(tx_data['user_id'], user_data)
    
    # Remove from pending
    pending = [p for p in load_pending() if p['txid'] != tx_data['txid']]
    save_pending(pending)
    
    # Notify admin and user
    await update.message.reply_text(f"✅ Approved ${amount:.2f} for TXID {tx_data['txid']}")
    await context.bot.send_message(
        chat_id=tx_data['user_id'],
        text=f"🎉 Your deposit of ${amount:.2f} has been approved!"
    )

# In your main bot.py file add these handlers:
def register_pending_handlers(app):
    app.add_handler(CommandHandler("pending", pending_command_handler))
    app.add_handler(CallbackQueryHandler(handle_approval_callback))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.User(ADMIN_ID),
        handle_amount_input
    ))