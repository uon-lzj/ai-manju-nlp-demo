"""公共云启动入口：保留Streamlit，在平台指定端口监听。"""
import os
import sys
import subprocess
from pathlib import Path


def server_args():
    port = int(os.environ.get('PORT', '8501'))
    if not 1 <= port <= 65535:
        raise ValueError('PORT must be between 1 and 65535')
    return [sys.executable, '-m', 'streamlit', 'run', str(Path(__file__).with_name('app.py')),
            '--server.address', '0.0.0.0', '--server.port', str(port),
            '--server.headless', 'true', '--browser.gatherUsageStats', 'false']


if __name__ == '__main__':
    if os.name == 'nt':
        sys.exit(subprocess.call(server_args()))
    else:
        os.execv(sys.executable, server_args())
