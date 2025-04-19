import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from utils.pending import load_pending, save_pending
from utils.user_manager import load_user, save_user
from config import ADMIN_ID

pending_approvals = {}

async def pending_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    pending = load_pending()
    if not pending:
        await update.message.reply_text("✅ No pending deposits")
        return

    for deposit in pending:
        try:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{deposit['txid']}:{deposit['user_id']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{deposit['txid']}")
            ]])
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📝 Pending Deposit\n"
                     f"User: @{deposit.get('username', 'Unknown')}\n"
                     f"TXID: <code>{deposit['txid']}</code>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Error showing pending deposit: {e}")

async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            pending = [p for p in load_pending() if p['txid'] != txid]
            save_pending(pending)
            await query.message.reply_text(f"❌ Rejected TXID: {txid}")
            await context.bot.send_message(
                next((p['user_id'] for p in pending if p['txid'] == txid), 
                "❌ Your deposit was rejected")
            )

    except Exception as e:
        logging.error(f"Callback error: {e}")

async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    if admin_id != ADMIN_ID or admin_id not in pending_approvals:
        return

    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError
            
        tx_data = pending_approvals.pop(admin_id)
        user_data = load_user(tx_data['user_id'])
        
        # Update balance and transactions
        user_data['balance'] = user_data.get('balance', 0.0) + amount
        user_data.setdefault('transactions', []).append({
            'txid': tx_data['txid'],
            'amount': amount,
            'status': 'approved'
        })
        
        save_user(tx_data['user_id'], user_data)
        
        # Remove from pending
        pending = [p for p in load_pending() if p['txid'] != tx_data['txid']]
        save_pending(pending)
        
        # Send notifications
        await update.message.reply_text(f"✅ Approved ${amount:.2f}")
        await context.bot.send_message(
            tx_data['user_id'],
            f"🎉 ${amount:.2f} has been added to your balance!"
        )

    except ValueError:
        await update.message.reply_text("❌ Invalid amount")

def register_pending_handlers(app):
    app.add_handler(CommandHandler("pending", pending_command_handler))
    app.add_handler(CallbackQueryHandler(handle_approval_callback))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.User(ADMIN_ID),
        handle_amount_input
    ))