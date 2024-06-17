# Use a lightweight Python base image
FROM python

# Create a working directory for the application
WORKDIR /app

# Copy requirements.txt (assuming you have one)
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Set the environment variable for the Flask app entry point
ENV FLASK_APP=app.py

# Expose the port where the Flask app will run
EXPOSE 5000

# Run the Flask app in debug mode (for development)
CMD ["flask", "run", "--host", "0.0.0.0"]
