#!/usr/bin/env python3
import argparse
import sys
import os
import signal
import time
import atexit
from pathlib import Path
from .app import main as start_app

# PID文件路径
PID_FILE = Path.home() / ".kiro2api" / "kiro2api.pid"
LOG_FILE = Path.home() / ".kiro2api" / "kiro2api.log"

def main():
    # 如果没有参数，显示自定义帮助
    if len(sys.argv) == 1:
        show_help()
        return
    
    parser = argparse.ArgumentParser(
        prog='ki2',
        description='Kiro2API - Claude Sonnet 4 OpenAI Compatible API',
        add_help=False  # 禁用默认帮助
    )
    
    # 位置参数 - 命令
    parser.add_argument(
        'command',
        nargs='?',
        choices=['start', 'stop', 'restart', 'status', 'info'],
        help='Command to execute'
    )
    
    # 可选参数
    parser.add_argument(
        '-p', '--port', 
        required=False,                 # 这个选项是可选的
        type=int,                       # 期望接收一个整数类型的值
        dest="listen_port",            # 指定存储该值的属性名为 args.program_kind
        default=8989,               # 如果没有提供该选项，则使用默认值 8989
        help='Port to run the API server on (default: 8989)'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Show version information'
    )
    
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='Show help information'
    )
    
    args = parser.parse_args()
    
    if args.help:
        show_help()
    elif args.version:
        show_version()
    elif args.command == 'start':
        port = args.listen_port
        start_daemon(port)
    elif args.command == 'stop':
        stop_daemon()
    elif args.command == 'restart':
        restart_daemon(args.listen_port)
    elif args.command == 'status':
        show_status()
    elif args.command == 'info':
        show_settings()
    else:
        show_help()

def show_help():
    """显示自定义帮助信息"""
    print()
    print("Usage: ki2 [command]")
    print()
    print("Commands:")
    print("  start         Start API server as daemon")
    print("  stop          Stop API server daemon") 
    print("  restart       Restart API server daemon")
    print("  status        Show server status and PID")
    print("  info          Show configuration information")
    print("  -v, --version Show version information")
    print("  -h, --help    Show help information")
    print()
    print("Options:")
    print("  -p, --port    Port to run the server on (default: 8989)")
    print()
    print("Examples:")
    print("  ki2 start")
    print("  ki2 start -p 9000")
    print("  ki2 status")
    print("  ki2 stop")
    print()

def restart_daemon(port: int):
    """重启守护进程"""
    print("Restarting Kiro2API daemon...")
    
    # 先停止现有进程
    if is_running():
        print("Stopping existing daemon...")
        stop_daemon()
        
        # 等待进程完全停止
        for _ in range(5):
            if not is_running():
                break
            time.sleep(1)
    
    # 启动新进程
    print("Starting daemon...")
    start_daemon(port)

def start_daemon(port: int):
    """启动守护进程"""
    # 检查是否已经在运行
    if is_running():
        print("Kiro2API is already running!")
        return
    
    # 确保目录存在
    PID_FILE.parent.mkdir(exist_ok=True)
    
    print(f"Starting Kiro2API daemon on port {port}...")
    
    # 创建守护进程
    try:
        pid = os.fork()
        if pid > 0:
            # 父进程退出
            sys.exit(0)
    except OSError:
        print("Failed to fork daemon process")
        sys.exit(1)
    
    # 子进程继续
    os.chdir("/")
    os.setsid()
    os.umask(0)
    
    # 第二次fork
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        print("Failed to fork daemon process")
        sys.exit(1)
    
    # 重定向标准输入输出
    with open('/dev/null', 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    
    with open(LOG_FILE, 'a') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())
    
    # 写入PID文件
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    # 注册退出时清理PID文件
    atexit.register(cleanup_pid_file)
    
    # 处理信号
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    print(f"Daemon started with PID {os.getpid()}")
    
    # 启动服务器
    start_app(port)

def stop_daemon():
    """停止守护进程"""
    if not PID_FILE.exists():
        print("Kiro2API is not running (no PID file found)")
        return
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # 检查进程是否存在
        try:
            os.kill(pid, 0)  # 发送信号0检查进程是否存在
        except OSError:
            print("Kiro2API is not running (process not found)")
            cleanup_pid_file()
            return
        
        # 发送TERM信号停止进程
        print(f"Stopping Kiro2API daemon (PID: {pid})...")
        os.kill(pid, signal.SIGTERM)
        
        # 等待进程结束
        for _ in range(10):  # 等待最多10秒
            try:
                os.kill(pid, 0)
                time.sleep(1)
            except OSError:
                break
        
        # 如果还没结束，强制杀死
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        
        cleanup_pid_file()
        print("Kiro2API daemon stopped")
        
    except (ValueError, FileNotFoundError):
        print("Invalid PID file")
        cleanup_pid_file()

def show_status():
    """显示守护进程状态"""
    if not PID_FILE.exists():
        print("Kiro2API Status: Not running")
        return
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # 检查进程是否存在
        try:
            os.kill(pid, 0)
            print(f"Kiro2API Status: Running")
            print(f"PID: {pid}")
            print(f"PID File: {PID_FILE}")
            print(f"Log File: {LOG_FILE}")
            
            # 显示日志的最后几行
            if LOG_FILE.exists():
                print("\nRecent log entries:")
                with open(LOG_FILE, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-5:]:  # 显示最后5行
                        print(f"  {line.rstrip()}")
        except OSError:
            print("Kiro2API Status: Not running (process not found)")
            cleanup_pid_file()
            
    except (ValueError, FileNotFoundError):
        print("Kiro2API Status: Unknown (invalid PID file)")
        cleanup_pid_file()

def is_running():
    """检查守护进程是否正在运行"""
    if not PID_FILE.exists():
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        cleanup_pid_file()
        return False

def cleanup_pid_file():
    """清理PID文件"""
    if PID_FILE.exists():
        PID_FILE.unlink()

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"Received signal {signum}, shutting down...")
    cleanup_pid_file()
    sys.exit(0)

def show_version():
    """Display current version"""
    try:
        from . import __version__
        print(f"Kiro2API Version: {__version__}")
    except ImportError:
        print("Kiro2API Version: 1.0.0")

def show_settings():
    """Display current configuration settings"""
    import os
    from pathlib import Path
    
    print("Kiro2API Configuration:")
    print("=" * 30)
    
    # Token file location
    token_path = Path.home() / ".aws/sso/cache/kiro-auth-token.json"
    print(f"Token file: {token_path}")
    print(f"Token exists: {token_path.exists()}")
    
    # Environment variables
    print(f"\nEnvironment Variables:")
    # print(f"API_KEY: {os.getenv('API_KEY', 'ki2api-key-2024')}")
    print(f"KIRO_ACCESS_TOKEN: {'Set' if os.getenv('KIRO_ACCESS_TOKEN') else 'Not set'}")
    print(f"KIRO_REFRESH_TOKEN: {'Set' if os.getenv('KIRO_REFRESH_TOKEN') else 'Not set'}")
    
    # Server info
    print(f"\nServer Configuration:")
    print(f"Host: 0.0.0.0")
    print(f"Port: 8989")
    print(f"URL: http://localhost:8989")
    
    # Daemon files
    print(f"\nDaemon Files:")
    print(f"PID File: {PID_FILE}")
    print(f"Log File: {LOG_FILE}")

if __name__ == '__main__':
    main()
    # python -m src.kiro2api.cli   
