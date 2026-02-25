"""
KOMALAM GPU Detector
Probes for NVIDIA (CUDA) and AMD (DirectML) GPUs on Windows.
Falls back to CPU gracefully when no GPU is present.
"""

import subprocess
import platform
import json
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Suppress console window flash on Windows
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class GPUDetector:
    def __init__(self):
        self._info: Optional[dict] = None

    def detect(self) -> dict:
        """Run detection and cache the result."""
        self._info = {
            "gpus": [],
            "recommended_backend": "cpu",
            "platform": platform.system(),
            "processor": platform.processor(),
        }

        nvidia = self._detect_nvidia()
        if nvidia:
            self._info["gpus"].append(nvidia)
            self._info["recommended_backend"] = "cuda"

        amd = self._detect_amd()
        if amd:
            self._info["gpus"].append(amd)
            if not nvidia:
                self._info["recommended_backend"] = "directml"

        return self._info

    def _detect_nvidia(self) -> Optional[dict]:
        """Query nvidia-smi for GPU details."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,driver_version,temperature.gpu,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=_NO_WINDOW,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return None

            parts = result.stdout.strip().split(",")
            if len(parts) < 5:
                return None

            return {
                "name": parts[0].strip(),
                "type": "NVIDIA",
                "vram_mb": int(parts[1].strip()),
                "driver": parts[2].strip(),
                "temperature_c": int(parts[3].strip()),
                "utilization_pct": int(parts[4].strip()),
                "backend": "CUDA",
            }
        except FileNotFoundError:
            return None  # nvidia-smi not installed
        except subprocess.TimeoutExpired:
            log.warning("nvidia-smi timed out")
            return None
        except (ValueError, IndexError) as exc:
            log.warning("Failed to parse nvidia-smi output: %s", exc)
            return None

    def _detect_amd(self) -> Optional[dict]:
        """Detect AMD GPU via WMI (Windows only)."""
        try:
            result = subprocess.run(
                [
                    "powershell", "-Command",
                    "Get-WmiObject Win32_VideoController | "
                    "Where-Object { $_.Name -like '*AMD*' -or $_.Name -like '*Radeon*' } | "
                    "Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Json",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=_NO_WINDOW,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return None

            data = json.loads(result.stdout.strip())
            if isinstance(data, list):
                data = data[0]
            if not data:
                return None

            vram_bytes = data.get("AdapterRAM", 0)
            return {
                "name": data.get("Name", "AMD GPU"),
                "type": "AMD",
                "vram_mb": int(vram_bytes / (1024 * 1024)) if vram_bytes else 0,
                "driver": data.get("DriverVersion", "Unknown"),
                "temperature_c": -1,   # not available via WMI
                "utilization_pct": -1,
                "backend": "DirectML",
            }
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            log.warning("AMD WMI query timed out")
            return None
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            log.debug("AMD detection failed: %s", exc)
            return None

    def get_gpu_info(self) -> dict:
        if self._info is None:
            self.detect()
        return self._info

    def get_primary_gpu(self) -> Optional[dict]:
        info = self.get_gpu_info()
        return info["gpus"][0] if info["gpus"] else None

    def get_gpu_summary(self) -> str:
        info = self.get_gpu_info()
        if not info["gpus"]:
            return "CPU Only (No GPU detected)"

        gpu = info["gpus"][0]
        vram_gb = round(gpu["vram_mb"] / 1024, 1)
        parts = [f"{gpu['name']} ({vram_gb}GB VRAM) — {gpu['backend']}"]
        if gpu["temperature_c"] > 0:
            parts.append(f"{gpu['temperature_c']}°C")
        if gpu["utilization_pct"] >= 0:
            parts.append(f"{gpu['utilization_pct']}% util")
        return " | ".join(parts)

    def get_live_nvidia_stats(self) -> Optional[dict]:
        """Real-time stats for the resource monitor status bar widget."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=_NO_WINDOW,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return None

            parts = result.stdout.strip().split(",")
            if len(parts) < 4:
                return None
            return {
                "utilization_pct": int(parts[0].strip()),
                "memory_used_mb": int(parts[1].strip()),
                "memory_total_mb": int(parts[2].strip()),
                "temperature_c": int(parts[3].strip()),
            }
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            return None
