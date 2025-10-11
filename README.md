# Global Wellness Chatbot (WellBot)

## 📖 Description

**WellBot** is an AI-powered, bilingual (English/Hindi) chatbot designed to provide instant, reliable wellness and first-aid information. It features a comprehensive admin dashboard for real-time management, analytics, and continuous improvement based on user feedback. This project was developed as a final year submission.



## ✨ Key Features

### User Features
* **Bilingual Chat:** Interact with the bot in either English or Hindi.
* **Secure Authentication:** Full user registration and login system.
* **Profile Management:** Users can view and update their profile details.
* **Feedback System:** Users can rate bot responses with a 👍/👎 and leave optional comments.
* **Password Reset:** A secure, token-based "Forgot Password" feature that sends a reset link via email.

### Admin Features
* **Secure Admin Dashboard:** A separate, protected area for application management.
* **Analytics:** View charts for query trends, top intents, and overall user feedback scores.
* **Knowledge Base Management:** A powerful UI to add, edit, delete, search, and filter all bot responses.
* **Feedback Review:** A dedicated panel to review all user feedback and comments.
* **Unanswered Questions Log:** Automatically logs questions the bot could not answer, helping to identify knowledge gaps.

## 💻 Tech Stack

* **Backend:** FastAPI, SQLAlchemy, Uvicorn
* **Frontend:** Streamlit
* **Database:** SQLite
* **AI / NLU:** Transformers, PyTorch, `thefuzz` for intent recognition and entity extraction.
* **Security:** JWT for token-based authentication, `passlib` with `bcrypt` for password hashing.
* **Deployment:** Docker

## 🚀 Setup and Installation

Follow these steps to get the project running locally.

### 1. Clone the Repository
```bash
git clone <your-repo-link>
cd <your-repo-folder>
```

### 2. Set Up Virtual Environment
```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up the Database
Run the setup script to create and populate the initial `knowledge_base` table from `kb.json`.
```bash
python setup_database.py
```

### 5. Configure Email Credentials
This step is required for the "Forgot Password" feature to send emails.

* Create a new file named `.env` in the root of the project.
* Add your email credentials (using a service like SendGrid):
    ```
    MAIL_USERNAME=apikey
    MAIL_PASSWORD=YOUR_SENDGRID_API_KEY
    MAIL_FROM=your_verified_email@example.com
    ```

### 6. Run the Application
You need to run the backend and frontend in two separate terminals.

* **Terminal 1: Run the Backend**
    ```bash
    uvicorn app.main:app --reload
    ```

* **Terminal 2: Run the Frontend**
    ```bash
    streamlit run frontend.py
    ```
The application will be available at `http://localhost:8501`.

### 7. Create an Admin User
To access the admin dashboard:
1.  Register a new user through the application's UI.
2.  Use a database tool like **DB Browser for SQLite** to open the `main_database.db` file.
3.  Navigate to the `users` table and change the `is_admin` value for your user from `0` to `1`.
4.  Save the changes and log in with that user. The "Admin Panel" will now be visible.
