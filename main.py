import decimal
from datetime import datetime, date
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from app.core.database import close_db
from app.core.logger import init_logging
from app.routers import auth, users, news, feeds, audio, admin, subscriptions, reference, docs


class JsonProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


app = Flask(__name__)
app.json_provider_class = JsonProvider
app.json = JsonProvider(app)

CORS(app, resources={r"/*": {"origins": "*"}})
app.teardown_appcontext(close_db)
init_logging(app)

app.register_blueprint(auth.bp,          url_prefix="/auth")
app.register_blueprint(users.bp,         url_prefix="/users")
app.register_blueprint(news.bp,          url_prefix="/news")
app.register_blueprint(feeds.bp,         url_prefix="/feeds")
app.register_blueprint(audio.bp,         url_prefix="/audio")
app.register_blueprint(admin.bp,         url_prefix="/admin")
app.register_blueprint(subscriptions.bp, url_prefix="/subscriptions")
app.register_blueprint(reference.bp)
app.register_blueprint(docs.bp)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
