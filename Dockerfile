# Step 1: Start with an official Python base image
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy your project's requirements file
COPY requirements.txt .

# Step 4a: Install the small, CPU-only version of PyTorch first to avoid downloading huge GPU files
RUN pip install torch --no-cache-dir --index-url https://download.pytorch.org/whl/cpu

# Step 4b: Install the rest of your app's dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy all of your project's files into the container
COPY . .

# Step 6: Expose port 8000 from the container
EXPOSE 8000

# Step 7: The command to run your specific app
# This points to the 'app' variable in your 'app/main.py' file
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]