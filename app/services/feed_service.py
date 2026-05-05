from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import News, Category, Language, User
from app.core import redis as cache_store

WINDOW_TTL = {"latest": 30, "today": 120, "yesterday": 600, "older": 600}


def _get_window_bounds(user: User, window: str) -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    anchor = user.anchor_time or now
    bounds = {
        "latest":    (now - timedelta(hours=2), now),
        "today":     (anchor - timedelta(hours=24), anchor),
        "yesterday": (anchor - timedelta(hours=48), anchor - timedelta(hours=24)),
        "older":     (datetime(2020, 1, 1), anchor - timedelta(hours=48)),
    }
    return bounds[window]


def get_feed(db: Session, user: User, language: str, window: str, last_id: int | None,
             after_id: int | None, page: int, limit: int, category: str | None,
             city: str | None, district: str | None, state: str | None,
             national: bool | None, breaking: bool | None) -> dict:

    if not user.anchor_time:
        user.anchor_time = datetime.utcnow()
        db.commit()

    cache_key = f"feed:{language}:{window}:{category}:{city}:{state}:{last_id}:{limit}"
    cached = cache_store.cache_get(cache_key)
    if cached:
        return cached

    window_start, window_end = _get_window_bounds(user, window)

    q = db.query(News, Category, Language).outerjoin(
        Category, News.category_code == Category.code
    ).join(Language, News.language_code == Language.code).filter(
        News.language_code == language,
        News.published_at >= window_start,
        News.published_at <= window_end,
    )

    if last_id:
        q = q.filter(News.id < last_id)
    if after_id:
        q = q.filter(News.id > after_id)
    if category:
        q = q.filter(News.category_code == category)
    if city:
        q = q.filter(News.city == city)
    if district:
        q = q.filter(News.district == district)
    if state:
        q = q.filter(News.state == state)
    if national:
        q = q.filter(News.national == 1)
    if breaking:
        q = q.filter(News.is_breaking == 1)

    use_cursor = window in ("latest", "today")
    if use_cursor:
        q = q.order_by(News.is_breaking.desc(), News.id.desc())
    else:
        q = q.order_by(News.is_breaking.desc(), News.published_at.desc())
        q = q.offset((page - 1) * limit)

    rows = q.limit(limit + 1).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    data = [_row_to_card(n, cat, lang) for n, cat, lang in rows]
    next_cursor = data[-1]["id"] if data and has_more else None

    result = {
        "window": window,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "next_cursor": next_cursor,
        "has_more": has_more,
        "count": len(data),
        "data": data,
    }
    cache_store.cache_set(cache_key, result, WINDOW_TTL.get(window, 120))
    return result


def get_article(db: Session, news_id: int) -> dict | None:
    row = db.query(News, Category, Language).outerjoin(
        Category, News.category_code == Category.code
    ).join(Language, News.language_code == Language.code).filter(News.id == news_id).first()
    if not row:
        return None
    n, cat, lang = row
    available = [r[0] for r in db.query(News.language_code).filter(News.raw_id == n.raw_id).all()]
    card = _row_to_card(n, cat, lang)
    card.update({
        "raw_id": n.raw_id,
        "content": n.content,
        "audio_size_bytes": n.audio_size_bytes,
        "audio_play_count": n.audio_play_count,
        "share_count": n.share_count,
        "language_name": lang.name_english if lang else None,
        "language_native": lang.name_native if lang else None,
        "district": n.district,
        "available_languages": available,
    })
    return card


def get_trending(db: Session, language: str, city: str | None, limit: int, hours: int) -> list:
    since = datetime.utcnow() - timedelta(hours=hours)
    q = db.query(News, Category, Language).outerjoin(
        Category, News.category_code == Category.code
    ).join(Language, News.language_code == Language.code).filter(
        News.language_code == language,
        News.published_at >= since,
    )
    if city:
        q = q.filter(News.city == city)
    rows = q.order_by(News.view_count.desc(), News.audio_play_count.desc()).limit(limit).all()
    return [_row_to_card(n, cat, lang) for n, cat, lang in rows]


def get_breaking(db: Session, language: str, limit: int) -> list:
    rows = db.query(News, Category, Language).outerjoin(
        Category, News.category_code == Category.code
    ).join(Language, News.language_code == Language.code).filter(
        News.language_code == language,
        News.is_breaking == 1,
    ).order_by(News.published_at.desc()).limit(limit).all()
    return [_row_to_card(n, cat, lang) for n, cat, lang in rows]


def search_news(db: Session, q: str, language: str, category: str | None, page: int, limit: int) -> dict:
    since = datetime.utcnow() - timedelta(days=30)
    base = db.query(News, Category, Language).outerjoin(
        Category, News.category_code == Category.code
    ).join(Language, News.language_code == Language.code).filter(
        News.language_code == language,
        News.published_at >= since,
        text("MATCH(news.title, news.content) AGAINST(:q IN BOOLEAN MODE)").bindparams(q=q),
    )
    if category:
        base = base.filter(News.category_code == category)
    total = base.count()
    rows = base.offset((page - 1) * limit).limit(limit).all()
    return {"query": q, "total": total, "page": page, "data": [_row_to_card(n, cat, lang) for n, cat, lang in rows]}


def _row_to_card(n: News, cat: Category | None, lang: Language | None) -> dict:
    return {
        "id": n.id,
        "language_code": n.language_code,
        "title": n.title,
        "summary": n.summary,
        "audio_url": n.audio_url,
        "audio_duration": n.audio_duration,
        "image_url": n.image_url,
        "category_code": n.category_code,
        "category_name": cat.name_english if cat else None,
        "category_icon": cat.icon_emoji if cat else None,
        "category_color": cat.color_hex if cat else None,
        "state": n.state,
        "city": n.city,
        "is_breaking": bool(n.is_breaking),
        "view_count": n.view_count,
        "like_count": n.like_count,
        "dislike_count": n.dislike_count,
        "published_at": n.published_at.isoformat(),
    }
