from fastapi import FastAPI
from app.routers import users
from app import models, database

# Create DB tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Global Wellness Chatbot API")

# Register routers
app.include_router(users.router)

