# ============================================
# FAMILY TREE BOT - COMPLETE DOCKERFILE
# Works on Railway with all files
# ============================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# 1. Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Upgrade pip
RUN pip install --upgrade pip

# 3. Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. COPY ALL FILES - This is what you were missing!
# Copy main Python files
COPY bot.py .
COPY config.py .
COPY database.py .
COPY images.py .

# Copy handlers directory
COPY handlers/ ./handlers/

# Copy utils directory
COPY utils/ ./utils/

# 5. Create data directory (for persistent database)
RUN mkdir -p /data && chmod 777 /data

# 6. Verify all files are copied
RUN echo "📁 Checking files..." && \
    ls -la && \
    echo "📂 Checking handlers..." && \
    ls -la handlers/ && \
    echo "📂 Checking utils..." && \
    ls -la utils/

# 7. Run as non-root user for security
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# 8. Start the bot
CMD ["python", "bot.py"]
