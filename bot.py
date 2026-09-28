"""
================================================================
Advanced Trading Signals Telegram Bot (Single File Version)
================================================================
Built with python-telegram-bot v20.7

Features:
- Mixed keyboard layout (2-1-2-1-2-1-2-1-2 pattern)
- 14 colored buttons (English)
- SQLite database for referrals
- Admin control panel
- Broadcast & signal sending to channel
- Welcome message + referral system
- Auto-fetches bot username on startup

Just run: python bot.py
================================================================
"""

import logging
import os
import sys
import sqlite3
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode, KeyboardButtonStyle

# ============================================================
# 1) CONFIGURATION
# ============================================================

# Bot token from @BotFather
BOT_TOKEN = "8825955443:AAGk3WzJHfYvSHObwXNE1HRsy2PrEbzNnxc"

# Bot username (auto-updated on startup, leave as is)
BOT_USERNAME = "your_bot_username"

# Channel & resource URLs
JOIN_CHANNEL_URL = "https://t.me/your_channel"
JOIN_CHANNEL_USERNAME = "@your_channel"
LIVE_CHART_URL = "https://www.tradingview.com/chart/"
QUOTEX_HUB_URL = "https://quotex.io/"
SIGNALS_CHANNEL_ID = "@your_signals_channel"
RESULTS_CHANNEL_URL = "https://t.me/your_results_channel"
SUPPORT_URL = "https://t.me/your_support"
FREE_BOTS_URL = "https://t.me/your_free_bots"

# Admin IDs (get yours from @userinfobot)
ADMIN_IDS = [
    123456789,  # Replace with your Telegram user ID
]

# Subscription plans
PLANS = [
    {
        "name": "Free Plan",
        "price": "$0",
        "duration": "7 days",
        "features": [
            "Limited signals (3 signals per day)",
            "Access to basic time list",
            "Bot-only support",
        ],
    },
    {
        "name": "Weekly Plan",
        "price": "$15",
        "duration": "7 days",
        "features": [
            "Unlimited signals",
            "Full access to time list",
            "Instant alerts",
            "VIP support",
        ],
    },
    {
        "name": "Monthly Plan",
        "price": "$45",
        "duration": "30 days",
        "features": [
            "All weekly plan features",
            "Top payout currencies analysis",
            "Exclusive future signals",
            "Weekly training sessions",
        ],
    },
    {
        "name": "Gold Plan",
        "price": "$120",
        "duration": "90 days",
        "features": [
            "All monthly plan features",
            "Personal account manager",
            "Custom VIP signals",
            "Exclusive training workshops",
        ],
    },
]

# ============================================================
# COLOR SYSTEM - Native Telegram Button Styles (v22.7+)
# ============================================================
# Telegram Bot API 9.4+ supports NATIVE colored button backgrounds!
# Requires python-telegram-bot >= 22.7 (we use 22.8)
# Works on Telegram client builds released AFTER February 9, 2026.
# Older clients will display buttons without styling (graceful fallback).
#
# Only 3 colors are supported by Telegram:
#   - PRIMARY  → Blue background
#   - SUCCESS  → Green background
#   - DANGER   → Red background
# ============================================================

# Style aliases for cleaner code
STYLE_BLUE = KeyboardButtonStyle.PRIMARY    # 🔵 Blue
STYLE_GREEN = KeyboardButtonStyle.SUCCESS   # 🟢 Green
STYLE_RED = KeyboardButtonStyle.DANGER      # 🔴 Red

# Keep emoji constants for MESSAGE text (not buttons)
COLOR_BLUE = "🔵"
COLOR_RED = "🔴"
COLOR_GREEN = "🟢"
COLOR_YELLOW = "🟡"
COLOR_PURPLE = "🟣"

# Referral link template (auto-updated on startup)
REFERRAL_LINK_TEMPLATE = f"https://t.me/{BOT_USERNAME}?start=ref_{{user_id}}"


def validate_config():
    """Validate that required settings are present."""
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set!")
        return False
    return True


# ============================================================
# 2) DATABASE (SQLite)
# ============================================================

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_database.db")


def init_db():
    """Initialize database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        join_date TEXT,
        referrer_id INTEGER DEFAULT NULL,
        referral_count INTEGER DEFAULT 0,
        is_premium INTEGER DEFAULT 0,
        plan TEXT DEFAULT 'free'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        date TEXT,
        joined_channel INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        currency TEXT,
        direction TEXT,
        entry_price REAL,
        expiry TEXT,
        time TEXT,
        status TEXT DEFAULT 'pending'
    )
    """)

    conn.commit()
    conn.close()


