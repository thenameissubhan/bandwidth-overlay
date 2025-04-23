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

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFont(QFont("Arial", 14))

        self.draggable = True
        self.load_settings()

        # Trackers
        self.last_received = 0
        self.last_sent = 0
        self.download_speeds = deque(maxlen=10)  # Increased moving average size to 10 (was 5)
        self.upload_speeds = deque(maxlen=10)  # Increased moving average size to 10 (was 5)
        self.high_ping = None
        self.drag_position = QPoint()

        self.update_speed()
        self.update_ping()

        self.show()
        self.raise_()
        self.activateWindow()

    def update_speed(self):
        preferred_interfaces = ["Ethernet", "Wi-Fi", "wlan0", "eth0"]
        net_io = psutil.net_io_counters(pernic=True)

        download_total = 0
        upload_total = 0

        # Aggregate network stats for preferred interfaces
        for name, stats in net_io.items():
            if any(pref in name for pref in preferred_interfaces):
                download_total += stats.bytes_recv
                upload_total += stats.bytes_sent

        # Calculate download/upload speeds
        download_speed = (download_total - self.last_received) * 8 / 1_000_000
        upload_speed = (upload_total - self.last_sent) * 8 / 1_000_000

        # Update trackers
        self.last_received, self.last_sent = download_total, upload_total

        # Add speeds to history for moving average
        self.download_speeds.append(download_speed)
        self.upload_speeds.append(upload_speed)

        # Calculate average speeds
        avg_download = sum(self.download_speeds) / len(self.download_speeds)
        avg_upload = sum(self.upload_speeds) / len(self.upload_speeds)

        # Ping information
        ping_text = f' | <span style="color:red; font-weight:bold;">PING {self.high_ping:.0f}ms</span>' if self.high_ping else ''
        self.setText(
            f'<span style="font-weight:600;">DL</span> <span style="font-weight:bold;">{avg_download:.1f}</span>  |  '
            f'<span style="font-weight:600;">UL</span> <span style="font-weight:bold;">{avg_upload:.1f}</span>{ping_text}'
        )
        self.setStyleSheet("color: white; font-size: 14px;")
        self.adjustSize()

        # Update every 500ms instead of 1000ms for faster detection
        QTimer.singleShot(500, self.update_speed)  # Changed update interval to 500ms

    def update_ping(self):
        try:
            output = subprocess.run(
                ["ping", "-n", "1", "8.8.8.8"],  # Ping Google's DNS
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if "time=" in output.stdout:
                latency = int(output.stdout.split("time=")[1].split("ms")[0])
                self.high_ping = latency if latency > 150 else None
            else:
                self.high_ping = None
        except Exception:
            self.high_ping = None

        # Update ping every 500ms to get faster detection
        QTimer.singleShot(500, self.update_ping)  # Changed ping update interval to 500ms

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.draggable:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.draggable:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.save_settings()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.draggable = False
        elif event.button() == Qt.RightButton:
            self.draggable = True
        self.save_settings()

    def save_settings(self):
        config = configparser.ConfigParser()
        config["SETTINGS"] = {
            "x": str(self.x()),
            "y": str(self.y()),
            "draggable": str(int(self.draggable))
        }
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            try:
                x = int(config["SETTINGS"]["x"])
                y = int(config["SETTINGS"]["y"])
                self.draggable = bool(int(config["SETTINGS"]["draggable"]))
                self.move(x, y)
            except (KeyError, ValueError):
                self.move(1100, 20)
        else:
            self.move(1100, 20)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = BandwidthOverlay()
    sys.exit(app.exec_())
