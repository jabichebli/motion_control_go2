# utils/logger.py
import os
import time
from datetime import datetime


class RunLogger:
    """
    Creates a structured artifact directory for each training run.
    Example:
        artifacts/runs/2025-10-19_12-30-00/
            ├── checkpoints/
            ├── logs/
            ├── plots/
            └── videos/
    """

    def __init__(self, base_dir="artifacts/runs"):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.run_dir = os.path.join(base_dir, timestamp)

        # Subdirectories
        self.checkpoints_dir = os.path.join(self.run_dir, "checkpoints")
        self.logs_dir = os.path.join(self.run_dir, "logs")
        self.plots_dir = os.path.join(self.run_dir, "plots")
        self.videos_dir = os.path.join(self.run_dir, "videos")

        # Create them
        os.makedirs(self.checkpoints_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.plots_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)

        # Text log file
        self.log_file = os.path.join(self.logs_dir, "train_log.txt")

        # Write header
        with open(self.log_file, "a") as f:
            f.write(f"Run started at {timestamp}\n")
            f.write("=" * 60 + "\n")

    def log(self, message: str, console=True):
        """Write message to log file (and optionally print)."""
        timestamp = time.strftime("[%H:%M:%S]")
        formatted = f"{timestamp} {message}"
        with open(self.log_file, "a") as f:
            f.write(formatted + "\n")
        if console:
            print(formatted)

    def get_dirs(self):
        """Return dict of subdirectory paths for easy access."""
        return {
            "run_dir": self.run_dir,
            "checkpoints": self.checkpoints_dir,
            "logs": self.logs_dir,
            "plots": self.plots_dir,
            "videos": self.videos_dir,
        }