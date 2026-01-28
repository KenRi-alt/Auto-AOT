FROM python:3.11-slim

WORKDIR /app

# Update pip first (important for dependency resolution)
RUN pip install --upgrade pip

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .

# Create non-root user (security best practice)
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

# Create data directory
RUN mkdir -p /home/botuser/data

# Start the bot
CMD ["python", "bot.py"]