def add_user(user_id, username=None, first_name=None, referrer_id=None):
    """Add new user. Returns True if added, False if already exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute("""
    INSERT INTO users (user_id, username, first_name, join_date, referrer_id, referral_count, is_premium, plan)
    VALUES (?, ?, ?, ?, ?, 0, 0, 'free')
    """, (user_id, username, first_name, datetime.now().isoformat(), referrer_id))

    if referrer_id and referrer_id != user_id:
        cursor.execute(
            "SELECT id FROM referrals WHERE referrer_id = ? AND referred_id = ?",
            (referrer_id, user_id)
        )
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO referrals (referrer_id, referred_id, date, joined_channel)
            VALUES (?, ?, ?, 0)
            """, (referrer_id, user_id, datetime.now().isoformat()))
            cursor.execute(
                "UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?",
                (referrer_id,)
            )

    conn.commit()
    conn.close()
    return True


def get_user(user_id):
    """Get user data."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_referral_count(user_id):
    """Get user's referral count."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT referral_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def get_referrals_list(user_id):
    """Get list of users referred by this user."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT u.username, u.first_name, r.date, r.joined_channel
    FROM referrals r
    JOIN users u ON r.referred_id = u.user_id
    WHERE r.referrer_id = ?
    ORDER BY r.date DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_channel_join(user_id, joined=True):
    """Update channel join status."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE referrals SET joined_channel = ? WHERE referred_id = ?",
        (1 if joined else 0, user_id)
    )
    conn.commit()
    conn.close()


def is_admin(user_id):
    """Check if user is admin."""
    return user_id in ADMIN_IDS


def add_signal(currency, direction, entry_price, expiry):
    """Add a new signal."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO signals (currency, direction, entry_price, expiry, time, status)
    VALUES (?, ?, ?, ?, ?, 'pending')
    """, (currency, direction, entry_price, expiry, datetime.now().isoformat()))
    signal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return signal_id


def get_signals_stats():
    """Get signal statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) FROM signals GROUP BY status")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


def get_all_users_count():
    """Get total user count."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_all_users():
    """Get list of all users."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, join_date, referral_count, plan FROM users ORDER BY join_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============================================================
# 3) KEYBOARDS (Mixed 2-1-2-1-2-1-2-1-2 Layout)
# ============================================================

def get_main_menu_keyboard():
    """Main menu keyboard - mixed layout (2-1-2-1-2-1-2-1-2-1).
    Uses NATIVE Telegram button styles (blue/green/red backgrounds).
    Red color is reserved ONLY for genuine alert/danger actions.
    Requires python-telegram-bot v22.7+ and Telegram client > Feb 9, 2026."""
    keyboard = [
        # Row 1: 2 buttons side-by-side
        [
            InlineKeyboardButton("Join Channel", url=JOIN_CHANNEL_URL, style=STYLE_BLUE),
            InlineKeyboardButton("Live Chart", url=LIVE_CHART_URL, style=STYLE_GREEN),
        ],
        # Row 2: 1 full-width (NEW: Request Signals Now)
        [InlineKeyboardButton("⚡ Request Signals Now", callback_data="request_signals", style=STYLE_GREEN)],
        # Row 3: 2 buttons
        [
            InlineKeyboardButton("Subscription Plans", callback_data="plans", style=STYLE_BLUE),
            InlineKeyboardButton("Current Signals", callback_data="current_signals", style=STYLE_GREEN),
        ],
        # Row 4: 1 full-width
        [InlineKeyboardButton("Time Schedule", callback_data="time_list", style=STYLE_BLUE)],
        # Row 5: 2 buttons
        [
            InlineKeyboardButton("Free Bots", callback_data="free_bots", style=STYLE_BLUE),
            InlineKeyboardButton("Quotex Hub", url=QUOTEX_HUB_URL, style=STYLE_GREEN),
        ],
        # Row 6: 1 full-width
        [InlineKeyboardButton("Top Payout Currencies", callback_data="top_payout", style=STYLE_BLUE)],
        # Row 7: 2 buttons
        [
            InlineKeyboardButton("Future Signals", callback_data="future_signals", style=STYLE_GREEN),
            InlineKeyboardButton("Signals Results", callback_data="future_results", style=STYLE_BLUE),
        ],
        # Row 8: 1 full-width
        [InlineKeyboardButton("Referral Link", callback_data="referral_link", style=STYLE_GREEN)],
        # Row 9: 2 buttons
        [
            InlineKeyboardButton("Bot Control", callback_data="control_bot", style=STYLE_BLUE),
            InlineKeyboardButton("My Account", callback_data="my_account", style=STYLE_GREEN),
        ],
        # Row 10: 1 full-width (RED - reserved for support/emergency only)
        [InlineKeyboardButton("📞 Support", callback_data="support", style=STYLE_RED)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard():
    """Back to main menu."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Back to Main Menu", callback_data="main_menu", style=STYLE_BLUE)]
    ])


