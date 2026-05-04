import sys
import os

APPDIR = os.path.dirname(__file__)
sys.path.insert(0, APPDIR)

from a2wsgi import ASGIMiddleware
from main import app

application = ASGIMiddleware(app)
