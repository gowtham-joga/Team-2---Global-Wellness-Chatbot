# /frontend/Dockerfile

# Step 1: Start with a Python image
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy the main requirements file from the parent directory
# The '../' goes up one level to find the file
COPY requirements.txt .

# Step 4: Install all the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy your frontend code (everything in this folder) into the container
COPY . .

# Step 6: Expose the default port for Streamlit
EXPOSE 8501

# Step 7: The command to start the Streamlit server
CMD ["streamlit", "run", "frontend.py", "--server.port=8501", "--server.address=0.0.0.0"]