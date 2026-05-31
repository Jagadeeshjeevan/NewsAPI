from sqlalchemy import Column, BigInteger, Integer, String, Text, Enum, DateTime, Float, Numeric, JSON, Time
from sqlalchemy.dialects.mysql import LONGTEXT, TINYINT
from sqlalchemy.sql import func
from app.core.database import Base


class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name_english = Column(String(50), nullable=False)
    name_native = Column(String(50), nullable=False)
    flag_emoji = Column(String(10))
    tts_voice = Column(String(100))
    is_active = Column(TINYINT, default=1)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name_english = Column(String(100), nullable=False)
    icon_emoji = Column(String(10))
    icon_url = Column(String(500))
    color_hex = Column(String(7))
    is_active = Column(TINYINT, default=1)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    user_type = Column(Enum("guest", "registered"), default="guest")
    device_id = Column(String(200), unique=True)
    google_id = Column(String(100), unique=True)
    email = Column(String(200), unique=True)
    name = Column(String(100))
    profile_pic   = Column(String(500))
    password_hash = Column(String(255))
    is_admin = Column(TINYINT, default=0)
    is_active = Column(TINYINT, default=1)
    preferred_lang = Column(String(10), default="te")
    state = Column(String(100))
    district = Column(String(100))
    city = Column(String(100))
    lat = Column(Numeric(10, 8))
    lng = Column(Numeric(11, 8))
    anchor_time = Column(DateTime)
    last_seen = Column(DateTime)
    last_login = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(TINYINT, default=0)
    created_at = Column(DateTime, server_default=func.now())


class UserDeviceToken(Base):
    __tablename__ = "user_device_tokens"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    fcm_token = Column(Text, nullable=False)
    device_type = Column(Enum("android", "ios", "web"), default="android")
    device_name = Column(String(100))
    notifications_enabled = Column(TINYINT, default=1)
    notify_breaking = Column(TINYINT, default=1)
    notify_location = Column(TINYINT, default=1)
    notify_category = Column(TINYINT, default=1)
    notify_digest = Column(TINYINT, default=1)
    notify_keyword = Column(TINYINT, default=1)
    quiet_hours_enabled = Column(TINYINT, default=0)
    quiet_start = Column(Time, default="22:00:00")
    quiet_end = Column(Time, default="07:00:00")
    last_active = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UserFilter(Base):
    __tablename__ = "user_filters"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    categories = Column(JSON)
    languages = Column(JSON)
    locations = Column(JSON)
    default_window = Column(String(20), default="today")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NewsRaw(Base):
    __tablename__ = "news_raw"

    id = Column(BigInteger, primary_key=True)
    source = Column(Enum("rss", "manual", "ai"), nullable=False)
    source_url = Column(String(500), unique=True)
    original_text = Column(LONGTEXT, nullable=False)
    original_lang = Column(String(10), default="en")
    image_url     = Column(String(500))
    category_id   = Column(Integer)
    category_code = Column(String(50))
    state         = Column(String(100))
    district      = Column(String(100))
    city          = Column(String(100))
    status        = Column(Enum("pending", "approved", "rejected", "success"), default="pending")
    ai_rewritten = Column(LONGTEXT)
    ai_summary = Column(Text)
    ai_score = Column(Float)
    is_duplicate = Column(TINYINT, default=0)
    submitted_by = Column(BigInteger)
    reviewed_by = Column(BigInteger)
    reviewed_at = Column(DateTime)
    rejection_reason = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class News(Base):
    __tablename__ = "news"

    id = Column(BigInteger, primary_key=True)
    raw_id = Column(BigInteger, nullable=False)
    language_id = Column(Integer, nullable=False)
    language_code = Column(String(10), nullable=False)
    title = Column(Text, nullable=False)
    summary = Column(Text)
    content = Column(LONGTEXT)
    audio_url = Column(String(500))
    audio_duration = Column(Integer)
    audio_size_bytes = Column(BigInteger)
    image_url = Column(String(500))
    category_id = Column(Integer)
    category_code = Column(String(50))
    tags = Column(JSON)
    national = Column(TINYINT, default=0)
    state = Column(String(100))
    district = Column(String(100))
    city = Column(String(100))
    lat = Column(Numeric(10, 8))
    lng = Column(Numeric(11, 8))
    radius_km = Column(Integer, default=50)
    is_breaking = Column(TINYINT, default=0)
    view_count = Column(Integer, default=0)
    audio_play_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    dislike_count = Column(Integer, default=0)
    published_at = Column(DateTime, server_default=func.now())


class NewsReaction(Base):
    __tablename__ = "news_reactions"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    news_id = Column(BigInteger, nullable=False)
    reaction = Column(Enum("like", "dislike"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NewsComment(Base):
    __tablename__ = "news_comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    news_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False)
    user_name = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    type = Column(Enum("location", "category", "breaking", "keyword"), nullable=False)
    language = Column(String(10), nullable=False)
    state = Column(String(100))
    district = Column(String(100))
    city = Column(String(100))
    category = Column(String(50))
    keyword = Column(String(100))
    is_active = Column(TINYINT, default=1)
    created_at = Column(DateTime, server_default=func.now())


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    news_id = Column(BigInteger, nullable=False)
    saved_at = Column(DateTime, server_default=func.now())


class UserReadHistory(Base):
    __tablename__ = "user_read_history"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    news_id = Column(BigInteger, nullable=False)
    read_at = Column(DateTime, server_default=func.now())
