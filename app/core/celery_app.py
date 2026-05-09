from app.core.config import settings

if settings.REDIS_ENABLED:
    from celery import Celery

    celery_app = Celery(
        "diginews",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        include=["app.services.ai_service"],
    )

    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Kolkata",
    )
else:
    class _DummyCelery:
        def task(self, *args, **kwargs):
            def decorator(f):
                def delay(*a, **kw):
                    pass
                f.delay = delay
                return f
            return decorator

    celery_app = _DummyCelery()
