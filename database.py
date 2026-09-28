"""
وحدة قاعدة البيانات لنظام الإحالات والمستخدمين
تستخدم SQLite لتخزين البيانات محلياً بدون الحاجة لخادم خارجي
"""

import sqlite3
import os
import time
from datetime import datetime

# مسار قاعدة البيانات
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_database.db")


def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجداول إذا لم تكن موجودة"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # جدول المستخدمين
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

    # جدول الإحالات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        date TEXT,
        joined_channel INTEGER DEFAULT 0
    )
    """)

    # جدول الإشارات
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

    # جدول الاشتراكات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER,
        plan TEXT,
        start_date TEXT,
        end_date TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    conn.commit()
    conn.close()


def add_user(user_id: int, username: str = None, first_name: str = None,
             referrer_id: int = None) -> bool:
    """
    إضافة مستخدم جديد إلى قاعدة البيانات
    يعيد True إذا تمت الإضافة، False إذا كان موجوداً مسبقاً
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # التحقق إذا كان المستخدم موجوداً
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        conn.close()
        return False

    # إضافة المستخدم
    cursor.execute("""
    INSERT INTO users (user_id, username, first_name, join_date, referrer_id, referral_count, is_premium, plan)
    VALUES (?, ?, ?, ?, ?, 0, 0, 'free')
    """, (user_id, username, first_name, datetime.now().isoformat(), referrer_id))

    # إذا كان هناك مُحيل، نضيف الإحالة ونحدث عداده
    if referrer_id and referrer_id != user_id:
        # التحقق من عدم تكرار الإحالة
        cursor.execute(
            "SELECT id FROM referrals WHERE referrer_id = ? AND referred_id = ?",
            (referrer_id, user_id)
        )
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO referrals (referrer_id, referred_id, date, joined_channel)
            VALUES (?, ?, ?, 0)
            """, (referrer_id, user_id, datetime.now().isoformat()))

            # زيادة عداد الإحالات للمُحيل
            cursor.execute("""
            UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?
            """, (referrer_id,))

    conn.commit()
    conn.close()
    return True


def get_user(user_id: int) -> dict:
    """الحصول على بيانات المستخدم"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_referral_count(user_id: int) -> int:
    """الحصول على عدد إحالات المستخدم"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT referral_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def get_referrals_list(user_id: int) -> list:
    """الحصول على قائمة المستخدمين الذين أحالهم المستخدم"""
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


def update_channel_join(user_id: int, joined: bool = True):
    """تحديث حالة انضمام المستخدم للقناة"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE referrals SET joined_channel = ? WHERE referred_id = ?",
        (1 if joined else 0, user_id)
    )
    conn.commit()
    conn.close()


def is_admin(user_id: int) -> bool:
    """التحقق من كون المستخدم مشرفاً"""
    from config import ADMIN_IDS
    return user_id in ADMIN_IDS


def add_signal(currency: str, direction: str, entry_price: float, expiry: str) -> int:
    """إضافة إشارة جديدة إلى قاعدة البيانات"""
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


def update_signal_status(signal_id: int, status: str):
    """تحديث حالة الإشارة (win/loss/pending)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE signals SET status = ? WHERE id = ?",
        (status, signal_id)
    )
    conn.commit()
    conn.close()


def get_signals_stats() -> dict:
    """الحصول على إحصائيات الإشارات"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) FROM signals GROUP BY status")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


def get_all_users_count() -> int:
    """الحصول على العدد الإجمالي للمستخدمين"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_all_users() -> list:
    """الحصول على قائمة كل المستخدمين"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, join_date, referral_count, plan FROM users ORDER BY join_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
