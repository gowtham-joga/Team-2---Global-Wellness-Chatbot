from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone # <-- Uses timezone-aware datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# IMPORTANT: In a real production app, this key should be a long, random string
# and stored securely as an environment variable, not in the code.
SECRET_KEY = "a_very_secret_key_for_your_project"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    # Use timezone-aware datetime for robustness
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None