import argparse
import os
import signal
import sys
import time
import threading
from pathlib import Path
from collections import deque
import daemon
from daemon import pidfile
import uvicorn
from py_src.app import create_app
from py_src.config import load_config

PID_FILE = ".vertex_oai_py.pid"
LOG_FILE = "logs/vertex-oai-py.log"

def get_pid():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return None
    return None

def is_running():
    pid = get_pid()
    if pid:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    return False

def trim_log_file(file_path, max_lines):
    """高效保留文件最后 N 行"""
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            d = deque(f, max_lines)
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(d)
    except Exception as e:
        print(f"Error trimming log file: {e}")

def log_maintenance_worker(file_path, max_lines, stop_event):
    """后台日志维护线程"""
    while not stop_event.is_set():
        trim_log_file(file_path, max_lines)
        # 每 60 秒检查一次
        for _ in range(60):
            if stop_event.is_set():
                break
            time.sleep(1)

def start_server(daemon_mode=False, config_path="config.yaml"):
    if is_running():
        print(f"Server is already running (PID: {get_pid()})")
        return

    config = load_config(config_path)
    app, _ = create_app(config_path)
    
    # 准备日志目录
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    stop_event = threading.Event()
    
    def run_uvicorn():
        # 启动日志清理线程
        if config.server.log_to_file:
            maintenance_thread = threading.Thread(
                target=log_maintenance_worker, 
                args=(LOG_FILE, config.server.max_log_lines, stop_event),
                daemon=True
            )
            maintenance_thread.start()
            
        try:
            uvicorn.run(app, host=config.server.host, port=config.server.port, log_level="info")
        finally:
            stop_event.set()

    if daemon_mode:
        print(f"Starting server in background...")
        
        # 处理日志输出重定向
        if config.server.log_to_file:
            log_out = open(LOG_FILE, "a", buffering=1)
        else:
            log_out = open(os.devnull, "w")
            
        context = daemon.DaemonContext(
            pidfile=pidfile.TimeoutPIDLockFile(PID_FILE),
            stdout=log_out,
            stderr=log_out,
            working_directory=os.getcwd()
        )
        
        with context:
            run_uvicorn()
    else:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        try:
            run_uvicorn()
        finally:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)

def stop_server():
    pid = get_pid()
    if not pid:
        print("Server is not running")
        return

    print(f"Stopping server (PID: {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(50):
            time.sleep(0.1)
            if not is_running():
                print("Server stopped")
                if os.path.exists(PID_FILE):
                    os.remove(PID_FILE)
                return
        
        print("Server didn't stop in time, killing...")
        os.kill(pid, signal.SIGKILL)
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except OSError as e:
        print(f"Error stopping server: {e}")

def main():
    parser = argparse.ArgumentParser(description="Vertex-OAI Python Gateway")
    parser.add_argument("command", choices=["start", "stop", "restart", "status"], nargs="?", default=None)
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--foreground", action="store_true", help="Run in foreground")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start_server(not args.foreground, args.config)
    elif args.command == "stop":
        stop_server()
    elif args.command == "restart":
        stop_server()
        time.sleep(1)
        start_server(not args.foreground, args.config)
    elif args.command == "status":
        if is_running():
            print(f"Server is running (PID: {get_pid()})")
        else:
            print("Server is not running")
    else:
        start_server(False, args.config)

if __name__ == "__main__":
    main()
