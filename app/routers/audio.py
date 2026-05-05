from flask import Blueprint, request, jsonify, g
from app.core.database import get_db
from app.dependencies.auth import auth_required
from app.models.models import News
from app.services.audio_service import get_audio_meta, stream_audio

bp = Blueprint("audio", __name__)


# API 40: GET /audio/stream/<news_id>
@bp.get("/stream/<int:news_id>")
@auth_required
def stream(news_id):
    db = get_db()
    range_header = request.headers.get("Range")
    return stream_audio(db, news_id, range_header)


# API 41: GET /audio/meta/<news_id>
@bp.get("/meta/<int:news_id>")
@auth_required
def meta(news_id):
    db = get_db()
    result = get_audio_meta(db, news_id)
    if isinstance(result, tuple):
        return result
    return jsonify(result)


# API 42: POST /audio/play/<news_id>
@bp.post("/play/<int:news_id>")
@auth_required
def play(news_id):
    db = get_db()
    db.query(News).filter(News.id == news_id).update({"audio_play_count": News.audio_play_count + 1})
    db.commit()
    news = db.query(News).filter(News.id == news_id).first()
    return jsonify({"audio_play_count": news.audio_play_count if news else 0})
