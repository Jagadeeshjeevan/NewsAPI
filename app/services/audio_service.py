import os
from flask import Response, stream_with_context, jsonify
from sqlalchemy.orm import Session
from app.models.models import News
from app.core.config import settings


def get_audio_meta(db: Session, news_id: int):
    news = db.query(News).filter(News.id == news_id).first()
    if not news or not news.audio_url:
        return jsonify({"detail": "Audio not found"}), 404
    return {
        "news_id": news_id,
        "audio_url": news.audio_url,
        "audio_duration": news.audio_duration,
        "audio_size_bytes": news.audio_size_bytes,
        "language_code": news.language_code,
    }


def stream_audio(db: Session, news_id: int, range_header: str | None):
    news = db.query(News).filter(News.id == news_id).first()
    if not news or not news.audio_url:
        return jsonify({"detail": "Audio not found"}), 404

    file_path = os.path.join(settings.AUDIO_STORAGE_PATH, news.audio_url.lstrip("/"))
    if not os.path.exists(file_path):
        return jsonify({"detail": "Audio file not found on disk"}), 404

    file_size = os.path.getsize(file_path)

    if range_header:
        range_val = range_header.replace("bytes=", "")
        parts = range_val.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
        length = end - start + 1

        def generate_partial():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(8192, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return Response(
            stream_with_context(generate_partial()),
            status=206,
            mimetype="audio/mpeg",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
            },
        )

    def generate_full():
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return Response(
        stream_with_context(generate_full()),
        mimetype="audio/mpeg",
        headers={"Accept-Ranges": "bytes", "Content-Length": str(file_size)},
    )

