FROM python:3.12.4

WORKDIR /app

# Install necessary dependencies
RUN apt -y update && \
    apt -y install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    libatspi2.0-0 libxshmfence1 && \
    python -m pip install --upgrade pip && \
    pip install pyppeteer Pillow asyncio aiohttp opencv-python-headless ddddocr quart && \
    rm -rf /var/lib/apt/lists/*

COPY ./docker/ ./
# Expose the port
EXPOSE 12345

# Run the application
CMD ["python", "api.py"]