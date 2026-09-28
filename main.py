"""
الملف الرئيسي لتشغيل بوت تلجرام
بوت الإشارات المتقدم - python-telegram-bot v20.7

طريقة التشغيل:
1. تم وضع توكن البوت في ملف config.py
2. قم بتثبيت المتطلبات: pip install -r requirements.txt
3. شغل البوت: python main.py
"""

import logging
import sys
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ChatMemberHandler,
    filters,
)

# استيراد الإعدادات
from config import BOT_TOKEN, validate_config
from database import init_db
from handlers import (
    start,
    button_handler,
    admin_new_signal,
    receive_signal_input,
    admin_broadcast,
    receive_broadcast,
    cancel,
    track_channel_join,
    WAITING_SIGNAL_INPUT,
    WAITING_BROADCAST,
)

# إعداد التسجيل (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# تقليل سجلات مكتبة httpx
logging.getLogger("httpx").setLevel(logging.WARNING)


async def post_init(application):
    """يُستدعى بعد تهيئة البوت - لطباعة معلومات البوت"""
    me = await application.bot.get_me()
    logger.info("=" * 50)
    logger.info(f"🤖 معلومات البوت:")
    logger.info(f"   📛 الاسم: {me.first_name}")
    logger.info(f"   🔗 المعرف: @{me.username}")
    logger.info(f"   🆔 ID: {me.id}")

    # تحديث BOT_USERNAME ديناميكياً في حالة كان مكان الروابط
    import config
    if config.BOT_USERNAME in ["your_bot_username", ""]:
        config.BOT_USERNAME = me.username
        # تحديث رابط الإحالة
        config.REFERRAL_LINK_TEMPLATE = f"https://t.me/{me.username}?start=ref_{{user_id}}"
        logger.info(f"   ✅ تم تحديث رابط الإحالة تلقائياً: {config.REFERRAL_LINK_TEMPLATE}")
    logger.info("=" * 50)


def main():
    """النقطة الرئيسية لتشغيل البوت"""
    # التحقق من الإعدادات
    if not validate_config():
        logger.error("❌ الإعدادات غير مكتملة! عدّل ملف config.py أولاً")
        sys.exit(1)

    # تهيئة قاعدة البيانات
    logger.info("📊 جاري تهيئة قاعدة البيانات...")
    init_db()
    logger.info("✅ تمت تهيئة قاعدة البيانات بنجاح")

    # إنشاء التطبيق
    logger.info("🤖 جاري تشغيل البوت...")
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ======== تسجيل المعالجات (Handlers) ========

    # معالج أمر /start
    application.add_handler(CommandHandler("start", start))

    # معالج أمر /help
    application.add_handler(CommandHandler("help", start))

    # معالج أمر الإلغاء
    application.add_handler(CommandHandler("cancel", cancel))

    # معالج المحادثة لإنشاء الإشارات (للمشرفين)
    signal_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_new_signal, pattern="^admin_new_signal$")],
        states={
            WAITING_SIGNAL_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_signal_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(signal_conversation)

    # معالج المحادثة للبث
    broadcast_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast, pattern="^admin_broadcast$")],
        states={
            WAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_broadcast)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(broadcast_conversation)

    # المعالج الرئيسي لكل الأزرار
    application.add_handler(CallbackQueryHandler(button_handler))

    # معالج تتبع انضمام الأعضاء للقناة (للإحالات)
    application.add_handler(ChatMemberHandler(track_channel_join, ChatMemberHandler.CHAT_MEMBER))

    # رسالة بدء التشغيل
    logger.info("=" * 50)
    logger.info("🚀 بوت الإشارات المتقدم يعمل الآن!")
    logger.info("=" * 50)
    logger.info("📋 المميزات النشطة:")
    logger.info("   ✅ قائمة رئيسية مع 14 زر")
    logger.info("   ✅ تلوين الأزرار (🔵🔴🟢)")
    logger.info("   ✅ نظام إحالات متكامل")
    logger.info("   ✅ لوحة تحكم المشرف")
    logger.info("   ✅ بث الإشارات للقناة")
    logger.info("   ✅ تتبع انضمام الأعضاء")
    logger.info("=" * 50)
    logger.info("⏹️  اضغط Ctrl+C لإيقاف البوت")
    logger.info("=" * 50)

    # تشغيل البوت
    application.run_polling(allowed_updates=["message", "callback_query", "chat_member"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n🛑 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        sys.exit(1)
