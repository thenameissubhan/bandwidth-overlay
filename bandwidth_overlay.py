import sys
import psutil
import configparser
import subprocess
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont
from collections import deque
import os

CONFIG_FILE = "position.cfg"

class BandwidthOverlay(QLabel):
    def __init__(self):
        super().__init__()
        
        # Make window frameless, always on top, and transparent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set default font style
        self.setFont(QFont("Arial", 14))

        # Default draggable state and load saved settings
        self.draggable = True  # Default is draggable
        self.load_settings()

        # Store previous counters for real-time bandwidth calculation
        self.last_received, self.last_sent = psutil.net_io_counters().bytes_recv, psutil.net_io_counters().bytes_sent

        # Smoother real-time tracking (store last 5 readings)
        self.download_speeds = deque(maxlen=5)
        self.upload_speeds = deque(maxlen=5)

        # Ping tracking
        self.high_ping = None

        # Draggable feature variables
        self.drag_position = QPoint()

        # Start real-time updates
        self.update_speed()
        self.update_ping()

        # Show overlay window
        self.show()
        self.raise_()  
        self.activateWindow()

    def update_speed(self):
        counters = psutil.net_io_counters()

        # Calculate real-time bandwidth usage (difference per second)
        download_speed = (counters.bytes_recv - self.last_received) * 8 / 1_000_000
        upload_speed = (counters.bytes_sent - self.last_sent) * 8 / 1_000_000

        # Update counters for next measurement
        self.last_received, self.last_sent = counters.bytes_recv, counters.bytes_sent

        # Append speeds for smoothing
        self.download_speeds.append(download_speed)
        self.upload_speeds.append(upload_speed)

        # Calculate average speeds
        avg_download = sum(self.download_speeds) / len(self.download_speeds)
        avg_upload = sum(self.upload_speeds) / len(self.upload_speeds)

        # Construct overlay text with ping if high
        ping_text = f' | <span style="color:red; font-weight:bold;">PING {self.high_ping:.0f}ms</span>' if self.high_ping else ''
        self.setText(
            f'<span style="font-weight:600;">DL</span> <span style="font-weight:bold;">{avg_download:.1f}</span>  |  '
            f'<span style="font-weight:600;">UL</span> <span style="font-weight:bold;">{avg_upload:.1f}</span>{ping_text}'
        )
        self.setStyleSheet("color: white; font-size: 14px;")
        self.adjustSize()

        # Update every 1 second
        QTimer.singleShot(1000, self.update_speed)

    def update_ping(self):
        """Check ping using the system ping command without showing a CMD window."""
        try:
            output = subprocess.run(
                ["ping", "-n", "1", "8.8.8.8"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW  # Prevents CMD window from appearing
            )
            if "time=" in output.stdout:
                latency = int(output.stdout.split("time=")[1].split("ms")[0])
                self.high_ping = latency if latency > 150 else None
            else:
                self.high_ping = None
        except Exception:
            self.high_ping = None

        # Update every 1 seconds
        QTimer.singleShot(1000, self.update_ping)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.draggable:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.draggable:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Save position when user stops dragging."""
        self.save_settings()

    def mouseDoubleClickEvent(self, event):
        """Lock/unlock position on double click."""
        if event.button() == Qt.LeftButton:
            self.draggable = False  # Lock position
        elif event.button() == Qt.RightButton:
            self.draggable = True   # Unlock position
        self.save_settings()

    def save_settings(self):
        """Save the overlay's position and lock state to a config file."""
        config = configparser.ConfigParser()
        config["SETTINGS"] = {
            "x": str(self.x()),
            "y": str(self.y()),
            "draggable": str(int(self.draggable))  # 1 for True (draggable), 0 for False
        }
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)

    def load_settings(self):
        """Load saved position and lock state from the config file."""
        if os.path.exists(CONFIG_FILE):
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            try:
                x = int(config["SETTINGS"]["x"])
                y = int(config["SETTINGS"]["y"])
                self.draggable = bool(int(config["SETTINGS"]["draggable"]))
                self.move(x, y)
            except (KeyError, ValueError):
                self.move(1100, 20)  # Default position if error occurs
        else:
            self.move(1100, 20)  # Default position if config doesn't exist

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = BandwidthOverlay()
    sys.exit(app.exec_())
