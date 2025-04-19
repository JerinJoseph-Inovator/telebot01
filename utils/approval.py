from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.pending import load_pending, save_pending
from utils.user_manager import add_deposit
from config import ADMIN_ID

pending_approvals = {}  # {admin_id: {txid: str, user_id: int}}

async def handle_approval(update, context, txid, user_id):
    """Common approval handler for all deposit types"""
    pending_approvals[update.effective_user.id] = {
        'txid': txid,
        'user_id': user_id
    }
    await update.callback_query.message.reply_text(
        f"💰 Enter amount for TXID {txid}:",
        parse_mode="HTML"
    )

async def handle_rejection(txid):
    """Common rejection handler"""
    pending = [p for p in load_pending() if p['txid'] != txid]
    save_pending(pending)



def create_approval_keyboard(txid: str, user_id: int) -> InlineKeyboardMarkup:
    """Create properly formatted inline keyboard"""
    return InlineKeyboardMarkup([
        [  # First row
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{txid}:{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject:{txid}")
        ]
    ])