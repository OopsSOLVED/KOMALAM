"""
KOMALAM Resource Monitor
Status-bar widget showing live CPU, RAM, and GPU utilisation.
"""

import psutil
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar, QFrame
from PyQt5.QtCore import QTimer
from typing import Optional


class ResourceMonitor(QFrame):
    """Compact system resource display, refreshes every 2 s."""

    REFRESH_MS = 2000

    def __init__(self, gpu_detector=None, parent=None):
        super().__init__(parent)
        self.setObjectName("resource_frame")
        self.gpu_detector = gpu_detector
        self._setup_ui()
        self._start_timer()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(12)

        self.cpu_label = QLabel("CPU: --")
        self.cpu_label.setObjectName("resource_label")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setObjectName("resource_bar")
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setFixedWidth(60)
        self.cpu_bar.setTextVisible(False)
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.cpu_bar)

        sep1 = QLabel("│")
        sep1.setObjectName("resource_label")
        layout.addWidget(sep1)

        self.ram_label = QLabel("RAM: --")
        self.ram_label.setObjectName("resource_label")
        self.ram_bar = QProgressBar()
        self.ram_bar.setObjectName("resource_bar")
        self.ram_bar.setRange(0, 100)
        self.ram_bar.setFixedWidth(60)
        self.ram_bar.setTextVisible(False)
        layout.addWidget(self.ram_label)
        layout.addWidget(self.ram_bar)

        sep2 = QLabel("│")
        sep2.setObjectName("resource_label")
        layout.addWidget(sep2)

        self.gpu_label = QLabel("GPU: N/A")
        self.gpu_label.setObjectName("resource_label")
        layout.addWidget(self.gpu_label)

    def _start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_stats)
        self.timer.start(self.REFRESH_MS)
        self._update_stats()

    def _update_stats(self):
        try:
            cpu_pct = psutil.cpu_percent(interval=0)
            self.cpu_label.setText(f"CPU: {cpu_pct:.0f}%")
            self.cpu_bar.setValue(int(cpu_pct))

            ram = psutil.virtual_memory()
            ram_used_gb = ram.used / (1024 ** 3)
            ram_total_gb = ram.total / (1024 ** 3)
            self.ram_label.setText(f"RAM: {ram_used_gb:.1f}/{ram_total_gb:.0f}GB")
            self.ram_bar.setValue(int(ram.percent))

            if self.gpu_detector:
                gpu_stats = self.gpu_detector.get_live_nvidia_stats()
                if gpu_stats:
                    util = gpu_stats["utilization_pct"]
                    mem_used = gpu_stats["memory_used_mb"] / 1024
                    mem_total = gpu_stats["memory_total_mb"] / 1024
                    temp = gpu_stats["temperature_c"]
                    self.gpu_label.setText(
                        f"GPU: {util}% | {mem_used:.1f}/{mem_total:.0f}GB | {temp}°C"
                    )
                else:
                    gpu = self.gpu_detector.get_primary_gpu()
                    if gpu and gpu["type"] == "AMD":
                        self.gpu_label.setText(f"GPU: {gpu['name']}")
                    else:
                        self.gpu_label.setText("GPU: N/A")
        except Exception:
            pass  # non-critical UI widget — don't crash the app

    def stop(self):
        if self.timer:
            self.timer.stop()
