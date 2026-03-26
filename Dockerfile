FROM mcr.microsoft.com/playwright/python:v1.42.0

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Railway port
EXPOSE 8080

# Start app with gunicorn
CMD ["gunicorn", "automation:app", "--bind", "0.0.0.0:8080"]
