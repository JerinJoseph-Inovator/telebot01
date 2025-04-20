# handlers/top_up.py
import logging
import re
import json
import uuid
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from pathlib import Path
from datetime import datetime

from utils.json_manager import load_data
from utils.keyboards import add_back_button
from utils.pending import load_pending, save_pending

ADMIN_ID = 1188902990

async def top_up_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show deposit methods and available balance option"""
    data = load_data()
    keyboard = [
        [f"Deposit {method}"] for method in data["deposit_methods"]
    ]
    keyboard.append(["Available Balance"])
    keyboard = add_back_button(keyboard, back_to="main")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Choose a deposit method:",
        reply_markup=reply_markup
    )

async def deposit_method_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show wallet address for selected deposit method"""
    method = update.message.text.replace("Deposit ", "")
    data = load_data()

    if method not in data["deposit_methods"]:
        await update.message.reply_text("❌ Invalid deposit method")
        return

    address = data["deposit_methods"][method]["wallet"]
    await update.message.reply_text(
        f"<b>Send only {method} to the address below and submit your transaction hash/ID under the Available Balance section. Minimum deposit is $100.</b>\n\n"
        f"<code>{address}</code>\n\nClick to copy.",
        parse_mode="HTML"
    )

async def available_balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle balance checks and transaction submissions"""
    msg = update.message.text.strip()

    if msg == "Available Balance":
        await show_balance_instructions(update)
        return

    # TXID format validation
    if not re.match(r"^[a-zA-Z0-9\-_=+/]{20,}$", msg):
        await update.message.reply_text("❌ Invalid Transaction ID format")
        return

    await handle_txid_submission(update, context, msg)

async def show_balance_instructions(update: Update):
    """Show the user's current balance and deposit instructions"""
    user_id = update.effective_user.id
    project_root = Path(__file__).resolve().parent.parent
    user_file = project_root / "user" / f"{user_id}.json"

    try:
        if user_file.exists():
            with open(user_file, 'r') as f:
                user_data = json.load(f)
                balance = user_data.get('balance', 0.0)
        else:
            balance = 0.0

        formatted_balance = "${:,.2f}".format(balance)

        response = (
            f"💳 *Your Current Balance:* {formatted_balance}\n\n"
            "📥 *Need to Add Funds?*\n"
            "1. Make a deposit using one of our payment methods\n"
            "2. Enter your Transaction ID here\n\n"
            "🔍 <a href=\"https://youtu.be/yh6Oy-nkPd8?si=dhd_BSiE78-QIBsP\">"
            "How to find your Transaction ID</a>"
        )

        await update.message.reply_text(
            response,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as e:
        logging.error(f"Error showing balance for user {user_id}: {str(e)}")
        await update.message.reply_text(
            "⚠️ We couldn't retrieve your balance. Please try again later.\n\n"
            "You can still submit your Transaction ID for deposit verification.",
            parse_mode="HTML"
        )

async def handle_txid_submission(update: Update, context: ContextTypes.DEFAULT_TYPE, txid: str):
    """Process valid TXID submissions and notify the admin"""
    try:
        user = update.effective_user

        # Generate a short alias
        alias = str(uuid.uuid4())[:8]

        # Save to pending.json
        pending = load_pending()
        pending.append({
            "alias": alias,
            "user_id": user.id,
            "username": user.username or "Unknown",
            "txid": txid,
            "timestamp": datetime.now().isoformat()
        })
        save_pending(pending)

        await update.message.reply_text("✅ Transaction submitted for review. It may take up to 24 hours for approval.")

        # Notify admin directly
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{alias}:{user.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{alias}")
            ]
        ])

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🧾 *New Deposit Request*\n\n"
                f"👤 User: @{user.username or 'unknown'}\n"
                f"🆔 TXID: <code>{txid}</code>\n"
                f"🔑 Alias: `{alias}`\n"
                f"🕒 Submitted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    except Exception as e:
        logging.error(f"Failed to handle TXID submission: {e}")
