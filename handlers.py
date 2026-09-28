"""
Button handlers module for the Telegram bot
Contains handler functions for all main menu buttons (in English)
"""

import logging
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from config import (
    COLOR_BLUE, COLOR_RED, COLOR_GREEN, COLOR_YELLOW, COLOR_PURPLE,
    JOIN_CHANNEL_URL, JOIN_CHANNEL_USERNAME, LIVE_CHART_URL,
    QUOTEX_HUB_URL, RESULTS_CHANNEL_URL, SUPPORT_URL, FREE_BOTS_URL,
    SIGNALS_CHANNEL_ID, PLANS, REFERRAL_LINK_TEMPLATE, BOT_USERNAME
)
from keyboards import (
    get_main_menu_keyboard, get_back_keyboard, get_plans_keyboard,
    get_control_keyboard, get_admin_confirm_keyboard
)
import database as db

logger = logging.getLogger(__name__)

# Conversation states for admin
WAITING_SIGNAL_INPUT, WAITING_BROADCAST = range(2)

# Professional welcome message in English
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
    """Handle /start command - welcome message"""
    user = update.effective_user
    user_id = user.id

    # Check for referrer in the link
    referrer_id = None
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        if arg.startswith("ref_"):
            try:
                referrer_id = int(arg.replace("ref_", ""))
            except ValueError:
                referrer_id = None

    # Add user to database
    is_new = db.add_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        referrer_id=referrer_id
    )

    if is_new:
        logger.info(f"New user: {user_id} - @{user.username}")

    # Store user id in context
    context.user_data["user_id"] = user_id

    # Send welcome message
    welcome_text = WELCOME_MESSAGE
    if referrer_id:
        welcome_text += f"\n{COLOR_YELLOW} 👋 You were referred by a friend!\n"

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main handler for all buttons"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    context.user_data["user_id"] = user_id

    # Route to the appropriate handler
    if data == "main_menu":
        await show_main_menu(query)
    elif data == "plans":
        await show_plans(query)
    elif data.startswith("plan_"):
        await show_plan_details(query, data.replace("plan_", ""))
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
    else:
        await query.edit_message_text(
            "This feature is under development, stay tuned for updates! 🔧",
            reply_markup=get_back_keyboard()
        )


async def show_main_menu(query):
    """Show main menu"""
    await query.edit_message_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def show_plans(query):
    """Show subscription plans"""
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
        text,
        reply_markup=get_plans_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def show_plan_details(query, plan_key):
    """Show details of a specific plan"""
    plans_map = {
        "free": PLANS[0],
        "weekly": PLANS[1],
        "monthly": PLANS[2],
        "gold": PLANS[3],
    }
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
    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def show_current_signals(query):
    """Show current signals (demo data)"""
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
    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def show_time_list(query):
    """Show time schedule for sessions"""
    now = datetime.now()
    sessions = [
        ("Tokyo Session", now + timedelta(hours=2), "🇯🇵"),
        ("London Session", now + timedelta(hours=5), "🇬🇧"),
        ("New York Session", now + timedelta(hours=9), "🇺🇸"),
        ("Sydney Session", now + timedelta(hours=14), "🇦🇺"),
    ]

    sessions_text = "\n".join([
        f"{COLOR_BLUE} {flag} {name}\n"
        f"{COLOR_GREEN} ⏰ Starts: {time.strftime('%Y-%m-%d %H:%M')}"
        for name, time, flag in sessions
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
    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def show_free_bots(query):
    """Show free bots list"""
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
        [InlineKeyboardButton(f"{COLOR_GREEN} 🎁 Visit Free Bots", url=FREE_BOTS_URL)],
        [InlineKeyboardButton(f"{COLOR_BLUE} Back", callback_data="main_menu")],
    ])
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


async def show_control_bot(query, user_id):
    """Show control panel (admins only)"""
    if not db.is_admin(user_id):
        text = f"""
{COLOR_RED} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_RED} ⛔ Access Denied
{COLOR_RED} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_YELLOW} This feature is restricted to admins only.

{COLOR_BLUE} If you believe this is an error, please contact support.
"""
        await query.edit_message_text(
            text,
            reply_markup=get_back_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_PURPLE} 🎛️ Admin Control Panel
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_GREEN} Welcome Admin 👑

{COLOR_YELLOW} Quick Statistics:
{COLOR_BLUE} 👥 Users: {db.get_all_users_count()}
{COLOR_GREEN} 📊 Today's Signals: {len(db.get_signals_stats())}

