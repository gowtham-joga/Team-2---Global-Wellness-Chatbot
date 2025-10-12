# E:/WELLNESS/app/utils.py (The Final, Correct Version)

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

# 1. Switch to a reliable hashing scheme to avoid bcrypt errors.
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# This is the secret key for your JWT tokens.
SECRET_KEY = "a_very_secret_key_for_your_project"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def hash_password(password: str):
    # 2. Truncate password before hashing.
    return pwd_context.hash(password[:72])

def verify_password(plain_password, hashed_password):
    # 3. Truncate password here as well, before verifying. This is the critical fix.
    return pwd_context.verify(plain_password[:72], hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None