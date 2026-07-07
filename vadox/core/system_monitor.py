import psutil
import time
from PyQt6.QtCore import QThread, pyqtSignal


class SystemMonitor(QThread):
    stats_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._running = True
        self._start_time = time.time()

    def run(self):
        while self._running:
            try:
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory().percent
                disk = psutil.disk_usage('/').percent

                net = psutil.net_io_counters()
                net_kb = (net.bytes_sent + net.bytes_recv) // 1024

                try:
                    import subprocess, platform
                    kwargs = {}
                    if platform.system() == "Windows":
                        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                    result = subprocess.run(
                        ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                        capture_output=True, text=True, timeout=2, **kwargs
                    )
                    gpu = int(result.stdout.strip()) if result.returncode == 0 else 0
                except Exception:
                    gpu = 0

                uptime_secs = int(time.time() - self._start_time)
                h = uptime_secs // 3600
                m = (uptime_secs % 3600) // 60
                s = uptime_secs % 60
                uptime_str = f"{h:02d}:{m:02d}:{s:02d}"

                proc_count = len(psutil.pids())
                username = psutil.users()[0].name if psutil.users() else "USER"

                self.stats_updated.emit({
                    'cpu': cpu,
                    'mem': mem,
                    'disk': disk,
                    'gpu': gpu,
                    'net_kb': net_kb,
                    'uptime': uptime_str,
                    'procs': proc_count,
                    'user': username.upper()[:8],
                })
            except Exception:
                pass

    def stop(self):
        self._running = False
