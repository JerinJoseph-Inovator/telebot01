from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.json_manager import load_data
from utils.keyboards import add_back_button
from utils.pending import load_pending, save_pending

ADMIN_ID = 1188902990  # Your Telegram user ID

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
    
    # First check if it's a menu button press
    if msg == "Available Balance":
        await show_balance_instructions(update)
        return
        
    # Then handle TXID submission
    await handle_txid_submission(update, context, msg)

async def show_balance_instructions(update: Update):
    """Show balance information and TXID instructions"""
    await update.message.reply_text(
        'Balance: 💲0.00\n\n'
        '🗒 Made a Deposit? Enter transaction ID below\n'
        '<a href="https://youtu.be/yh6Oy-nkPd8?si=dhd_BSiE78-QIBsP">How to get transaction ID</a>',
        parse_mode="HTML", 
        disable_web_page_preview=True
    )

async def handle_txid_submission(update: Update, context: ContextTypes.DEFAULT_TYPE, txid: str):
    """Process valid TXID submissions"""
    pending = load_pending()
    pending.append({
        "user_id": update.effective_user.id,
        "username": update.effective_user.username or "Unknown",
        "txid": txid
    })
    save_pending(pending)

    # User confirmation
    await update.message.reply_text("✅ Transaction submitted for review. It may take up to 24 hours for approval.")

    # Admin notification
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{txid}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject:{txid}")
        ]
    ]
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📝 New deposit pending\n\nUser: @{update.effective_user.username}\nTXID: <code>{txid}</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Failed to notify admin: {e}")