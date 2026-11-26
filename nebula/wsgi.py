"""WSGI entry point for hosts that only run WSGI (PythonAnywhere's free web apps).

The FastAPI app is ASGI; a2wsgi adapts it. Saves go to NEBULA_DB, which defaults to
saves/nebula.db inside the project folder (persistent on PythonAnywhere).
"""

from a2wsgi import ASGIMiddleware

from nebula.api import app as asgi_app

application = ASGIMiddleware(asgi_app)