def get_plans_keyboard():
    """Plans selection keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Free Plan - $0", callback_data="plan_free", style=STYLE_GREEN)],
        [InlineKeyboardButton("Weekly Plan - $15", callback_data="plan_weekly", style=STYLE_BLUE)],
        [InlineKeyboardButton("Monthly Plan - $45", callback_data="plan_monthly", style=STYLE_RED)],
        [InlineKeyboardButton("Gold Plan - $120", callback_data="plan_gold", style=STYLE_GREEN)],
        [InlineKeyboardButton("Back", callback_data="main_menu", style=STYLE_BLUE)],
    ])


def get_control_keyboard(is_admin):
    """Admin control keyboard."""
    if not is_admin:
        return get_back_keyboard()
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("New Signal", callback_data="admin_new_signal", style=STYLE_GREEN),
            InlineKeyboardButton("Broadcast", callback_data="admin_broadcast", style=STYLE_BLUE),
        ],
        [InlineKeyboardButton("Bot Statistics", callback_data="admin_stats", style=STYLE_RED)],
        [InlineKeyboardButton("Back", callback_data="main_menu", style=STYLE_BLUE)],
    ])


def get_admin_confirm_keyboard():
    """Admin confirm/cancel keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes, Send", callback_data="admin_confirm_send", style=STYLE_GREEN),
            InlineKeyboardButton("Cancel", callback_data="control_bot", style=STYLE_RED),
        ]
    ])


# ============================================================
# 4) HANDLERS
# ============================================================

# Conversation states for admin
WAITING_SIGNAL_INPUT, WAITING_BROADCAST = range(2)

WELCOME_MESSAGE = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_YELLOW} Welcome to the Advanced Trading Signals Bot 🤖📈
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_GREEN} 📌 About Us
A professional bot providing accurate trading signals for currencies and financial markets,
with live analysis and 24/7 continuous monitoring.

{COLOR_BLUE} ✨ Bot Features:
{COLOR_GREEN}• {COLOR_BLUE} Instant real-time signals
{COLOR_GREEN}• {COLOR_RED} Live chart & real-time analysis
{COLOR_GREEN}• {COLOR_GREEN} Quotex Hub platform integration
{COLOR_GREEN}• {COLOR_BLUE} Multiple subscription plans for everyone
{COLOR_GREEN}• {COLOR_RED} Time schedule for upcoming sessions
{COLOR_GREEN}• {COLOR_GREEN} Top payout currencies monitoring
{COLOR_GREEN}• {COLOR_BLUE} Referral system with rewards

{COLOR_RED} ⚠️ Important Notice:
{COLOR_RED} You must join the official channel first to access all features!

{COLOR_BLUE} 🎯 Choose from the menu below to get started:
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    user_id = user.id

    referrer_id = None
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        if arg.startswith("ref_"):
            try:
                referrer_id = int(arg.replace("ref_", ""))
            except ValueError:
                referrer_id = None

    is_new = add_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        referrer_id=referrer_id
    )

    if is_new:
        logging.info(f"New user: {user_id} - @{user.username}")

    context.user_data["user_id"] = user_id

    welcome_text = WELCOME_MESSAGE
    if referrer_id:
        welcome_text += f"\n{COLOR_YELLOW} 👋 You were referred by a friend!\n"

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main callback router for all buttons."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    context.user_data["user_id"] = user_id

    if data == "main_menu":
        await show_main_menu(query)
    elif data == "plans":
        await show_plans(query)
    elif data.startswith("plan_"):
        await show_plan_details(query, data.replace("plan_", ""))
    elif data == "request_signals":
        await show_request_signals(query)
    elif data == "current_signals":
        await show_current_signals(query)
    elif data == "time_list":
        await show_time_list(query)
    elif data == "free_bots":
        await show_free_bots(query)
    elif data == "control_bot":
        await show_control_bot(query, user_id)
    elif data == "top_payout":
        await show_top_payout(query)
    elif data == "future_signals":
        await show_future_signals(query)
    elif data == "future_results":
        await show_future_results(query)
    elif data == "referral_link":
        await show_referral_link(query, user_id)
    elif data == "my_account":
        await show_my_account(query, user_id)
    elif data == "support":
        await show_support(query)
    elif data == "admin_new_signal":
        await admin_new_signal(query, context)
    elif data == "admin_broadcast":
        await admin_broadcast(query, context)
    elif data == "admin_stats":
        await admin_stats(query)
    elif data == "admin_confirm_send":
        await admin_confirm_send(query, context)


async def show_main_menu(query):
    await query.edit_message_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def show_plans(query):
    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_YELLOW} 💎 Subscription Plans 💎
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

Choose the plan that suits you from the list below:

{COLOR_GREEN} 🆓 Free Plan - $0
{COLOR_BLUE} Duration: 7 days trial
{COLOR_GREEN} Limited basic features

{COLOR_BLUE} 📅 Weekly Plan - $15
{COLOR_GREEN} Duration: 7 full days
{COLOR_GREEN} Unlimited signals + instant alerts

{COLOR_RED} 📆 Monthly Plan - $45
{COLOR_GREEN} Duration: 30 days
{COLOR_GREEN} All features + advanced analytics

