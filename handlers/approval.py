from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from utils.approval import pending_approvals, handle_rejection
from utils.user_manager import add_deposit
from config import ADMIN_ID

async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(':')
    action = data[0]
    
    if action == "approve" and len(data) == 3:
        txid, user_id = data[1], int(data[2])
        await handle_approval(update, context, txid, user_id)
        
    elif action == "reject" and len(data) == 2:
        txid = data[1]
        handle_rejection(txid)
        await query.message.reply_text(f"❌ Rejected TXID: {txid}")

async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    if admin_id != ADMIN_ID or admin_id not in pending_approvals:
        return

    try:
        amount = float(update.message.text)
        tx_data = pending_approvals.pop(admin_id)
        
        # Update user balance and history
        user = add_deposit(
            user_id=tx_data['user_id'],
            amount=amount,
            txid=tx_data['txid']
        )
        
        # Notify user
        await context.bot.send_message(
            tx_data['user_id'],
            f"🎉 Your deposit of ${amount:.2f} has been approved!"
        )
        
        await update.message.reply_text(
            f"✅ Approved ${amount:.2f} for user {tx_data['user_id']}"
        )

    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Please enter a number.")