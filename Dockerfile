# 使用轻量级的 Python 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1

# 安装依赖（使用清华源加速）
RUN pip install --no-cache-dir requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# 将当前目录下的所有文件复制到容器中
COPY . .

# 容器启动时运行脚本
# 使用 -u 参数确保日志实时输出到 Docker 控制台
CMD ["python", "-u", "ip_validity.py"]