{COLOR_YELLOW} 👑 Gold Plan - $120
{COLOR_GREEN} Duration: 90 days
{COLOR_GREEN} VIP features + personal account manager

Select a plan to view full details:
"""
    await query.edit_message_text(
        text, reply_markup=get_plans_keyboard(), parse_mode=ParseMode.HTML
    )


async def show_plan_details(query, plan_key):
    plans_map = {"free": PLANS[0], "weekly": PLANS[1], "monthly": PLANS[2], "gold": PLANS[3]}
    plan = plans_map.get(plan_key, PLANS[0])
    features_text = "\n".join([f"{COLOR_GREEN} ✅ {f}" for f in plan["features"]])

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_YELLOW} 📋 Plan Details
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_GREEN} Name: {plan['name']}
{COLOR_BLUE} Price: {plan['price']}
{COLOR_GREEN} Duration: {plan['duration']}

{COLOR_YELLOW} ✨ Included Features:
{features_text}

{COLOR_RED} 💳 To subscribe to this plan:
Contact technical support via the Support button in the main menu
"""
    await query.edit_message_text(text, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)


async def show_request_signals(query):
    """Show instant signals request page with countdown and live updates."""
    now = datetime.now()
    # Generate fresh, time-stamped signals (as if requested just now)
    live_signals = [
        ("EUR/USD", "CALL", "1.0856", "M1", "94%"),
        ("GBP/JPY", "PUT", "189.42", "M5", "89%"),
        ("USD/JPY", "CALL", "149.78", "M1", "91%"),
        ("AUD/CAD", "PUT", "0.9124", "M5", "88%"),
    ]

    signals_text = "\n\n".join([
        f"{COLOR_GREEN} 📊 {s[0]}\n"
        f"{COLOR_BLUE} Direction: {COLOR_GREEN if s[1] == 'CALL' else COLOR_RED} {s[1]}\n"
        f"{COLOR_BLUE} Entry: {s[2]}\n"
        f"{COLOR_BLUE} Expiry: {s[3]}\n"
        f"{COLOR_YELLOW} Confidence: {s[4]}"
        for s in live_signals
    ])

    # Next update countdown (demo)
    next_update = now + timedelta(minutes=5)

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_GREEN} ⚡ Instant Signals Request
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_YELLOW} 📅 Request Time: {now.strftime('%Y-%m-%d %H:%M:%S')}
{COLOR_GREEN} ✅ Status: Live & Active

{signals_text}

{COLOR_PURPLE} 📈 Market Summary:
{COLOR_GREEN} • Active pairs: 4
{COLOR_BLUE} • Avg confidence: 90.5%
{COLOR_GREEN} • Market sentiment: Bullish 📈

{COLOR_YELLOW} ⏰ Next refresh: {next_update.strftime('%H:%M:%S')}
{COLOR_RED} ⚠️ Trade responsibly - Not financial advice

{COLOR_BLUE} 💡 For unlimited real-time signals,
upgrade to a premium plan via "Subscription Plans".
"""
    await query.edit_message_text(text, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)


async def show_current_signals(query):
    signals = [
        ("EUR/USD", "CALL", "1.0856", "M1", "92%"),
        ("GBP/JPY", "PUT", "189.42", "M5", "88%"),
        ("USD/JPY", "CALL", "149.78", "M1", "95%"),
    ]
    signals_text = "\n\n".join([
        f"{COLOR_GREEN} 📊 {s[0]}\n"
        f"{COLOR_BLUE} Direction: {COLOR_GREEN if s[1] == 'CALL' else COLOR_RED} {s[1]}\n"
        f"{COLOR_BLUE} Entry: {s[2]}\n"
        f"{COLOR_BLUE} Expiry: {s[3]}\n"
        f"{COLOR_YELLOW} Expected Rate: {s[4]}"
        for s in signals
    ])
    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_GREEN} 📈 Live Current Signals
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{signals_text}

{COLOR_YELLOW} ⏰ Last Update: {datetime.now().strftime('%H:%M:%S')}
{COLOR_RED} ⚠️ Trade responsibly - Signals are not a profit guarantee

{COLOR_BLUE} 📌 To subscribe to premium instant signals,
use the "Subscription Plans" button
"""
    await query.edit_message_text(text, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)


async def show_time_list(query):
    now = datetime.now()
    sessions = [
        ("Tokyo Session", now + timedelta(hours=2), "🇯🇵"),
        ("London Session", now + timedelta(hours=5), "🇬🇧"),
        ("New York Session", now + timedelta(hours=9), "🇺🇸"),
        ("Sydney Session", now + timedelta(hours=14), "🇦🇺"),
    ]
    sessions_text = "\n".join([
        f"{COLOR_BLUE} {flag} {name}\n"
        f"{COLOR_GREEN} ⏰ Starts: {t.strftime('%Y-%m-%d %H:%M')}"
        for name, t, flag in sessions
    ])
    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_YELLOW} ⏰ Trading Sessions Time Schedule
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{sessions_text}

