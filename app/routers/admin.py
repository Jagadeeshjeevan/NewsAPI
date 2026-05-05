from datetime import datetime
from flask import Blueprint, request, jsonify, g
from sqlalchemy import func
from app.core.database import get_db
from app.core import redis as cache_store
from app.dependencies.auth import admin_required
from app.models.models import User, NewsRaw, News, Category, Language
from app.schemas.schemas import (
    ApproveRequest, RejectRequest, AdminEditRequest, BreakingFlagRequest,
    PublishedEditRequest, AdminPushRequest, LanguageCreate, LanguagePatch,
    CategoryCreate, CategoryPatch,
)
from app.services.ai_service import task_process_approved_news
from app.services.notify_service import send_admin_blast

bp = Blueprint("admin", __name__)


# API 14: GET /admin/queue
@bp.get("/queue")
@admin_required
def get_queue():
    db = get_db()
    args = request.args
    page = int(args.get("page", 1))
    limit = int(args.get("limit", 20))
    q = db.query(NewsRaw).filter(NewsRaw.status == "pending")
    if args.get("category_code"):
        q = q.filter(NewsRaw.category_code == args["category_code"])
    if args.get("source"):
        q = q.filter(NewsRaw.source == args["source"])
    if args.get("min_score"):
        q = q.filter(NewsRaw.ai_score >= float(args["min_score"]))
    if args.get("max_score"):
        q = q.filter(NewsRaw.ai_score <= float(args["max_score"]))
    total = q.count()
    rows = q.order_by(NewsRaw.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return jsonify({"total": total, "page": page, "limit": limit, "data": [
        {"id": r.id, "source": r.source, "source_url": r.source_url,
         "original_text": (r.original_text or "")[:500], "ai_summary": r.ai_summary,
         "ai_score": r.ai_score, "category_code": r.category_code,
         "city": r.city, "state": r.state, "is_duplicate": bool(r.is_duplicate),
         "created_at": r.created_at} for r in rows
    ]})


# API 15: GET /admin/queue/<id>
@bp.get("/queue/<int:raw_id>")
@admin_required
def get_queue_item(raw_id):
    db = get_db()
    raw = db.query(NewsRaw).filter(NewsRaw.id == raw_id).first()
    if not raw:
        return jsonify({"detail": "Not found"}), 404
    return jsonify({"id": raw.id, "source": raw.source, "source_url": raw.source_url,
                    "original_text": raw.original_text, "ai_rewritten": raw.ai_rewritten,
                    "ai_summary": raw.ai_summary, "ai_score": raw.ai_score,
                    "category_code": raw.category_code, "state": raw.state, "city": raw.city,
                    "status": raw.status, "created_at": raw.created_at})


# API 16: POST /admin/queue/<id>/approve
@bp.post("/queue/<int:raw_id>/approve")
@admin_required
def approve(raw_id):
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = ApproveRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    raw = db.query(NewsRaw).filter(NewsRaw.id == raw_id, NewsRaw.status == "pending").first()
    if not raw:
        return jsonify({"detail": "Pending article not found"}), 404
    raw.status = "approved"
    raw.reviewed_by = g.current_user.id
    raw.reviewed_at = datetime.utcnow()
    db.commit()
    cache_store.cache_delete_pattern("feed:*")
    task_process_approved_news.delay(raw_id, body.is_breaking, body.use_ai_rewrite)
    return jsonify({"message": "Article approved. Translation and audio generation started.",
                    "raw_id": raw_id, "job_status": "processing"})


# API 17: POST /admin/queue/<id>/reject
@bp.post("/queue/<int:raw_id>/reject")
@admin_required
def reject(raw_id):
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = RejectRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    raw = db.query(NewsRaw).filter(NewsRaw.id == raw_id, NewsRaw.status == "pending").first()
    if not raw:
        return jsonify({"detail": "Pending article not found"}), 404
    raw.status = "rejected"
    raw.rejection_reason = body.reason
    raw.reviewed_by = g.current_user.id
    raw.reviewed_at = datetime.utcnow()
    db.commit()
    return jsonify({"message": "Article rejected", "raw_id": raw_id})


# API 18: PATCH /admin/queue/<id>
@bp.patch("/queue/<int:raw_id>")
@admin_required
def edit_queue(raw_id):
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = AdminEditRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    raw = db.query(NewsRaw).filter(NewsRaw.id == raw_id, NewsRaw.status == "pending").first()
    if not raw:
        return jsonify({"detail": "Pending article not found"}), 404
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(raw, field, val)
    if body.category_code:
        cat = db.query(Category).filter(Category.code == body.category_code).first()
        if cat:
            raw.category_id = cat.id
    db.commit()
    return jsonify({"id": raw.id, "status": raw.status, "category_code": raw.category_code})


# API 19: PATCH /admin/queue/<id>/breaking
@bp.patch("/queue/<int:raw_id>/breaking")
@admin_required
def toggle_breaking(raw_id):
    data = request.get_json(force=True) or {}
    try:
        body = BreakingFlagRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    return jsonify({"message": "Breaking news flag updated", "is_breaking": body.is_breaking})


# API 20: GET /admin/published
@bp.get("/published")
@admin_required
def get_published():
    db = get_db()
    args = request.args
    page = int(args.get("page", 1))
    limit = int(args.get("limit", 20))
    q = db.query(News)
    if args.get("language_code"):
        q = q.filter(News.language_code == args["language_code"])
    if args.get("category_code"):
        q = q.filter(News.category_code == args["category_code"])
    if args.get("city"):
        q = q.filter(News.city == args["city"])
    total = q.count()
    rows = q.order_by(News.published_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return jsonify({"total": total, "page": page, "data": [
        {"id": n.id, "raw_id": n.raw_id, "language_code": n.language_code, "title": n.title,
         "category_code": n.category_code, "city": n.city, "is_breaking": bool(n.is_breaking),
         "view_count": n.view_count, "audio_play_count": n.audio_play_count,
         "like_count": n.like_count, "published_at": n.published_at} for n in rows
    ]})


# API 21: PATCH /admin/published/<id>
@bp.patch("/published/<int:news_id>")
@admin_required
def edit_published(news_id):
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = PublishedEditRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        return jsonify({"detail": "Not found"}), 404
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(news, field, val)
    db.commit()
    cache_store.cache_delete_pattern("feed:*")
    return jsonify({"id": news.id, "title": news.title, "is_breaking": bool(news.is_breaking)})


# API 22: DELETE /admin/published/<id>
@bp.delete("/published/<int:news_id>")
@admin_required
def delete_published(news_id):
    db = get_db()
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        return jsonify({"detail": "Not found"}), 404
    db.delete(news)
    db.commit()
    cache_store.cache_delete_pattern("feed:*")
    return jsonify({"message": "Article unpublished successfully"})


# API 23: GET /admin/analytics
@bp.get("/analytics")
@admin_required
def analytics():
    db = get_db()
    total_guests = db.query(func.count(User.id)).filter(User.user_type == "guest").scalar() or 0
    total_reg = db.query(func.count(User.id)).filter(User.user_type == "registered").scalar() or 0
    total_views = db.query(func.sum(News.view_count)).scalar() or 0
    total_audio = db.query(func.sum(News.audio_play_count)).scalar() or 0
    total_likes = db.query(func.sum(News.like_count)).scalar() or 0
    pending = db.query(func.count(NewsRaw.id)).filter(NewsRaw.status == "pending").scalar() or 0
    total_pub = db.query(func.count(News.id)).scalar() or 0
    return jsonify({
        "users": {"total_guests": total_guests, "total_registered": total_reg},
        "news": {"pending": pending, "total_published": total_pub},
        "engagement": {"total_views": total_views, "total_audio_plays": total_audio, "total_likes": total_likes},
    })


# API 24: GET /admin/users
@bp.get("/users")
@admin_required
def list_users():
    db = get_db()
    args = request.args
    page = int(args.get("page", 1))
    limit = int(args.get("limit", 50))
    q = db.query(User)
    if args.get("user_type"):
        q = q.filter(User.user_type == args["user_type"])
    if args.get("search"):
        s = f"%{args['search']}%"
        q = q.filter((User.name.ilike(s)) | (User.email.ilike(s)))
    total = q.count()
    rows = q.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return jsonify({"total": total, "page": page, "data": [
        {"id": u.id, "user_type": u.user_type, "name": u.name, "email": u.email,
         "preferred_lang": u.preferred_lang, "is_admin": bool(u.is_admin), "created_at": u.created_at}
        for u in rows
    ]})


# API 25: POST /admin/push
@bp.post("/push")
@admin_required
def admin_push():
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = AdminPushRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    return jsonify(send_admin_blast(db, body.title, body.body, body.language_code, body.state, body.city, body.news_id))


# API 49: POST /admin/languages
@bp.post("/languages")
@admin_required
def add_language():
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = LanguageCreate(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    if db.query(Language).filter(Language.code == body.code).first():
        return jsonify({"detail": "Language code already exists"}), 409
    lang = Language(**body.model_dump())
    db.add(lang)
    db.commit()
    db.refresh(lang)
    cache_store.cache_delete_pattern("ref:languages")
    return jsonify({"id": lang.id, "code": lang.code, "name_english": lang.name_english}), 201


# API 50: PATCH /admin/languages/<id>
@bp.patch("/languages/<int:lang_id>")
@admin_required
def update_language(lang_id):
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = LanguagePatch(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    lang = db.query(Language).filter(Language.id == lang_id).first()
    if not lang:
        return jsonify({"detail": "Language not found"}), 404
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(lang, field, val)
    db.commit()
    cache_store.cache_delete_pattern("ref:languages")
    return jsonify({"id": lang.id, "code": lang.code, "name_english": lang.name_english})


# API 51: POST /admin/categories
@bp.post("/categories")
@admin_required
def add_category():
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = CategoryCreate(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    if db.query(Category).filter(Category.code == body.code).first():
        return jsonify({"detail": "Category code already exists"}), 409
    cat = Category(**body.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    cache_store.cache_delete_pattern("ref:categories")
    return jsonify({"id": cat.id, "code": cat.code, "name_english": cat.name_english}), 201


# API 52: PATCH /admin/categories/<id>
@bp.patch("/categories/<int:cat_id>")
@admin_required
def update_category(cat_id):
    db = get_db()
    data = request.get_json(force=True) or {}
    try:
        body = CategoryPatch(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 422
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        return jsonify({"detail": "Category not found"}), 404
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(cat, field, val)
    db.commit()
    cache_store.cache_delete_pattern("ref:categories")
    return jsonify({"id": cat.id, "code": cat.code, "name_english": cat.name_english})
