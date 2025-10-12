# Step 1: Start with a Python image
FROM python:3.11-slim

# Step 2: Set the working directory
WORKDIR /app

# Step 3: Copy the requirements file
COPY requirements.txt .

# Step 4: Install PyTorch for CPU first, as it's a special case
RUN pip install torch --no-cache-dir --index-url https://download.pytorch.org/whl/cpu

# Step 5: Install all other dependencies from your full requirements list
RUN pip install --no-cache-dir -r requirements.txt

# Step 6: Copy ALL your project files into the container.
# This is simpler and makes sure everything, including the nlu_model, is included.
COPY . .

# Step 7: Expose the port the backend runs on
EXPOSE 8000

# Step 8: The command to start the FastAPI server, pointing to main.py inside the app folder
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