{COLOR_GREEN} 💡 Tip:
Best trading times are during session overlaps (London + New York)

{COLOR_RED} ⚠️ Times are in UTC
"""
    await query.edit_message_text(text, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)


async def show_free_bots(query):
    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_GREEN} 🎁 Available Free Bots
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_YELLOW} 🤖 Free bots you can benefit from:

{COLOR_GREEN} 1️⃣ Free Currency Signals Bot
{COLOR_BLUE} Basic analysis for major currencies

{COLOR_GREEN} 2️⃣ Price Alerts Bot
{COLOR_BLUE} Alerts when price reaches a specific level

{COLOR_GREEN} 3️⃣ Market News Bot
{COLOR_BLUE} Latest economic news as soon as published

{COLOR_GREEN} 4️⃣ Profit/Loss Calculator Bot
{COLOR_BLUE} Easily calculate your trading profits

{COLOR_RED} 🔗 To access the free bots:
Click the "Visit Free Bots" button below
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Visit Free Bots", url=FREE_BOTS_URL, style=STYLE_GREEN)],
        [InlineKeyboardButton("Back", callback_data="main_menu", style=STYLE_BLUE)],
    ])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def show_control_bot(query, user_id):
    if not is_admin(user_id):
        text = f"""
{COLOR_RED} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_RED} ⛔ Access Denied
{COLOR_RED} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_YELLOW} This feature is restricted to admins only.

{COLOR_BLUE} If you believe this is an error, please contact support.
"""
        await query.edit_message_text(text, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)
        return

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_PURPLE} 🎛️ Admin Control Panel
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_GREEN} Welcome Admin 👑

{COLOR_YELLOW} Quick Statistics:
{COLOR_BLUE} 👥 Users: {get_all_users_count()}
{COLOR_GREEN} 📊 Today's Signals: {len(get_signals_stats())}

{COLOR_GREEN} Select the desired action:
"""
    await query.edit_message_text(text, reply_markup=get_control_keyboard(is_admin=True), parse_mode=ParseMode.HTML)


async def show_top_payout(query):
    currencies = [
        ("EUR/USD OTC", "95%"),
        ("GBP/JPY OTC", "93%"),
        ("USD/JPY OTC", "92%"),
        ("AUD/CAD OTC", "91%"),
        ("EUR/GBP OTC", "90%"),
        ("USD/CHF OTC", "89%"),
    ]
    currencies_text = "\n".join([
        f"{COLOR_GREEN} {i+1}. {c[0]:<15} {COLOR_YELLOW} {c[1]}"
        for i, c in enumerate(currencies)
    ])
    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_GREEN} 💰 Top Payout Currencies Now
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{currencies_text}

{COLOR_YELLOW} 📊 Updated: {datetime.now().strftime('%H:%M')}
{COLOR_RED} ⚠️ Rates change continuously based on the market

{COLOR_BLUE} 💡 Tip: Focus on currencies with 90%+ rates for higher profit
"""
    await query.edit_message_text(text, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)


async def show_future_signals(query):
    now = datetime.now()
    future_signals = [
        ("EUR/USD", now + timedelta(minutes=15), "CALL", "M1"),
        ("GBP/USD", now + timedelta(minutes=30), "PUT", "M5"),
        ("USD/JPY", now + timedelta(hours=1), "CALL", "M1"),
    ]
    signals_text = "\n".join([
        f"{COLOR_GREEN} 📊 {s[0]}\n"
        f"{COLOR_BLUE} ⏰ {s[1].strftime('%H:%M')}\n"
        f"{COLOR_BLUE} Direction: {s[2]}\n"
        f"{COLOR_BLUE} Duration: {s[3]}"
        for s in future_signals
    ])
    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_PURPLE} 🔮 Upcoming Future Signals
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{signals_text}

{COLOR_YELLOW} ✅ To check the results of previous signals:
Use the "Future Signals Results" button next to it

{COLOR_RED} ⚠️ Future signals are a premium feature (Monthly Plan or higher)
"""
    await query.edit_message_text(text, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)


async def show_future_results(query):
    results = [
        ("EUR/USD", "CALL", "WIN", "✅", "1.0856 → 1.0862"),
        ("GBP/JPY", "PUT", "WIN", "✅", "189.42 → 189.18"),
        ("USD/CAD", "CALL", "LOSS", "❌", "1.3642 → 1.3639"),
        ("AUD/USD", "PUT", "WIN", "✅", "0.6582 → 0.6571"),
        ("EUR/GBP", "CALL", "WIN", "✅", "0.8541 → 0.8553"),
    ]
    results_text = "\n\n".join([
        f"{COLOR_GREEN} 📊 {r[0]} | {r[1]}\n"
        f"{'✅' if r[2] == 'WIN' else '❌'} Result: {r[2]}\n"
        f"📈 Movement: {r[4]}"
        for r in results
    ])
    wins = sum(1 for r in results if r[2] == "WIN")
    total = len(results)
    win_rate = (wins / total * 100) if total > 0 else 0

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_GREEN} 📊 Future Signals Results
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{results_text}

