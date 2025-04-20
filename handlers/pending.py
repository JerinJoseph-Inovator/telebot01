import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from html import escape

from utils.pending import load_pending, save_pending
from utils.user_manager import load_user, save_user
from utils.deposit import add_deposit
from config import ADMIN_ID

pending_approvals = {}

# Handles the /pendingdeposits command
async def pending_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        if update.message:
            await update.message.reply_text("❌ Unauthorized access")
        return

    pending = load_pending()
    if not pending:
        await context.bot.send_message(chat_id=ADMIN_ID, text="✅ No pending deposits")
        return

    for deposit in pending:
        try:
            alias = deposit.get('alias')
            txid = deposit.get('txid')
            user_id = deposit.get('user_id')
            username = deposit.get('username', 'Unknown')
            safe_username = escape(username)

            if not alias or not txid or not user_id:
                logging.warning(f"Invalid pending entry: {deposit}")
                continue

            keyboard = InlineKeyboardMarkup([[ 
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{alias}:{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{alias}")
            ]])

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📝 Pending Deposit\n"
                     f"User: @{safe_username}\n"
                     f"TXID: <code>{escape(txid)}</code>\n"
                     f"Alias: `{alias}`",
                reply_markup=keyboard,
                parse_mode="HTML"
            )

        except Exception as e:
            logging.error(f"Pending display error: {e}", exc_info=True)
            await context.bot.send_message(chat_id=ADMIN_ID, text="⚠️ Error showing pending deposits")

# Handles Approve/Reject button presses
async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("❌ You're not authorized")
        return

    try:
        data = query.data.split(':')
        action = data[0]

        pending = load_pending()

        if action == "approve" and len(data) == 3:
            alias, user_id = data[1], int(data[2])
            deposit = next((p for p in pending if p.get("alias") == alias and p.get("user_id") == user_id), None)

            if not deposit:
                await context.bot.send_message(chat_id=ADMIN_ID, text="⚠️ Pending deposit not found.")
                return

            txid = deposit["txid"]
            pending_approvals[query.from_user.id] = {
                "txid": txid,
                "user_id": user_id
            }

            await context.bot.send_message(chat_id=ADMIN_ID, text=f"💰 Enter amount to approve for TXID:\n<code>{txid}</code>", parse_mode="HTML")

        elif action == "reject" and len(data) == 2:
            alias = data[1]
            deposit = next((p for p in pending if p.get("alias") == alias), None)

            if not deposit:
                await context.bot.send_message(chat_id=ADMIN_ID, text="⚠️ Deposit not found.")
                return

            try:
                await context.bot.send_message(
                    chat_id=deposit["user_id"],
                    text="❌ Your deposit was rejected. Please contact support."
                )
            except Exception as e:
                logging.warning(f"Couldn't notify user of rejection: {e}")

            # Remove from pending and save
            pending = [p for p in pending if p.get("alias") != alias]
            save_pending(pending)

            await context.bot.send_message(chat_id=ADMIN_ID, text=f"❌ Rejected TXID: {deposit['txid']}")

    except Exception as e:
        logging.error(f"Callback error: {e}", exc_info=True)
        await context.bot.send_message(chat_id=ADMIN_ID, text="❌ Error processing request")

# Handles amount entry by admin after approving
async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    if admin_id != ADMIN_ID:
        return
    if admin_id not in pending_approvals:
        return

    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError("Amount must be positive")

        tx_data = pending_approvals.pop(admin_id)

        # Save the deposit
        add_deposit(
            user_id=tx_data["user_id"],
            amount=amount,
            txid=tx_data["txid"],
            service="deposit"
        )

        # Remove from pending
        pending = load_pending()
        pending = [p for p in pending if p.get("txid") != tx_data["txid"]]
        save_pending(pending)

        # Notify both parties
        await update.message.reply_text(f"✅ Approved ${amount:.2f}")
        await context.bot.send_message(
            chat_id=tx_data["user_id"],
            text=f"🎉 ${amount:.2f} has been added to your balance!"
        )

    except ValueError:
        await update.message.reply_text("❌ Please enter a valid positive number")
    except Exception as e:
        logging.error(f"Deposit approval error: {e}", exc_info=True)
        await update.message.reply_text("❌ Failed to process approval")
