# Docker Hub 官方镜像（通过 daemon.json 镜像代理加速）
FROM python:3.12-slim

WORKDIR /app

# pip 使用阿里云 PyPI 镜像加速
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && pip config set global.trusted-host mirrors.aliyun.com

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["daily-fortune-mcp", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