{COLOR_YELLOW} 📈 Performance Statistics:
{COLOR_GREEN} ✅ Winning signals: {wins}
{COLOR_RED} ❌ Losing signals: {total - wins}
{COLOR_BLUE} 📊 Win rate: {win_rate:.0f}%

{COLOR_GREEN} 🎯 To follow real-time results:
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Results Channel", url=RESULTS_CHANNEL_URL, style=STYLE_GREEN)],
        [InlineKeyboardButton("Back", callback_data="main_menu", style=STYLE_BLUE)],
    ])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def show_referral_link(query, user_id):
    global BOT_USERNAME, REFERRAL_LINK_TEMPLATE
    bot_username = BOT_USERNAME
    if bot_username in ["your_bot_username", "", None]:
        try:
            me = await query.bot.get_me()
            bot_username = me.username
            BOT_USERNAME = bot_username
            REFERRAL_LINK_TEMPLATE = f"https://t.me/{bot_username}?start=ref_{{user_id}}"
        except Exception:
            bot_username = "your_bot_username"

    ref_link = REFERRAL_LINK_TEMPLATE.format(user_id=user_id)
    ref_count = get_referral_count(user_id)
    referrals = get_referrals_list(user_id)

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_GREEN} 🎁 Referral System
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_YELLOW} Your referral link:
{COLOR_GREEN} {ref_link}

{COLOR_BLUE} 📊 Your Statistics:
{COLOR_GREEN} 👥 Referrals count: {ref_count}
{COLOR_BLUE} 💎 Earned rewards: {ref_count * 5} points

{COLOR_PURPLE} 🎁 How does the referral system work?
{COLOR_GREEN} 1️⃣ Share your link with friends
{COLOR_GREEN} 2️⃣ When they join the bot, you get credited
{COLOR_GREEN} 3️⃣ Every 10 referrals = 1 free VIP month

{COLOR_YELLOW} 📋 Recent Referrals List:
"""
    if referrals:
        for ref in referrals[:5]:
            name = ref.get("first_name") or ref.get("username") or "User"
            joined = "✅ Joined" if ref.get("joined_channel") else "⏳ Pending"
            text += f"\n{COLOR_BLUE} • {name} - {joined}"
    else:
        text += f"\n{COLOR_RED} No referrals yet. Share your link to get started!"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={ref_link}&text=Join%20the%20Advanced%20Trading%20Signals%20Bot!", style=STYLE_GREEN)],
        [InlineKeyboardButton("Back", callback_data="main_menu", style=STYLE_BLUE)],
    ])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def show_my_account(query, user_id):
    user_data = get_user(user_id)
    if not user_data:
        await query.edit_message_text(
            f"{COLOR_RED} ⚠️ Your account was not found. Start over with /start",
            reply_markup=get_back_keyboard()
        )
        return

    join_date = user_data.get("join_date", "Unknown")[:10] if user_data.get("join_date") else "Unknown"
    plan = user_data.get("plan", "free")
    ref_count = user_data.get("referral_count", 0)
    is_premium = user_data.get("is_premium", 0)

    plan_emoji = "👑" if plan == "gold" else "📅" if plan == "monthly" else "📊" if plan == "weekly" else "🆓"
    plan_name = "Gold Plan" if plan == "gold" else "Monthly Plan" if plan == "monthly" else "Weekly Plan" if plan == "weekly" else "Free Plan"

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_PURPLE} 👤 My Account
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_GREEN} 🆔 User ID: {user_id}
{COLOR_BLUE} 👤 Name: {user_data.get('first_name', 'Unknown')}
{COLOR_GREEN} 📅 Join Date: {join_date}

{COLOR_YELLOW} 💎 Current Subscription:
{plan_emoji} {plan_name}
{COLOR_GREEN} Status: {'VIP Subscriber 👑' if is_premium else 'Regular User'}

{COLOR_BLUE} 📊 Your Statistics:
{COLOR_GREEN} 👥 Referrals: {ref_count}
{COLOR_BLUE} 💰 Rewards: {ref_count * 5} points

{COLOR_PURPLE} 🎯 Your Achievements:
{COLOR_GREEN} ✅ Bot member
{'✅ VIP subscriber' if is_premium else '⏳ Not subscribed yet'}
{COLOR_GREEN} ✅ {'Has referrals' if ref_count > 0 else 'No referrals yet'}
"""
    await query.edit_message_text(text, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)


async def show_support(query):
    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_GREEN} 🎧 Technical Support
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_YELLOW} We are here to help you anytime!

{COLOR_GREEN} 📞 Contact Methods:
{COLOR_BLUE} • Direct Support: via "Contact Support" button
{COLOR_GREEN} • Support Group: via official channel
{COLOR_BLUE} • FAQ: below

