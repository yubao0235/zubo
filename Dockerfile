FROM python:3.11-slim

WORKDIR /app

# 设置环境
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1

# 1. 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 【关键步骤】复制整个项目，包括 py 文件夹及其内容
COPY . .

# 3. 运行脚本
CMD ["python", "-u", "ip_validity.py"]
