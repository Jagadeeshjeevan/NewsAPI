import os
from datetime import datetime
from app.core.celery_app import celery_app
from app.core.config import settings


@celery_app.task(name="app.services.ai_service.task_process_approved_news")
def task_process_approved_news(raw_id: int, is_breaking: bool = False, use_ai_rewrite: bool = True):
    from app.core.database import SessionLocal
    from app.models.models import NewsRaw, News, Language
    import openai

    db = SessionLocal()
    try:
        raw = db.query(NewsRaw).filter(NewsRaw.id == raw_id).first()
        if not raw:
            return

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        text_to_use = raw.original_text

        if use_ai_rewrite and settings.OPENAI_API_KEY:
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{
                        "role": "user",
                        "content": f"Rewrite this news article in clear English. Keep it factual and concise:\n\n{text_to_use}"
                    }],
                    max_tokens=800,
                )
                text_to_use = resp.choices[0].message.content
                raw.ai_rewritten = text_to_use
                db.commit()
            except Exception:
                pass

        languages = db.query(Language).filter(Language.is_active == 1).all()
        for lang in languages:
            translated = _translate(text_to_use, lang.code)
            summary = translated[:300] if translated else ""

            news = News(
                raw_id=raw_id,
                language_id=lang.id,
                language_code=lang.code,
                title=_translate(raw.original_text[:200], lang.code),
                summary=summary,
                content=translated,
                image_url=None,
                category_id=raw.category_id,
                category_code=raw.category_code,
                state=raw.state,
                district=raw.district,
                city=raw.city,
                is_breaking=1 if is_breaking else 0,
                published_at=datetime.utcnow(),
            )
            db.add(news)
            db.flush()

            audio_url = _generate_tts(translated, lang.code, news.id, lang.tts_voice)
            if audio_url:
                news.audio_url = audio_url
            db.commit()

        task_send_notifications.delay(raw_id)

    finally:
        db.close()


def _translate(text: str, target_lang: str) -> str:
    if target_lang == "en":
        return text
    try:
        from google.cloud import translate_v2 as translate
        client = translate.Client()
        result = client.translate(text, target_language=target_lang)
        return result["translatedText"]
    except Exception:
        return text


def _generate_tts(text: str, lang_code: str, news_id: int, tts_voice: str | None) -> str | None:
    try:
        from google.cloud import texttospeech
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text[:4500])
        voice = texttospeech.VoiceSelectionParams(
            language_code=f"{lang_code}-IN",
            name=tts_voice or f"{lang_code}-IN-Standard-A",
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        dir_path = os.path.join(settings.AUDIO_STORAGE_PATH, lang_code)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, f"{news_id}.mp3")
        with open(file_path, "wb") as f:
            f.write(response.audio_content)
        return f"/audio/{lang_code}/{news_id}.mp3"
    except Exception:
        return None


@celery_app.task(name="app.services.ai_service.task_send_notifications")
def task_send_notifications(raw_id: int):
    from app.core.database import SessionLocal
    from app.models.models import News, Subscription, UserDeviceToken, User
    from app.services.notify_service import send_push_to_devices, _is_quiet_hours

    db = SessionLocal()
    try:
        news_rows = db.query(News).filter(News.raw_id == raw_id).all()
        if not news_rows:
            return
        sample = news_rows[0]

        subs = db.query(Subscription).filter(Subscription.is_active == 1).all()
        user_ids = set()
        for sub in subs:
            if sub.type == "breaking" and sample.is_breaking:
                user_ids.add(sub.user_id)
            elif sub.type == "category" and sub.category == sample.category_code:
                user_ids.add(sub.user_id)
            elif sub.type == "location" and (
                sub.city == sample.city or sub.state == sample.state
            ):
                user_ids.add(sub.user_id)

        for user_id in user_ids:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                continue
            lang_news = next((n for n in news_rows if n.language_code == user.preferred_lang), sample)
            devices = db.query(UserDeviceToken).filter(
                UserDeviceToken.user_id == user_id,
                UserDeviceToken.notifications_enabled == 1,
            ).all()
            tokens = [d.fcm_token for d in devices if not _is_quiet_hours(d)]
            if tokens:
                send_push_to_devices(tokens, lang_news.title[:80], lang_news.summary or "", {"news_id": str(lang_news.id)})
    finally:
        db.close()