{COLOR_PURPLE} ❓ Frequently Asked Questions:

{COLOR_GREEN} Q: How do I get signals?
{COLOR_BLUE} A: Click the "Current Signals" button in the main menu

{COLOR_GREEN} Q: How do I subscribe to a paid plan?
{COLOR_BLUE} A: Click "Subscription Plans" then choose a plan

{COLOR_GREEN} Q: How do I earn from referrals?
{COLOR_BLUE} A: Share your referral link, every 10 referrals = 1 free VIP month

{COLOR_RED} 🚨 For urgent incidents only:
Contact support via the button below
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Contact Support", url=SUPPORT_URL, style=STYLE_GREEN)],
        [InlineKeyboardButton("📢 Official Channel", url=JOIN_CHANNEL_URL, style=STYLE_BLUE)],
        [InlineKeyboardButton("Back", callback_data="main_menu", style=STYLE_RED)],
    ])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


# ============================================================
# 5) ADMIN FUNCTIONS
# ============================================================

async def admin_new_signal(query, context):
    if not is_admin(query.from_user.id):
        await query.edit_message_text(
            f"{COLOR_RED} ⛔ Access Denied - Admins only",
            reply_markup=get_back_keyboard()
        )
        return ConversationHandler.END

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_GREEN} 📝 Create New Signal
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_YELLOW} Send the signal in the following format:
{COLOR_GREEN} Currency | Direction | Entry Price | Expiry

{COLOR_BLUE} Example:
{COLOR_GREEN} EUR/USD | CALL | 1.0856 | M1

{COLOR_RED} ⚠️ Send /cancel to cancel
"""
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return WAITING_SIGNAL_INPUT


async def receive_signal_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    text = update.message.text
    parts = [p.strip() for p in text.split("|")]
    if len(parts) != 4:
        await update.message.reply_text(
            f"{COLOR_RED} ⚠️ Invalid format! Use:\nCurrency | Direction | Price | Expiry"
        )
        return WAITING_SIGNAL_INPUT

    currency, direction, entry_price, expiry = parts
    try:
        price = float(entry_price)
    except ValueError:
        await update.message.reply_text(f"{COLOR_RED} ⚠️ Price must be a number")
        return WAITING_SIGNAL_INPUT

    signal_id = add_signal(currency, direction, price, expiry)
    context.user_data["pending_signal"] = {
        "id": signal_id,
        "currency": currency,
        "direction": direction,
        "price": price,
        "expiry": expiry,
    }

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_GREEN} ✅ Signal Ready
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_GREEN} 📊 Currency: {currency}
{COLOR_BLUE} 📈 Direction: {direction}
{COLOR_GREEN} 💰 Entry: {price}
{COLOR_BLUE} ⏰ Expiry: {expiry}

{COLOR_YELLOW} Do you want to send it to the signals channel?
"""
    await update.message.reply_text(
        text, reply_markup=get_admin_confirm_keyboard(), parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END


async def admin_confirm_send(query, context):
    if not is_admin(query.from_user.id):
        return

    signal = context.user_data.get("pending_signal")
    if not signal:
        await query.edit_message_text(
            f"{COLOR_RED} ⚠️ No pending signal",
            reply_markup=get_back_keyboard()
        )
        return

    signal_text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_GREEN} 📊 New Signal from the Bot
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_GREEN} 📈 Currency: {signal['currency']}
{COLOR_YELLOW} 📉 Direction: {signal['direction']}
{COLOR_GREEN} 💰 Entry Price: {signal['price']}
{COLOR_BLUE} ⏰ Expiry: {signal['expiry']}

{COLOR_PURPLE} 🕐 Signal Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{COLOR_RED} ⚠️ Trade responsibly - Signals are advisory only
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
"""
    try:
        await context.bot.send_message(
            chat_id=SIGNALS_CHANNEL_ID,
            text=signal_text,
            parse_mode=ParseMode.HTML
        )
        success_msg = f"{COLOR_GREEN} ✅ Signal sent to channel successfully!"
    except Exception as e:
        success_msg = f"{COLOR_RED} ⚠️ Send failed: {str(e)}"

    context.user_data.pop("pending_signal", None)
    await query.edit_message_text(
        f"{success_msg}\n\n{COLOR_BLUE} Back to control panel:",
        reply_markup=get_control_keyboard(is_admin=True),
        parse_mode=ParseMode.HTML
    )


async def admin_broadcast(query, context):
    if not is_admin(query.from_user.id):
        return

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_PURPLE} 📢 Broadcast Message to All Users
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_YELLOW} Send the message you want to broadcast:
{COLOR_RED} ⚠️ Send /cancel to cancel

{COLOR_GREEN} Total Users: {get_all_users_count()}
"""
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return WAITING_BROADCAST


