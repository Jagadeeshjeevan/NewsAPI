from __future__ import annotations
from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ── Enums ──────────────────────────────────────────────────────────────────

class UserType(str, Enum):
    GUEST = "guest"
    REGISTERED = "registered"

class DeviceType(str, Enum):
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"

class NewsSource(str, Enum):
    RSS = "rss"
    MANUAL = "manual"
    AI = "ai"

class NewsStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ReactionType(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"

class SubType(str, Enum):
    LOCATION = "location"
    CATEGORY = "category"
    BREAKING = "breaking"
    KEYWORD = "keyword"

class TimeWindow(str, Enum):
    LATEST = "latest"
    TODAY = "today"
    YESTERDAY = "yesterday"
    OLDER = "older"


# ── Auth ───────────────────────────────────────────────────────────────────

class AdminLoginRequest(BaseModel):
    email: str
    password: str

class GuestLoginRequest(BaseModel):
    device_id: str
    device_type: DeviceType = DeviceType.ANDROID
    device_name: Optional[str] = None

class GoogleLoginRequest(BaseModel):
    id_token: str
    device_id: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    user_type: str
    is_new: bool = False

class GoogleTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    user_type: str
    is_new_user: bool
    name: Optional[str] = None
    profile_pic: Optional[str] = None

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Users ──────────────────────────────────────────────────────────────────

class FiltersOut(BaseModel):
    categories: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    locations: Optional[List[str]] = []
    default_window: str = "today"

class UserOut(BaseModel):
    id: int
    user_type: str
    name: Optional[str] = None
    email: Optional[str] = None
    profile_pic: Optional[str] = None
    preferred_lang: str
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    is_admin: bool
    filters: Optional[FiltersOut] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    preferred_lang: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class OnboardingRequest(BaseModel):
    preferred_lang: str
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    categories: Optional[List[str]] = []

class DeviceTokenRequest(BaseModel):
    fcm_token: str
    device_type: DeviceType = DeviceType.ANDROID
    device_name: Optional[str] = None

class DeviceTokenSettingsRequest(BaseModel):
    notifications_enabled: Optional[bool] = None
    notify_breaking: Optional[bool] = None
    notify_location: Optional[bool] = None
    notify_category: Optional[bool] = None
    notify_digest: Optional[bool] = None
    notify_keyword: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_start: Optional[str] = None
    quiet_end: Optional[str] = None

class FiltersUpdateRequest(BaseModel):
    categories: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    default_window: Optional[str] = None


# ── News ───────────────────────────────────────────────────────────────────

class NewsSubmitRequest(BaseModel):
    title: str
    content: str
    category_code: str
    image_url: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None

class NewsCard(BaseModel):
    id: int
    language_code: str
    title: str
    summary: Optional[str] = None
    audio_url: Optional[str] = None
    audio_duration: Optional[int] = None
    image_url: Optional[str] = None
    category_code: Optional[str] = None
    category_name: Optional[str] = None
    category_icon: Optional[str] = None
    category_color: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    is_breaking: bool = False
    view_count: int = 0
    like_count: int = 0
    dislike_count: int = 0
    published_at: datetime

    class Config:
        from_attributes = True

class NewsDetail(NewsCard):
    raw_id: int
    content: Optional[str] = None
    audio_size_bytes: Optional[int] = None
    audio_play_count: int = 0
    share_count: int = 0
    language_name: Optional[str] = None
    language_native: Optional[str] = None
    district: Optional[str] = None
    available_languages: List[str] = []

class FeedResponse(BaseModel):
    window: str
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    next_cursor: Optional[int] = None
    has_more: bool = False
    count: int
    data: List[NewsCard]

class PaginatedNewsResponse(BaseModel):
    total: int
    page: int
    data: List[Any]


# ── Admin ──────────────────────────────────────────────────────────────────

class AdminQueueItem(BaseModel):
    id: int
    source: str
    source_url: Optional[str] = None
    original_text: str
    ai_summary: Optional[str] = None
    ai_score: Optional[float] = None
    category_code: Optional[str] = None
    category_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_duplicate: bool = False
    submitted_by_name: Optional[str] = None
    created_at: datetime

class ApproveRequest(BaseModel):
    is_breaking: bool = False
    use_ai_rewrite: bool = True
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None

class RejectRequest(BaseModel):
    reason: Optional[str] = None
    state: Optional[str] = None

class AdminEditRequest(BaseModel):
    title: Optional[str] = None
    original_text: Optional[str] = None
    category_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None

class BreakingFlagRequest(BaseModel):
    is_breaking: bool

class PublishedEditRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    category_code: Optional[str] = None
    is_breaking: Optional[bool] = None

class AdminPushRequest(BaseModel):
    title: str
    body: str
    language_code: str
    state: Optional[str] = None
    city: Optional[str] = None
    category_code: Optional[str] = None
    news_id: Optional[int] = None


# ── Reactions / Bookmarks ──────────────────────────────────────────────────

class ReactRequest(BaseModel):
    reaction: ReactionType

class ReactResponse(BaseModel):
    action: str
    my_reaction: str
    like_count: int
    dislike_count: int

class ReactionCountResponse(BaseModel):
    like_count: int
    dislike_count: int
    my_reaction: Optional[str] = None


# ── Subscriptions ──────────────────────────────────────────────────────────

class SubscriptionCreate(BaseModel):
    type: SubType
    language: str
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    keyword: Optional[str] = None

class SubscriptionPatch(BaseModel):
    is_active: bool


# ── Languages / Categories ─────────────────────────────────────────────────

class LanguageOut(BaseModel):
    id: int
    code: str
    name_english: str
    name_native: str
    flag_emoji: Optional[str] = None

    class Config:
        from_attributes = True

class CategoryOut(BaseModel):
    id: int
    code: str
    name_english: str
    icon_emoji: Optional[str] = None
    color_hex: Optional[str] = None

    class Config:
        from_attributes = True

class LanguageCreate(BaseModel):
    code: str
    name_english: str
    name_native: str
    flag_emoji: Optional[str] = None
    tts_voice: Optional[str] = None
    sort_order: int = 0

class LanguagePatch(BaseModel):
    name_english: Optional[str] = None
    tts_voice: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class CategoryCreate(BaseModel):
    code: str
    name_english: str
    icon_emoji: Optional[str] = None
    color_hex: Optional[str] = None
    sort_order: int = 0

class CategoryPatch(BaseModel):
    name_english: Optional[str] = None
    icon_emoji: Optional[str] = None
    color_hex: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
