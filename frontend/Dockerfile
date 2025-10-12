# Step 1: Start with a Python image
FROM python:3.11-slim

# Step 2: Set the working directory
WORKDIR /app

# Step 3: Copy the frontend's requirements file
COPY requirements.txt .

# Step 4: Install the frontend's dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the frontend's code
COPY . .

# Step 6: Expose the Streamlit port
EXPOSE 8501

# Step 7: The command to start the Streamlit server
CMD ["streamlit", "run", "frontend.py", "--server.port=8501", "--server.address=0.0.0.0"]
