from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

templates = Jinja2Templates(directory="app/templates")

def add_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )