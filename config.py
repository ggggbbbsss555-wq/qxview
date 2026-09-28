"""
ملف الإعدادات الرئيسي للبوت
ضع هنا التوكن وروابط القنوات الخاصة بك
"""

# ============================================================
# إعدادات البوت الأساسية
# ============================================================

# توكن البوت من BotFather - تم وضع التوكن مباشرة
BOT_TOKEN = "8825955443:AAGk3WzJHfYvSHObwXNE1HRsy2PrEbzNnxc"

# معرف البوت (يُستخدم لرابط الإحالة) - استبدله بمعرف بوتك بدون @
BOT_USERNAME = "your_bot_username"

# ============================================================
# روابط القنوات والموارد
# ============================================================

# قناة الانضمام الإلزامية (يجب أن ينضم لها المستخدم لاستخدام البوت)
JOIN_CHANNEL_URL = "https://t.me/your_channel"
JOIN_CHANNEL_USERNAME = "@your_channel"

# رابط لايف شارت (Live Chart)
LIVE_CHART_URL = "https://www.tradingview.com/chart/"

# رابط منصة Quotex Hub
QUOTEX_HUB_URL = "https://quotex.io/"

# قناة الإشارات (التي تُرسل إليها الإشارات عند التحكم)
SIGNALS_CHANNEL_ID = "@your_signals_channel"

# قناة النتائج (نتائج الإشارات المستقبلية)
RESULTS_CHANNEL_URL = "https://t.me/your_results_channel"

# رابط الدعم الفني
SUPPORT_URL = "https://t.me/your_support"

# رابط مجموعة التجربة المجانية أو البوتات المجانية
FREE_BOTS_URL = "https://t.me/your_free_bots"

# ============================================================
# قائمة الاشتراكات والخطط
# ============================================================

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
# معرفات المشرفين (Admin IDs)
# ============================================================
# احصل على معرفك من خلال @userinfobot
# أضف معرفات المستخدمين المصرح لهم بالتحكم في البوت
ADMIN_IDS = [
    123456789,  # استبدل بمعرفك
]

# ============================================================
# إعدادات التلوين (محاكاة بالألوان)
# ============================================================
# إيموجي الألوان لتلوين الأزرار (محاكاة بصرية)
COLOR_BLUE = "🔵"
COLOR_RED = "🔴"
COLOR_GREEN = "🟢"
COLOR_YELLOW = "🟡"
COLOR_PURPLE = "🟣"

# ============================================================
# رابط الإحالة الافتراضي
# ============================================================
REFERRAL_LINK_TEMPLATE = f"https://t.me/{BOT_USERNAME}?start=ref_{{user_id}}"

# ============================================================
# التحقق من صحة الإعدادات
# ============================================================
def validate_config():
    """التحقق من أن الإعدادات الأساسية موجودة"""
    if not BOT_TOKEN or BOT_TOKEN == "ضع_توكن_البوت_هنا":
        print("⚠️  تنبيه: لم تقم بتعيين BOT_TOKEN بعد!")
        print("   احصل على التوكن من @BotFather وضع القيمة في ملف config.py")
        return False
    return True
