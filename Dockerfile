# 使用更小的alpine基础镜像
FROM python:3.12.4-alpine

WORKDIR /app

# 安装必要的系统依赖和Python包，并清理缓存以减少镜像大小
RUN apk add --no-cache \
    libnss libatk libxkbcommon libxcomposite libxdamage libxrandr libasound libxshmfence \
    gcc musl-dev && \
    python -m pip install --upgrade pip && \
    pip install --no-cache-dir pyppeteer Pillow asyncio aiohttp opencv-python-headless ddddocr quart requests hypercorn apscheduler && \
    apk del gcc musl-dev && \
    rm -rf /var/cache/apk/*

    
# 复制必要的文件
COPY ./docker/ ./

# 暴露端口
EXPOSE 12345

# 运行应用程序
CMD ["hypercorn", "api:app", "--bind", "0.0.0.0:12345"]
