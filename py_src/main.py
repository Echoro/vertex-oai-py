import argparse
import os
import signal
import sys
import time
from pathlib import Path
import daemon
from daemon import pidfile
import uvicorn
from py_src.app import create_app

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

def start_server(daemon_mode=False, config_path="config.yaml"):
    if is_running():
        print(f"Server is already running (PID: {get_pid()})")
        return

    app, config = create_app(config_path)
    
    if daemon_mode:
        print(f"Starting server in background...")
        # Ensure log directory exists
        Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
        
        # Open log file
        log_file = open(LOG_FILE, "a")
        
        context = daemon.DaemonContext(
            pidfile=pidfile.TimeoutPIDLockFile(PID_FILE),
            stdout=log_file,
            stderr=log_file,
            working_directory=os.getcwd()
        )
        
        with context:
            uvicorn.run(app, host=config.server.host, port=config.server.port)
    else:
        # Save PID even in foreground for consistency if we want status to work
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        try:
            uvicorn.run(app, host=config.server.host, port=config.server.port)
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
        # Wait for it to stop
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
        # Default behavior: run foreground if no command
        start_server(False, args.config)

if __name__ == "__main__":
    main()
