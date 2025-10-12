# upload_model.py
from huggingface_hub import HfApi, login
import os

# --- IMPORTANT: FILL THIS IN ---
HF_USERNAME = "Agoj"  # <-- PUT YOUR USERNAME HERE
# --------------------------------

REPO_NAME = "global-wellness-chatbot-nlu"
LOCAL_MODEL_DIR = "nlu_model"

print("Logging into Hugging Face Hub...")
login() # When this asks for a token, paste the one you just copied.

api = HfApi()
print(f"Creating repository '{REPO_NAME}'...")
api.create_repo(repo_id=f"{HF_USERNAME}/{REPO_NAME}", repo_type="model", exist_ok=True)

print(f"Uploading '{LOCAL_MODEL_DIR}' folder...")
api.upload_folder(
    folder_path=LOCAL_MODEL_DIR,
    repo_id=f"{HF_USERNAME}/{REPO_NAME}",
    repo_type="model",
)
print("\n✅ Upload complete!")