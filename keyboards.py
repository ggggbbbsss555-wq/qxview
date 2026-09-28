"""
Keyboard layout module for the Telegram bot
Mixed layout pattern: 2 buttons side-by-side, then 1 full-width button, alternating.
All button labels are in English with colored emoji (🔵🔴🟢🟡🟣).
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    JOIN_CHANNEL_URL, LIVE_CHART_URL, QUOTEX_HUB_URL,
    RESULTS_CHANNEL_URL, SUPPORT_URL, FREE_BOTS_URL,
    REFERRAL_LINK_TEMPLATE, BOT_USERNAME, COLOR_BLUE, COLOR_RED, COLOR_GREEN
)


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Main menu keyboard - mixed layout pattern (2-1-2-1-2-1-2-1-2)
    Row 1: 2 buttons side-by-side
    Row 2: 1 full-width button
    Row 3: 2 buttons side-by-side
    Row 4: 1 full-width button
    Row 5: 2 buttons side-by-side
    Row 6: 1 full-width button
    Row 7: 2 buttons side-by-side
    Row 8: 1 full-width button
    Row 9: 2 buttons side-by-side
    """
    keyboard = [
        # Row 1 - 2 buttons side-by-side
        [
            InlineKeyboardButton(
                f"{COLOR_BLUE} Join Channel",
                url=JOIN_CHANNEL_URL
            ),
            InlineKeyboardButton(
                f"{COLOR_RED} Live Chart",
                url=LIVE_CHART_URL
            ),
        ],
        # Row 2 - 1 full-width button
        [
            InlineKeyboardButton(
                f"{COLOR_GREEN} Quotex Hub",
                url=QUOTEX_HUB_URL
            ),
        ],
        # Row 3 - 2 buttons side-by-side
        [
            InlineKeyboardButton(
                f"{COLOR_BLUE} Subscription Plans",
                callback_data="plans"
            ),
            InlineKeyboardButton(
                f"{COLOR_GREEN} Current Signals",
                callback_data="current_signals"
            ),
        ],
        # Row 4 - 1 full-width button
        [
            InlineKeyboardButton(
                f"{COLOR_RED} Time Schedule",
                callback_data="time_list"
            ),
        ],
        # Row 5 - 2 buttons side-by-side
        [
            InlineKeyboardButton(
                f"{COLOR_BLUE} Free Bots",
                callback_data="free_bots"
            ),
            InlineKeyboardButton(
                f"{COLOR_GREEN} Bot Control",
                callback_data="control_bot"
            ),
        ],
        # Row 6 - 1 full-width button
        [
            InlineKeyboardButton(
                f"{COLOR_RED} Top Payout Currencies",
                callback_data="top_payout"
            ),
        ],
        # Row 7 - 2 buttons side-by-side
        [
            InlineKeyboardButton(
                f"{COLOR_BLUE} Future Signals",
                callback_data="future_signals"
            ),
            InlineKeyboardButton(
                f"{COLOR_RED} Future Signals Results",
                callback_data="future_results"
            ),
        ],
        # Row 8 - 1 full-width button
        [
            InlineKeyboardButton(
                f"{COLOR_GREEN} Referral Link",
                callback_data="referral_link"
            ),
        ],
        # Row 9 - 2 buttons side-by-side
        [
            InlineKeyboardButton(
                f"{COLOR_BLUE} My Account",
                callback_data="my_account"
            ),
            InlineKeyboardButton(
                f"{COLOR_RED} Support",
                callback_data="support"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Back to main menu button"""
    keyboard = [
        [InlineKeyboardButton(f"{COLOR_BLUE} Back to Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_plans_keyboard() -> InlineKeyboardMarkup:
    """Plans keyboard - mixed layout (1-1-1-1-1)"""
    keyboard = [
        [InlineKeyboardButton(f"{COLOR_GREEN} Free Plan - $0", callback_data="plan_free")],
        [InlineKeyboardButton(f"{COLOR_BLUE} Weekly Plan - $15", callback_data="plan_weekly")],
        [InlineKeyboardButton(f"{COLOR_RED} Monthly Plan - $45", callback_data="plan_monthly")],
        [InlineKeyboardButton(f"{COLOR_GREEN} Gold Plan - $120", callback_data="plan_gold")],
        [InlineKeyboardButton(f"{COLOR_BLUE} Back", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_control_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
    """Bot control keyboard (admins only)"""
    if not is_admin:
        return get_back_keyboard()

    keyboard = [
        # Row 1 - 2 buttons
        [
            InlineKeyboardButton(f"{COLOR_GREEN} New Signal", callback_data="admin_new_signal"),
            InlineKeyboardButton(f"{COLOR_BLUE} Broadcast", callback_data="admin_broadcast"),
        ],
        # Row 2 - 1 full-width
        [InlineKeyboardButton(f"{COLOR_RED} Bot Statistics", callback_data="admin_stats")],
        # Row 3 - back
        [InlineKeyboardButton(f"{COLOR_BLUE} Back", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_confirm_keyboard() -> InlineKeyboardMarkup:
    """Admin confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(f"{COLOR_GREEN} Yes, Send", callback_data="admin_confirm_send"),
            InlineKeyboardButton(f"{COLOR_RED} Cancel", callback_data="control_bot"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