{COLOR_GREEN} Select the desired action:
"""
    await query.edit_message_text(
        text,
        reply_markup=get_control_keyboard(is_admin=True),
        parse_mode=ParseMode.HTML
    )


async def show_top_payout(query):
    """Show top payout currencies (demo data)"""
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
    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def show_future_signals(query):
    """Show future signals"""
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
    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def show_future_results(query):
    """Show future signals results"""
    # Demo results data
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
        [InlineKeyboardButton(f"{COLOR_GREEN} 📊 Results Channel", url=RESULTS_CHANNEL_URL)],
        [InlineKeyboardButton(f"{COLOR_BLUE} Back", callback_data="main_menu")],
    ])
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


async def show_referral_link(query, user_id):
    """Show user's referral link"""
    # استخدام BOT_USERNAME الديناميكي من config
    import config
    bot_username = config.BOT_USERNAME
    if bot_username in ["your_bot_username", "", None]:
        # محاولة الحصول على المعرف من البوت
        try:
            me = await query.bot.get_me()
            bot_username = me.username
            # تحديث القيمة في config
            config.BOT_USERNAME = bot_username
            config.REFERRAL_LINK_TEMPLATE = f"https://t.me/{bot_username}?start=ref_{{user_id}}"
        except Exception:
            bot_username = "your_bot_username"

    ref_link = config.REFERRAL_LINK_TEMPLATE.format(user_id=user_id)
    ref_count = db.get_referral_count(user_id)
    referrals = db.get_referrals_list(user_id)

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
        [InlineKeyboardButton(f"{COLOR_GREEN} 📤 Share Link", url=f"https://t.me/share/url?url={ref_link}&text=Join%20the%20Advanced%20Trading%20Signals%20Bot!")],
        [InlineKeyboardButton(f"{COLOR_BLUE} Back", callback_data="main_menu")],
    ])
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


async def show_my_account(query, user_id):
    """Show user account information"""
    user_data = db.get_user(user_id)
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
    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def show_support(query):
    """Show support page"""
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
        [InlineKeyboardButton(f"{COLOR_GREEN} 📞 Contact Support", url=SUPPORT_URL)],
        [InlineKeyboardButton(f"{COLOR_BLUE} 📢 Official Channel", url=JOIN_CHANNEL_URL)],
        [InlineKeyboardButton(f"{COLOR_RED} Back", callback_data="main_menu")],
    ])
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


# ============================================================
# Admin functions
# ============================================================

async def admin_new_signal(query, context):
    """Start creating a new signal (admin only)"""
    if not db.is_admin(query.from_user.id):
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
    context.user_data["admin_creating_signal"] = True
    return WAITING_SIGNAL_INPUT


async def receive_signal_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive signal data from admin"""
    user_id = update.effective_user.id
    if not db.is_admin(user_id):
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

    # Save to database
    signal_id = db.add_signal(currency, direction, price, expiry)

    # Store in context for confirmation
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
        text,
        reply_markup=get_admin_confirm_keyboard(),
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END


async def admin_confirm_send(query, context):
    """Confirm sending signal to channel"""
    if not db.is_admin(query.from_user.id):
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
        # Send to the specified channel
        await context.bot.send_message(
            chat_id=SIGNALS_CHANNEL_ID,
            text=signal_text,
            parse_mode=ParseMode.HTML
        )
        success_msg = f"{COLOR_GREEN} ✅ Signal sent to channel successfully!"
    except Exception as e:
        logger.error(f"Failed to send signal: {e}")
        success_msg = f"{COLOR_RED} ⚠️ Send failed: {str(e)}"

    # Clear from context
    context.user_data.pop("pending_signal", None)

    await query.edit_message_text(
        f"{success_msg}\n\n{COLOR_BLUE} Back to control panel:",
        reply_markup=get_control_keyboard(is_admin=True),
        parse_mode=ParseMode.HTML
    )


async def admin_broadcast(query, context):
    """Start broadcast to all users"""
    if not db.is_admin(query.from_user.id):
        return

    text = f"""
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━
{COLOR_PURPLE} 📢 Broadcast Message to All Users
{COLOR_BLUE} ━━━━━━━━━━━━━━━━━━━━━

{COLOR_YELLOW} Send the message you want to broadcast:
{COLOR_RED} ⚠️ Send /cancel to cancel

{COLOR_GREEN} Total Users: {db.get_all_users_count()}
"""
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    context.user_data["admin_broadcasting"] = True
    return WAITING_BROADCAST


async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive broadcast message and send to all users"""
    if not db.is_admin(update.effective_user.id):
        return ConversationHandler.END

    message = update.message.text
    users = db.get_all_users()
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
        except Exception as e:
            logger.warning(f"Failed to send to {user['user_id']}: {e}")
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
    """Show bot statistics for admin"""
    if not db.is_admin(query.from_user.id):
        return

    users_count = db.get_all_users_count()
    signals_stats = db.get_signals_stats()
    users = db.get_all_users()

    # Additional statistics
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
        text,
        reply_markup=get_control_keyboard(is_admin=True),
        parse_mode=ParseMode.HTML
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current operation"""
    context.user_data.pop("admin_creating_signal", None)
    context.user_data.pop("admin_broadcasting", None)
    context.user_data.pop("pending_signal", None)

    await update.message.reply_text(
        f"{COLOR_RED} ❌ Operation cancelled",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def track_channel_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track users joining the channel (for referral system)"""
    result = update.chat_member
    if result.new_chat_member.status in ['member', 'administrator']:
        user_id = result.from_user.id
        db.update_channel_join(user_id, joined=True)
        logger.info(f"User {user_id} joined the channel")
