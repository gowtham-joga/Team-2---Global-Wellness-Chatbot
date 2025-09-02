from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional

from app import models, schemas, database
from app.utils.utils import hash_password, verify_password, create_access_token, decode_token

router = APIRouter(prefix="/users", tags=["Users"])

# Point tokenUrl to your actual login path so Swagger shows the right place
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# -------- Register --------
@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    existing_user = (
        db.query(models.User)
        .filter((models.User.username == user.username) | (models.User.email == user.email))
        .first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or Email already registered")

    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        age=user.age,
        language=user.language,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# -------- Login --------
class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=schemas.Token)
def login(request: LoginRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


# -------- Current user dependency (centralizes auth) --------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db),
):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(models.User).filter(models.User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# -------- Me --------
@router.get("/me", response_model=schemas.UserResponse)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


# -------- Update profile (AUTH REQUIRED) --------
@router.put("/update", response_model=schemas.UserResponse)
def update_profile(
    update: schemas.UpdateProfileRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    if update.age is not None:
        current_user.age = update.age
    if update.language is not None:
        current_user.language = update.language

    db.commit()
    db.refresh(current_user)
    return current_user



