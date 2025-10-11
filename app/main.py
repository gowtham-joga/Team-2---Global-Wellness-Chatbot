from fastapi import FastAPI
# 👇 THIS IMPORT IS NEW
from fastapi.middleware.cors import CORSMiddleware 

from .database import engine
from . import models
from .routers import users, chat, admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Global Wellness Chatbot - Final Build")

# 👇 THIS ENTIRE BLOCK IS NEW
# This tells your backend to accept requests from your Streamlit frontend
origins = ["*"] # Allows all origins, which is fine for local development

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(chat.router)
app.include_router(admin.router)