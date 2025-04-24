# handlers/streaming_services.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.json_manager import load_stock
from utils.keyboards import add_back_button
from utils.user_manager import deduct_balance
from handlers.main_menu import main_menu
from config import ADMIN_ID
import logging
import re

async def streaming_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available streaming service brands"""
    stock = load_stock()
    services = list(stock.get("streaming_services", {}).keys())
    keyboard = [[s] for s in services]
    keyboard = add_back_button(keyboard, back_to="main")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose a Streaming Service:", reply_markup=reply_markup)

async def streaming_plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available plans for selected streaming service"""
    selected = update.message.text

    if selected == "🔙 Back to Main Menu":
        await main_menu(update, context)
        return

    stock = load_stock()
    plans_dict = stock.get("streaming_services", {}).get(selected, {})

    # Only show available plans
    available_plans = [plan for plan, available in plans_dict.items() if available]

    if not available_plans:
        await update.message.reply_text("❌ No available plans. Please try again later.")
        return

    context.user_data["selected_service"] = selected

    keyboard = [[plan] for plan in available_plans]
    keyboard = add_back_button(keyboard, back_to="streaming_services")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"{selected} Plans:", reply_markup=reply_markup)

async def handle_streaming_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the purchase of a selected plan"""
    try:
        user_id = update.effective_user.id
        plan_text = update.message.text
        service = context.user_data.get("selected_service")

        if plan_text == "🔙 Back to Streaming Services":
            await streaming_handler(update, context)
            return

        if not service:
            await update.message.reply_text("Please select a service first.")
            return

        match = re.match(r"^(\d+\s(?:Month|Year)s?) - \$(\d+(?:\.\d{1,2})?)$", plan_text)
        if not match:
            await update.message.reply_text("Invalid plan format. Please try again.")
            return

        duration = match.group(1)
        price = float(match.group(2))

        success = deduct_balance(
            user_id=user_id,
            amount=price,
            service="streaming",
            provider=service,
            duration=duration
        )

        if success:
            await update.message.reply_text(
                f"✅ Subscription confirmed! Your {service} {duration} plan "
                f"will be activated within 24 hours.\n\n"
                f"💳 ${price:.2f} has been deducted from your balance."
            )
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🎬 New Subscription\n\n"
                     f"👤 User: @{update.effective_user.username or update.effective_user.full_name}\n"
                     f"📺 Service: {service} {duration}\n"
                     f"💰 Price: ${price:.2f}\n"
                     f"⏳ Please activate within 24 hours"
            )
        else:
            await update.message.reply_text("❌ Insufficient balance. Please top up your account.")
    except Exception as e:
        logging.error(f"Streaming purchase error: {e}", exc_info=True)
        await update.message.reply_text("⚠️ An error occurred. Please try again later.")
