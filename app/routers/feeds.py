from flask import Blueprint, request, jsonify, g
from app.core.database import get_db
from app.dependencies.auth import _get_current_user, registered_required
from app.models.models import News, NewsReaction, Bookmark, UserReadHistory
from app.services import feed_service
from app.schemas.schemas import ReactRequest

bp = Blueprint("feeds", __name__)


def _optional_user():
    user, _ = _get_current_user()
    return user


# API 26: GET /feeds/
@bp.get("/")
def get_feed():
    db = get_db()
    args = request.args
    language = args.get("language")
    if not language:
        return jsonify({"detail": "language is required"}), 422

    limit = min(max(int(args.get("limit", 20)), 1), 50)
    last_id = args.get("last_id", type=int)
    after_id = args.get("after_id", type=int)
    national = args.get("national", type=lambda v: v.lower() == "true")
    breaking = args.get("breaking", type=lambda v: v.lower() == "true")

    result = feed_service.get_feed(
        db, _optional_user(),
        language=language,
        window=args.get("window", "today"),
        last_id=last_id,
        after_id=after_id,
        page=int(args.get("page", 1)),
        limit=limit,
        category=args.get("category"),
        city=args.get("city"),
        district=args.get("district"),
        state=args.get("state"),
        national=national,
        breaking=breaking,
    )
    return jsonify(result)


# API 28: GET /feeds/trending
@bp.get("/trending")
def get_trending():
    db = get_db()
    language = request.args.get("language")
    if not language:
        return jsonify({"detail": "language is required"}), 422
    data = feed_service.get_trending(
        db, language,
        city=request.args.get("city"),
        limit=int(request.args.get("limit", 10)),
        hours=int(request.args.get("hours", 24)),
    )
    return jsonify(data)


# API 29: GET /feeds/breaking
@bp.get("/breaking")
def get_breaking():
    db = get_db()
    language = request.args.get("language")
    if not language:
        return jsonify({"detail": "language is required"}), 422
    return jsonify(feed_service.get_breaking(db, language, int(request.args.get("limit", 5))))


# API 30: GET /feeds/search
@bp.get("/search")
def search():
    db = get_db()
    q = request.args.get("q", "")
    language = request.args.get("language")
    if not language:
        return jsonify({"detail": "language is required"}), 422
    return jsonify(feed_service.search_news(
        db, q, language,
        category=request.args.get("category"),
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
    ))


# API 37: GET /feeds/bookmarks
@bp.get("/bookmarks")
@registered_required
def get_bookmarks():
    db = get_db()
    language = request.args.get("language")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    q = db.query(Bookmark, News).join(News, Bookmark.news_id == News.id).filter(
        Bookmark.user_id == g.current_user.id
    )
    if language:
        q = q.filter(News.language_code == language)
    total = q.count()
    rows = q.order_by(Bookmark.saved_at.desc()).offset((page - 1) * limit).limit(limit).all()
    data = [{"saved_at": bm.saved_at, "id": n.id, "title": n.title,
             "language_code": n.language_code, "published_at": n.published_at} for bm, n in rows]
    return jsonify({"total": total, "page": page, "data": data})


# API 27: GET /feeds/<id>
@bp.get("/<int:news_id>")
def get_article(news_id):
    db = get_db()
    article = feed_service.get_article(db, news_id)
    if not article:
        return jsonify({"detail": "Article not found"}), 404
    db.query(News).filter(News.id == news_id).update({"view_count": News.view_count + 1})
    user = _optional_user()
    if user and user.user_type == "registered":
        existing = db.query(UserReadHistory).filter(
            UserReadHistory.user_id == user.id, UserReadHistory.news_id == news_id
        ).first()
        if not existing:
            db.add(UserReadHistory(user_id=user.id, news_id=news_id))
    db.commit()
    return jsonify(article)


# API 31: POST /feeds/<id>/read
@bp.post("/<int:news_id>/read")
def mark_read(news_id):
    db = get_db()
    db.query(News).filter(News.id == news_id).update({"view_count": News.view_count + 1})
    user = _optional_user()
    if user and user.user_type == "registered":
        existing = db.query(UserReadHistory).filter(
            UserReadHistory.user_id == user.id, UserReadHistory.news_id == news_id
        ).first()
        if not existing:
            db.add(UserReadHistory(user_id=user.id, news_id=news_id))
    db.commit()
    return jsonify({"message": "Marked as read"})


# API 32: POST /feeds/<id>/share
@bp.post("/<int:news_id>/share")
def share(news_id):
    db = get_db()
    db.query(News).filter(News.id == news_id).update({"share_count": News.share_count + 1})
    db.commit()
    news = db.query(News).filter(News.id == news_id).first()
    return jsonify({"share_count": news.share_count if news else 0})


# API 33: POST /feeds/<id>/react
@bp.post("/<int:news_id>/react")
@registered_required
def react(news_id):
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = ReactRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422

    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        return jsonify({"detail": "Article not found"}), 404

    existing = db.query(NewsReaction).filter(
        NewsReaction.user_id == g.current_user.id,
        NewsReaction.news_id == news_id,
    ).first()

    if not existing:
        db.add(NewsReaction(user_id=g.current_user.id, news_id=news_id, reaction=body.reaction))
        if body.reaction == "like":
            news.like_count += 1
        else:
            news.dislike_count += 1
        action, my_reaction = "added", body.reaction
    elif existing.reaction == body.reaction:
        db.delete(existing)
        if body.reaction == "like":
            news.like_count = max(0, news.like_count - 1)
        else:
            news.dislike_count = max(0, news.dislike_count - 1)
        action, my_reaction = "removed", None
    else:
        if existing.reaction == "like":
            news.like_count = max(0, news.like_count - 1)
            news.dislike_count += 1
        else:
            news.dislike_count = max(0, news.dislike_count - 1)
            news.like_count += 1
        existing.reaction = body.reaction
        action, my_reaction = "changed", body.reaction

    db.commit()
    db.refresh(news)
    return jsonify({"action": action, "my_reaction": my_reaction,
                    "like_count": news.like_count, "dislike_count": news.dislike_count})


# API 34: GET /feeds/<id>/reactions
@bp.get("/<int:news_id>/reactions")
def get_reactions(news_id):
    db = get_db()
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        return jsonify({"detail": "Article not found"}), 404
    my_reaction = None
    user = _optional_user()
    if user and user.user_type == "registered":
        r = db.query(NewsReaction).filter(
            NewsReaction.user_id == user.id, NewsReaction.news_id == news_id
        ).first()
        my_reaction = r.reaction if r else None
    return jsonify({"like_count": news.like_count, "dislike_count": news.dislike_count, "my_reaction": my_reaction})


# API 35: POST /feeds/<id>/bookmark
@bp.post("/<int:news_id>/bookmark")
@registered_required
def bookmark(news_id):
    db = get_db()
    existing = db.query(Bookmark).filter(
        Bookmark.user_id == g.current_user.id, Bookmark.news_id == news_id
    ).first()
    if not existing:
        db.add(Bookmark(user_id=g.current_user.id, news_id=news_id))
        db.commit()
    return jsonify({"message": "Bookmarked", "news_id": news_id}), 201


# API 36: DELETE /feeds/<id>/bookmark
@bp.delete("/<int:news_id>/bookmark")
@registered_required
def remove_bookmark(news_id):
    db = get_db()
    db.query(Bookmark).filter(
        Bookmark.user_id == g.current_user.id, Bookmark.news_id == news_id
    ).delete()
    db.commit()
    return jsonify({"message": "Bookmark removed"})
