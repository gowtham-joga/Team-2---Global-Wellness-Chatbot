from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .. import models, schemas, database, utils

router = APIRouter(prefix="/users", tags=["Users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# -----------------------------
# Helpers (Unchanged)
# -----------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    payload = utils.decode_token(token)
    if not payload or not (user_id := payload.get("sub")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

def get_admin_user(current_user: models.User = Depends(get_current_user)):
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return current_user

# -----------------------------
# Register (Unchanged)
# -----------------------------
@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=utils.hash_password(user.password),
        language=user.language,
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# -----------------------------
# Login (Unchanged)
# -----------------------------
@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    # Note: The subject 'sub' for the main access token is the user's ID
    return {"access_token": utils.create_access_token({"sub": str(user.id)}), "token_type": "bearer"}

# -----------------------------
# Profile
# -----------------------------
@router.get("/me", response_model=schemas.UserResponse)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user

## UPDATED: Uses the new UserUpdate schema for better practice ##
@router.put("/me", response_model=schemas.UserResponse)
def update_profile(update_data: schemas.UserUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    current_user.username = update_data.username
    current_user.email = update_data.email
    current_user.language = update_data.language
    db.commit()
    db.refresh(current_user)
    return current_user

# -----------------------------
# Forgot / Reset Password (UPDATED LOGIC)
# -----------------------------
@router.post("/forgot-password")
def forgot_password(req: schemas.ForgotPasswordRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if user:
        # In a real app, you would email this link.
        # For this project, we will print it to the backend terminal.
        
        # The 'sub' for the reset token is the user's email. A 'type' is added for security.
        token = utils.create_access_token({"sub": user.email, "type": "reset"})
        
        # This is a placeholder link for the Streamlit frontend
        reset_link = f"http://localhost:8501/?page=reset-password&token={token}"
        
        print("--- PASSWORD RESET LINK (Copy and paste into your browser) ---")
        print(reset_link)
        print("----------------------------------------------------------------")
        
    # Always return the same message to prevent users from guessing emails.
    return {"message": "If an account with that email exists, a reset link has been generated."}


@router.post("/reset-password")
def reset_password(req: schemas.ResetPasswordRequest, db: Session = Depends(database.get_db)):
    # Decode the token to get the user's email
    payload = utils.decode_token(req.token)
    if not payload or payload.get("type") != "reset" or not (email := payload.get("sub")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        # This case is unlikely if the token is valid, but it's good practice.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    # Set the new password
    user.hashed_password = utils.hash_password(req.new_password)
    db.commit()
    return {"message": "Password reset successful"}