import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils.pending import load_pending, save_pending
from utils.user_manager import add_deposit
from config import ADMIN_ID

# Tracks admins in the middle of an approval
_pending_map: dict[int, dict] = {}

async def list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ You don't have permission.")
    pending = load_pending()
    if not pending:
        return await update.message.reply_text("✅ No pending deposits.")
    await update.message.reply_text(f"📋 {len(pending)} pending:")
    for p in pending:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{p['txid']}:{p['user_id']}"),
            InlineKeyboardButton("❌ Reject",  callback_data=f"reject:{p['txid']}")
        ]])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🧾 User: @{p.get('username','unknown')}\nTXID: <code>{p['txid']}</code>",
            parse_mode="HTML",
            reply_markup=keyboard,
        )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        action, *rest = query.data.split(":")
        if action == "approve" and len(rest) == 2:
            txid, user_id = rest[0], int(rest[1])
            _pending_map[query.from_user.id] = {"txid": txid, "user_id": user_id}
            return await query.message.reply_text(f"💰 Enter amount for TXID <code>{txid}</code>:", parse_mode="HTML")
        if action == "reject" and len(rest) == 1:
            txid = rest[0]
            remaining = [x for x in load_pending() if x["txid"] != txid]
            save_pending(remaining)
            return await query.message.reply_text(f"❌ Rejected TXID <code>{txid}</code>.", parse_mode="HTML")
    except Exception as e:
        logging.error("Deposit callback error", exc_info=e)
        await query.message.reply_text("❌ Error processing request")

async def handle_deposit_approval_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    if admin_id not in _pending_map:
        return
    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError("Must be positive")
        tx = _pending_map.pop(admin_id)
        add_deposit(user_id=tx["user_id"], amount=amount, txid=tx["txid"], service="top_up")
        remaining = [x for x in load_pending() if x["txid"] != tx["txid"]]
        save_pending(remaining)
        await update.message.reply_text(f"✅ Approved ${amount:.2f} for {tx['user_id']}.")
        await context.bot.send_message(
            tx["user_id"],
            f"🎉 Your deposit of ${amount:.2f} has been approved and added!"
        )
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid positive number.")
    except Exception as e:
        logging.error("Approval error", exc_info=e)
        await update.message.reply_text("❌ Failed to process approval.")
