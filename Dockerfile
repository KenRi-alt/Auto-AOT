FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .
COPY .env.example .env.example

# Run as non-root (optional but recommended)
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

# Start the bot
CMD ["python", "bot.py"]
