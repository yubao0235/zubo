# 使用官方轻量版 Python
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置时区和不缓冲输出（为了实时看到日志）
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制脚本到容器
COPY ip_validity.py .

# 启动命令
CMD ["python", "-u", "ip_validity.py"]
