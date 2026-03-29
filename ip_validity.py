import requests
import os
import time
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal

# --- 关键配置 ---
CONFIG = {
    'timeout_alive': 5,      # 存活检测稍微放宽一点
    'timeout_speed': 10,     
    'max_workers_scan': 30,  # 稍微调低并发，防止有些服务器并发限制
    'max_workers_speed': 3,  
    'ip_dir': 'py/fofa/ip',
    'download_size': 1024 * 1024, 
}

shutdown_flag = False
def signal_handler(signum, frame):
    global shutdown_flag
    shutdown_flag = True
    print("\n[!] 正在停止...")

signal.signal(signal.SIGINT, signal_handler)

class IPTVTester:
    def check_alive(self, ip: str, stream: str) -> Tuple[bool, str]:
        """第一阶段修复：改用 GET 请求并立即关闭，确保兼容性"""
        url = f"http://{ip}/{stream}"
        try:
            # 改回 GET，设置 stream=True 避免下载整个视频，只取响应头就停
            with requests.get(url, timeout=CONFIG['timeout_alive'], stream=True, allow_redirects=True) as resp:
                if resp.status_code == 200:
                    return True, ""
                return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, "连接超时/失败"

    def get_speed(self, ip: str, stream: str) -> float:
        """第二阶段：下载采样测速"""
        url = f"http://{ip}/{stream}"
        try:
            start = time.time()
            with requests.get(url, timeout=CONFIG['timeout_speed'], stream=True) as r:
                if r.status_code != 200: return 0
                # 实际读取 1MB 数据
                data = r.raw.read(CONFIG['download_size'])
                if not data: return 0
                elapsed = time.time() - start
                return (len(data) / 1024) / elapsed
        except:
            return 0

    def process_operator(self, city: str, streams: List[str]):
        print(f"\n\n{'█'*10} 运营商分类测试: 【{city}】 {'█'*10}")
        
        ip_file = os.path.join(CONFIG['ip_dir'], f"{city}.txt")
        if not os.path.exists(ip_file):
            print(f"  [!] 跳过：未找到 {ip_file}")
            return

        # 增加容错处理：读取并清洗 IP 列表
        all_ips = []
        with open(ip_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    all_ips.append(line.split('#')[0].strip())
        all_ips = list(set(all_ips))

        print(f"  [1/2] 正在进行存活海选 (总数: {len(all_ips)})...")
        alive_ips = []
        
        # --- 第一阶段：存活预检 ---
        with ThreadPoolExecutor(max_workers=CONFIG['max_workers_scan']) as scan_exec:
            future_to_ip = {scan_exec.submit(self.check_alive, ip, streams[0]): ip for ip in all_ips}
            for future in as_completed(future_to_ip):
                if shutdown_flag: break
                ip = future_to_ip[future]
                is_alive, reason = future.result()
                if is_alive:
                    print(f"    [✔] 存活: {ip}")
                    alive_ips.append(ip)
                # 如需调试，可打开下面这行查看为什么失败
                # else: print(f"    [✘] 失败: {ip} {reason}")

        if not alive_ips:
            print(f"  [!] {city} 海选结束，无存活IP。")
            return

        print(f"\n  [2/2] 正在对存活的 {len(alive_ips)} 个IP进行深度测速...")
        final_results = []

        # --- 第二阶段：精准测速 ---
        with ThreadPoolExecutor(max_workers=CONFIG['max_workers_speed']) as speed_exec:
            future_to_speed = {speed_exec.submit(self.get_speed, ip, streams[0]): ip for ip in alive_ips}
            for future in as_completed(future_to_speed):
                if shutdown_flag: break
                ip = future_to_speed[future]
                speed = future.result()
                if speed > 0:
                    print(f"    [★] 测速成功: {ip:<20} | 速度: {speed:>8.2f} KB/s")
                    final_results.append((ip, speed))
                else:
                    print(f"    [×] 测速失败: {ip}")

        # 结果持久化
        if final_results:
            final_results.sort(key=lambda x: x[1], reverse=True)
            res_path = os.path.join(CONFIG['ip_dir'], f"{city}_result_ip.txt")
            with open(res_path, 'w', encoding='utf-8') as f:
                for ip, speed in final_results:
                    f.write(f"{ip} # {speed:.2f}KB/s\n")
            print(f"\n  [完成] {city} 保存 {len(final_results)} 个有效地址")

def main():
    CITY_STREAMS = {
    "安徽电信": ["rtp/238.1.78.150:7072"],
    "安徽联通": ["rtp/238.1.78.150:7072"],    
    "云南电信": ["rtp/239.200.200.145:8840"],
    "内蒙古电信": ["rtp/239.29.0.2:5000"],
    "吉林电信": ["rtp/239.37.0.125:5540"],
    "吉林联通": ["rtp/239.253.142.160:3000"],    
    "宁夏电信": ["rtp/239.121.4.94:8538"],
    "山东电信": ["rtp/239.21.1.87:5002"],
    "山东联通": ["rtp/239.253.254.78:8000"],
    "山西电信": ["rtp/239.1.1.7:8007"],
    "山西联通": ["rtp/226.0.2.152:9128"],
    "新疆电信": ["rtp/238.125.3.174:5140"],
    "江西电信": ["rtp/239.252.220.63:5140"],
    "河北电信": ["rtp/239.254.200.174:6000"],
    "河南电信": ["rtp/239.16.20.21:10210"],    
    "河南联通": ["rtp/225.1.4.98:1127"],
    "浙江联通": ["rtp/233.50.201.118:5140"],    
    "海南电信": ["rtp/239.253.64.253:5140"],
    "海南联通": ["rtp/239.254.96.82:7640"],    
    "湖北电信": ["rtp/239.254.96.96:8550"],
    "湖北联通": ["rtp/228.0.0.1:6108"],
    "湖南电信": ["rtp/239.76.253.101:9000"],
    "甘肃电信": ["rtp/239.255.30.249:8231"],
    "福建电信": ["rtp/239.61.2.132:8708"],
    "贵州电信": ["rtp/238.255.2.1:5999"],
    "辽宁联通": ["rtp/232.0.0.27:1234"],
    "陕西电信": ["rtp/239.112.205.78:5140"],
    "青海电信": ["rtp/239.120.1.64:8332"],
    "黑龙江联通": ["rtp/229.58.190.150:5000"],
    }

    tester = IPTVTester()
    os.makedirs(CONFIG['ip_dir'], exist_ok=True)

    for city, streams in CITY_STREAMS.items():
        if shutdown_flag: break
        tester.process_operator(city, streams)

if __name__ == "__main__":
    main()