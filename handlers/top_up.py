from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.json_manager import load_data
from utils.keyboards import add_back_button
from utils.pending import load_pending, save_pending

ADMIN_ID = 1188902990  # Replace this with your Telegram user ID

async def top_up_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    keyboard = [[f"Deposit {method}"] for method in data["deposit_methods"]]
    keyboard.append(["Available Balance"])
    keyboard = add_back_button(keyboard, back_to="main")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose a deposit method:", reply_markup=reply_markup)


async def deposit_method_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method = update.message.text.replace("Deposit ", "")
    data = load_data()
    if method in data["deposit_methods"]:
        address = data["deposit_methods"][method]["wallet"]
        await update.message.reply_text(
            f"<b>Send only {method} to the address below and submit your transaction hash/ID under the Available Balance section. Minimum deposit is $100.</b>\n\n"
            f"<code>{address}</code>\n\nClick to copy.",
            parse_mode="HTML"
        )


async def available_balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()

    # crude check if user is pasting a TXID
    if len(msg) > 20 and all(c.isalnum() or c in "-_" for c in msg):
        pending = load_pending()
        pending.append({
            "user_id": update.effective_user.id,
            "username": update.effective_user.username or "",
            "txid": msg
        })
        save_pending(pending)

        await update.message.reply_text("✅ Transaction submitted for review. Admin will verify shortly.")

        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{msg}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{msg}")
            ]
        ]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📝 New deposit pending\n\nUser: @{update.effective_user.username}\nTXID: <code>{msg}</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            'Balance: 💲0.00\n\n'
            '🗒 Made a Deposit? Enter transaction ID below\n'
            '<a href="https://youtu.be/yh6Oy-nkPd8?si=dhd_BSiE78-QIBsP">How to get transaction ID</a>',
            parse_mode="HTML", disable_web_page_preview=True
        )
