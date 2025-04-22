FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libxshmfence1 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb \
    && apt-get update && apt install -y ./chrome.deb \
    && rm chrome.deb

# Set environment variable so Selenium can find Chrome
ENV CHROME_BIN=/usr/bin/google-chrome

# Set working directory
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start the app
CMD ["gunicorn", "app.index:app"]