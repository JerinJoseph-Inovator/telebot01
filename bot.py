# bot.py
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)

from utils.json_manager import load_stock
from handlers.main_menu import main_menu
from handlers.gift_cards import gift_cards_handler, gift_card_offer_handler, handle_gift_card_purchase
from handlers.streaming_services import streaming_handler, streaming_plan_handler, handle_streaming_purchase
from handlers.top_up import top_up_handler, deposit_method_handler, available_balance_handler
from handlers.referrals import referrals_handler
from handlers.coupons.coupons import apply_coupon_handler

# admin‐stock flows
from handlers.admin_stock import admin_panel, admin_callback_handler, handle_admin_stock_input
# deposit‐approval flows
from handlers.deposit_approvals import list_pending, handle_admin_callback as deposit_callback, handle_deposit_approval_input

from config import BOT_TOKEN

ADMIN_ID = 1188902990

# configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)


async def dynamic_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    1) If text exactly matches a gift-card brand -> gift_card_offer_handler
    2) Else if it matches a streaming service -> streaming_plan_handler
    3) Else if it matches a purchase offer -> handle_gift_card_purchase or handle_streaming_purchase
    Otherwise: ignore.
    """
    text = update.message.text.strip()
    stock = load_stock()

    # 1) gift-card brand
    if text in stock.get("gift_cards", {}):
        return await gift_card_offer_handler(update, context)

    # 2) streaming service
    if text in stock.get("streaming_services", {}):
        return await streaming_plan_handler(update, context)

    # 3a) gift-card purchase pattern
    if re.fullmatch(r"\$\d+(?:\.\d+)? for \$\d+(?:\.\d+)?", text):
        return await handle_gift_card_purchase(update, context)

    # 3b) streaming purchase pattern
    if re.fullmatch(r"\d+\s(?:Month|Year)s? - \$\d+(?:\.\d{1,2})?", text):
        return await handle_streaming_purchase(update, context)

    # else do nothing (will fall through)
    # you could optionally call `await main_menu(update, context)` here.


def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ─── Group 0: Admin‐stock flows ────────────────────────────────
    app.add_handler(CommandHandler("admin", admin_panel), group=0)
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern=r"^admin:"), group=0)
    app.add_handler(
        MessageHandler(
            filters.TEXT & filters.User(ADMIN_ID) & ~filters.COMMAND,
            handle_admin_stock_input,
        ),
        group=0,
    )

    # ─── Group 1: Dynamic router ──────────────────────────────────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, dynamic_router),
        group=1,
    )

    # ─── Group 2: Static menus & back buttons ────────────────────
    app.add_handler(CommandHandler("start", main_menu), group=2)
    app.add_handler(CommandHandler("menu", main_menu), group=2)

    # top‐level menu buttons
    for label, handler in {
        "🎁 Gift Cards": gift_cards_handler,
        "🎬 Streaming Services": streaming_handler,
        "💳 Balance Top Up": top_up_handler,
        "Available Balance": available_balance_handler,
        "🏷️ Apply Coupon": apply_coupon_handler,
        "👥 Referrals": referrals_handler,
    }.items():
        app.add_handler(
            MessageHandler(filters.TEXT & filters.Regex(f"^{re.escape(label)}$"), handler),
            group=2,
        )

    # back buttons
    for label, handler in {
        "🔙 Back to Main Menu": main_menu,
        "🔙 Back to Gift Cards": gift_cards_handler,
        "🔙 Back to Streaming Services": streaming_handler,
        "🔙 Back to Coupons": apply_coupon_handler,
    }.items():
        app.add_handler(
            MessageHandler(filters.TEXT & filters.Regex(f"^{re.escape(label)}$"), handler),
            group=2,
        )

    # top-up flows
    app.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(r"^Deposit "), deposit_method_handler),
        group=2,
    )
    app.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(r"^[A-Za-z0-9\-_=+/]{20,}$"), available_balance_handler),
        group=2,
    )

    # ─── Group 3: Deposit approvals ────────────────────────────────
    app.add_handler(CommandHandler("pending", list_pending), group=3)
    app.add_handler(CallbackQueryHandler(deposit_callback, pattern=r"^(approve|reject):"), group=3)
    app.add_handler(
        MessageHandler(
            filters.TEXT & filters.User(ADMIN_ID) & ~filters.COMMAND,
            handle_deposit_approval_input,
        ),
        group=3,
    )

    app.run_polling()


if __name__ == "__main__":
    main()
