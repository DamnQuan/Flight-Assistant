# 使用 Python 官方镜像[reference:15]
FROM python:3.13-slim

# 设置工作目录[reference:16]
WORKDIR /app

# 复制依赖文件并安装[reference:17]
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件[reference:18]
COPY . .

# 暴露 Flask 默认端口[reference:19]
EXPOSE 5000

# 使用 Gunicorn 启动[reference:20]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]