async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    message = update.message.text
    users = get_all_users()
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(
        f"{COLOR_BLUE} 📤 Sending... (0/{len(users)})"
    )

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=f"{COLOR_BLUE} 📢 Message from Admin:\n\n{message}",
                parse_mode=ParseMode.HTML
            )
            sent += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"{COLOR_GREEN} ✅ Broadcast completed!\n\n"
        f"{COLOR_GREEN} 📤 Sent: {sent}\n"
        f"{COLOR_RED} ❌ Failed: {failed}",
        reply_markup=get_control_keyboard(is_admin=True),
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END


async def admin_stats(query):
    if not is_admin(query.from_user.id):
        return

    users_count = get_all_users_count()
    signals_stats = get_signals_stats()
    users = get_all_users()

    premium_count = sum(1 for u in users if u.get("plan") != "free")
    total_referrals = sum(u.get("referral_count", 0) for u in users)
    wins = signals_stats.get("win", 0)
    losses = signals_stats.get("loss", 0)
    total_signals = wins + losses
    win_rate = (wins / total_signals * 100) if total_signals > 0 else 0

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_PURPLE} 📊 Bot Statistics
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_YELLOW} 👥 Users:
{COLOR_GREEN} • Total Users: {users_count}
{COLOR_BLUE} • VIP Subscribers: {premium_count}
{COLOR_GREEN} • Total Referrals: {total_referrals}

{COLOR_YELLOW} 📈 Signals:
{COLOR_GREEN} • Winning signals: {wins}
{COLOR_RED} • Losing signals: {losses}
{COLOR_BLUE} • Win rate: {win_rate:.1f}%

{COLOR_YELLOW} 📅 Last Updates:
{COLOR_GREEN} • Last update date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    await query.edit_message_text(
        text, reply_markup=get_control_keyboard(is_admin=True), parse_mode=ParseMode.HTML
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("admin_creating_signal", None)
    context.user_data.pop("admin_broadcasting", None)
    context.user_data.pop("pending_signal", None)
    await update.message.reply_text(
        f"{COLOR_RED} ❌ Operation cancelled",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def track_channel_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track users joining the channel (for referral system)."""
    result = update.chat_member
    if result.new_chat_member.status in ['member', 'administrator']:
        user_id = result.from_user.id
        update_channel_join(user_id, joined=True)
        logging.info(f"User {user_id} joined the channel")


# ============================================================
# 6) MAIN ENTRY POINT
# ============================================================

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def post_init(application):
    """Called after bot initialization - prints bot info & auto-updates username."""
    me = await application.bot.get_me()
    logger.info("=" * 50)
    logger.info(f"🤖 Bot Info:")
    logger.info(f"   📛 Name: {me.first_name}")
    logger.info(f"   🔗 Username: @{me.username}")
    logger.info(f"   🆔 ID: {me.id}")

    global BOT_USERNAME, REFERRAL_LINK_TEMPLATE
    if BOT_USERNAME in ["your_bot_username", "", None]:
        BOT_USERNAME = me.username
        REFERRAL_LINK_TEMPLATE = f"https://t.me/{me.username}?start=ref_{{user_id}}"
        logger.info(f"   ✅ Referral link auto-updated: {REFERRAL_LINK_TEMPLATE}")
    logger.info("=" * 50)


def main():
    """Main entry point."""
    if not validate_config():
        logger.error("❌ Configuration incomplete! Edit BOT_TOKEN in this file.")
        sys.exit(1)

    logger.info("📊 Initializing database...")
    init_db()
    logger.info("✅ Database initialized successfully")

    logger.info("🤖 Starting the bot...")
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("cancel", cancel))

    # Signal creation conversation
    signal_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_new_signal, pattern="^admin_new_signal$")],
        states={
            WAITING_SIGNAL_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_signal_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(signal_conversation)

    # Broadcast conversation
    broadcast_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast, pattern="^admin_broadcast$")],
        states={
            WAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_broadcast)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(broadcast_conversation)

    # Main button handler
    application.add_handler(CallbackQueryHandler(button_handler))

    # Channel join tracking
    application.add_handler(ChatMemberHandler(track_channel_join, ChatMemberHandler.CHAT_MEMBER))

    logger.info("=" * 50)
    logger.info("🚀 Advanced Trading Signals Bot is running!")
    logger.info("=" * 50)
    logger.info("📋 Active Features:")
    logger.info("   ✅ Main menu with 14 buttons (mixed 2-1-2-1-2 layout)")
    logger.info("   ✅ Colored buttons (🔵🔴🟢)")
    logger.info("   ✅ Complete referral system")
    logger.info("   ✅ Admin control panel")
    logger.info("   ✅ Signal broadcasting to channel")
    logger.info("   ✅ Channel member tracking")
    logger.info("=" * 50)
    logger.info("⏹️  Press Ctrl+C to stop the bot")
    logger.info("=" * 50)

    application.run_polling(allowed_updates=["message", "callback_query", "chat_member"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        sys.exit(1)
