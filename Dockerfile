FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run db_init.py to ensure databases are created, then start Gunicorn
# Render expects the server to listen on port 10000 by default (or the PORT env var)
# We bind to 0.0.0.0 to allow external access
CMD sh -c "python db_init.py && gunicorn app:app --bind 0.0.0.0:10000"
