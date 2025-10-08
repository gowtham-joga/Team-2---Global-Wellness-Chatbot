from fastapi import FastAPI
from .database import engine
from . import models
from .routers import users, chat, admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Global Wellness Chatbot - Final Build")

app.include_router(users.router)
app.include_router(chat.router)
app.include_router(admin.router)