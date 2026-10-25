import os
import time
import psutil
from typing import Dict, Any

class ResourceMonitor:
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        
    def get_process_memory_mb(self) -> float:
        """Returns the current Resident Set Size (RSS) memory of this Python process in MB."""
        try:
            mem_bytes = self.process.memory_info().rss
            return round(mem_bytes / (1024 * 1024), 2)
        except Exception:
            return 0.0

    def get_system_metrics(self) -> Dict[str, Any]:
        """Returns overall system memory and CPU utilization."""
        try:
            sys_mem = psutil.virtual_memory()
            return {
                "system_ram_gb": round(sys_mem.total / (1024 ** 3), 2),
                "ram_usage_percent": sys_mem.percent,
                "ram_available_gb": round(sys_mem.available / (1024 ** 3), 2),
                "cpu_percent": psutil.cpu_percent(interval=None),
                "process_memory_mb": self.get_process_memory_mb()
            }
        except Exception as e:
            return {
                "system_ram_gb": 16.0,
                "ram_usage_percent": 0.0,
                "ram_available_gb": 0.0,
                "cpu_percent": 0.0,
                "process_memory_mb": 0.0,
                "error": str(e)
            }

resource_monitor = ResourceMonitor()
