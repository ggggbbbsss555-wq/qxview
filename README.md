# 🤖 Advanced Telegram Trading Signals Bot

A professional Telegram bot built with `python-telegram-bot v20.7` that provides trading signals, a complete referral system, and an admin control panel.

## ✨ Features

### 📋 Main Menu (14 buttons in a mixed 2-1-2-1-2-1-2-1-2 layout)

| Row | Layout | Button 1 | Button 2 |
|-----|--------|----------|----------|
| 1 | 2 side-by-side | 🔵 Join Channel | 🔴 Live Chart |
| 2 | 1 full-width | 🟢 Quotex Hub | — |
| 3 | 2 side-by-side | 🔵 Subscription Plans | 🟢 Current Signals |
| 4 | 1 full-width | 🔴 Time Schedule | — |
| 5 | 2 side-by-side | 🔵 Free Bots | 🟢 Bot Control |
| 6 | 1 full-width | 🔴 Top Payout Currencies | — |
| 7 | 2 side-by-side | 🔵 Future Signals | 🔴 Future Signals Results |
| 8 | 1 full-width | 🟢 Referral Link | — |
| 9 | 2 side-by-side | 🔵 My Account | 🔴 Support |

### 🎨 Button Coloring
Color emulation using colored emoji prefixes (Telegram API does not support native button colors):
- 🔵 Blue — Information & Links
- 🔴 Red — Alerts & Important Actions
- 🟢 Green — Confirmation & Positive Features
- 🟡 Yellow — Special Features
- 🟣 Purple — VIP & Admin Features

### 📈 Full Features
- ✅ Professional English welcome message with feature overview
- ✅ Complete referral system with full tracking
- ✅ Admin control panel (create signals, broadcast messages, statistics)
- ✅ Channel join tracking (ChatMemberHandler)
- ✅ Local SQLite database (no external server required)
- ✅ Signal broadcasting to a specific channel
- ✅ Realistic demo data for preview

## 🚀 Installation & Setup

### 1️⃣ Requirements
- Python 3.9 or higher
- pip (Python package manager)

### 2️⃣ Installation
```bash
cd telegram-bot
pip install -r requirements.txt
```

### 3️⃣ Configuration
Edit `config.py` and update the following values:

```python
# Bot token from @BotFather
BOT_TOKEN = "your_bot_token_here"

# Bot username without @
BOT_USERNAME = "your_bot_username"

# Channel URLs
JOIN_CHANNEL_URL = "https://t.me/your_channel"
JOIN_CHANNEL_USERNAME = "@your_channel"
SIGNALS_CHANNEL_ID = "@your_signals_channel"
RESULTS_CHANNEL_URL = "https://t.me/your_results_channel"
SUPPORT_URL = "https://t.me/your_support"
FREE_BOTS_URL = "https://t.me/your_free_bots"

# Admin ID (get it from @userinfobot)
ADMIN_IDS = [123456789]
```

### 4️⃣ Run the Bot
```bash
python main.py
```

## 📁 Project Structure

```
telegram-bot/
├── main.py           # Main entry point
├── config.py         # Bot configuration (token, URLs, plans)
├── database.py       # SQLite database for referrals
├── handlers.py       # Button handlers and logic
├── keyboards.py      # Keyboard layouts (2-1-2-1-2 mixed pattern)
├── requirements.txt  # Dependencies
├── README.md         # This file
└── bot_database.db   # Database (auto-created)
```

## 🎛️ Admin Control Panel Features

When an admin clicks "Bot Control", they get access to:

1. **📝 New Signal**: Create a signal in format `Currency | Direction | Price | Expiry`
2. **📢 Broadcast**: Send a message to all registered users
3. **📊 Bot Statistics**: View comprehensive statistics

## 🎁 Referral System

### How it works:
1. Each user gets a unique referral link
2. When a new user joins via the link, the referrer gets credited
3. Every 10 referrals = 1 free VIP month

### Referral link format:
```
https://t.me/your_bot?start=ref_USER_ID
```

## 📌 Important Notes

### Button Coloring
> ⚠️ Telegram API does not natively support button colors. The coloring here is done via colored emoji (🔵🔴🟢) prefixed to each button's text — the only officially available method.

### Bot Permissions Required
- ✅ Send messages
- ✅ Manage inline keyboards
- ✅ Track channel member status

### Adding the Bot as Channel Admin
To send signals automatically, you must:
1. Add the bot as an admin in the signals channel
2. Grant it "Post Messages" permission

## 🔧 Troubleshooting

### Error: `BOT_TOKEN is not set`
- Make sure you updated `BOT_TOKEN` in `config.py`

### Error: `Chat not found` when sending a signal
- Make sure the bot is an admin in the channel
- Make sure `@channel_username` is correct

### Error: `Forbidden: bot is not a member`
- Add the bot to the channel and grant posting permissions

## 📞 Support
For help or bug reports, contact us via the Support section in the bot.

---

**Built with ❤️ and python-telegram-bot v20.7**
