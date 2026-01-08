from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QFrame, QGridLayout,
                             QLineEdit, QSpinBox, QDialog, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QConicalGradient
import pyqtgraph as pg
import pandas as pd
from datetime import datetime

# --- Temperature monitoring system Style Constants ---
COLOR_BG = "#050510"
COLOR_PANEL = "#101020"
COLOR_CYAN = "#00F0FF"
COLOR_RED = "#FF0040"
COLOR_DIM = "#202040"
FONT_MAIN = "Consolas"

STYLESHEET = f"""
    QMainWindow {{ background-color: {COLOR_BG}; }}
    QWidget {{ color: {COLOR_CYAN}; font-family: {FONT_MAIN}; }}
    QFrame {{ background-color: {COLOR_PANEL}; border: 1px solid {COLOR_DIM}; border-radius: 5px; }}
    QPushButton {{ 
        background-color: {COLOR_DIM}; border: 1px solid {COLOR_CYAN}; 
        color: {COLOR_CYAN}; padding: 5px; font-weight: bold;
    }}
    QPushButton:hover {{ background-color: {COLOR_CYAN}; color: {COLOR_BG}; }}
    QTextEdit {{ background-color: {COLOR_BG}; border: none; color: {COLOR_CYAN}; }}
    QLabel {{ border: none; }}
"""

class LogViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History Log Viewer")
        self.resize(800, 600)
        self.setStyleSheet(f"background-color: {COLOR_BG}; color: {COLOR_CYAN};")
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: {COLOR_PANEL}; gridline-color: {COLOR_DIM}; }}
            QHeaderView::section {{ background-color: {COLOR_DIM}; color: white; padding: 4px; border: 1px solid {COLOR_BG}; }}
            QTableCornerButton::section {{ background-color: {COLOR_DIM}; }}
        """)
        layout.addWidget(self.table)
        
    def load_csv(self, filename):
        try:
            df = pd.read_csv(filename)
            self.table.setRowCount(len(df))
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels(df.columns)
            
            for r in range(len(df)):
                for c, val in enumerate(df.iloc[r]):
                    item = QTableWidgetItem(str(val))
                    self.table.setItem(r, c, item)
            
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        except Exception as e:
            print(f"Error loading CSV: {e}")

class GaugeWidget(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = 0.0
        self.is_alarm = False
        self.setMinimumSize(150, 150)

    def update_value(self, val, alarm=False):
        self.value = val
        self.is_alarm = alarm
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        center = self.rect().center()
        radius = min(w, h) / 2 - 10
        
        # Draw Background Ring
        pen = QPen(QColor(COLOR_DIM))
        pen.setWidth(10)
        painter.setPen(pen)
        painter.drawEllipse(center, int(radius), int(radius))
        
        # Draw Active Arc
        # Normalize 0-120C to 0-270 degrees
        start_angle = 225 * 16
        span_angle = - (self.value / 120.0) * 270 * 16
        
        color = QColor(COLOR_RED) if self.is_alarm else QColor(COLOR_CYAN)
        pen.setColor(color)
        painter.setPen(pen)
        painter.drawArc(self.rect().adjusted(10,10,-10,-10), start_angle, int(span_angle))
        
        # Text
        painter.setPen(color)
        painter.setFont(QFont(FONT_MAIN, 20, QFont.Weight.Bold))
        text = f"{self.value:.1f}°C"
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text)
        painter.drawText(int(center.x() - tw/2), int(center.y() + 10), text)
        
        painter.setFont(QFont(FONT_MAIN, 10))
        painter.setPen(QColor("white"))
        tw = painter.fontMetrics().horizontalAdvance(self.title)
        painter.drawText(int(center.x() - tw/2), int(center.y() + 30), self.title)

class DashboardUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.history_data = []

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Top Bar: Status + Title
        top_bar = QHBoxLayout()
        self.status_led = QLabel("●")
        self.status_led.setStyleSheet("color: red; font-size: 20px;")
        self.status_label = QLabel("DISCONNECTED")
        top_bar.addWidget(self.status_led)
        top_bar.addWidget(self.status_label)
        top_bar.addStretch()
        title = QLabel("Temperature monitoring system")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        top_bar.addWidget(title)
        
        # Settings Bar
        settings_bar = QHBoxLayout()
        settings_bar.setContentsMargins(0, 10, 0, 10)
        
        lbl_ip = QLabel("IP:")
        lbl_ip.setStyleSheet("color: white; font-weight: bold;")
        self.ip_input = QLineEdit("192.168.1.100")
        self.ip_input.setStyleSheet(f"background-color: {COLOR_DIM}; color: {COLOR_CYAN}; border: 1px solid {COLOR_CYAN}; padding: 3px;")
        
        lbl_sensors = QLabel("SENSORS:")
        lbl_sensors.setStyleSheet("color: white; font-weight: bold; margin-left: 10px;")
        self.sensor_spin = QSpinBox()
        self.sensor_spin.setRange(1, 3)
        self.sensor_spin.setValue(3)
        self.sensor_spin.setStyleSheet(f"background-color: {COLOR_DIM}; color: {COLOR_CYAN}; border: 1px solid {COLOR_CYAN}; padding: 3px;")

        lbl_alarm = QLabel("ALARM LIMIT:")
        lbl_alarm.setStyleSheet("color: white; font-weight: bold; margin-left: 10px;")
        self.alarm_spin = QSpinBox()
        self.alarm_spin.setRange(0, 150)
        self.alarm_spin.setValue(100)
        self.alarm_spin.setStyleSheet(f"background-color: {COLOR_DIM}; color: {COLOR_RED}; border: 1px solid {COLOR_RED}; padding: 3px;")
        
        self.btn_connect = QPushButton("CONNECT / UPDATE")
        self.btn_connect.setFixedWidth(150)

        settings_bar.addWidget(lbl_ip)
        settings_bar.addWidget(self.ip_input)
        settings_bar.addWidget(lbl_sensors)
        settings_bar.addWidget(self.sensor_spin)
        settings_bar.addWidget(lbl_alarm)
        settings_bar.addWidget(self.alarm_spin)
        settings_bar.addWidget(self.btn_connect)
        settings_bar.addStretch()

        layout.addLayout(top_bar)
        layout.addLayout(settings_bar)
        
        # Gauges
        gauges_layout = QHBoxLayout()
        self.gauge1 = GaugeWidget("SENSOR 1")
        self.gauge2 = GaugeWidget("SENSOR 2")
        self.gauge3 = GaugeWidget("SENSOR 3")
        gauges_layout.addWidget(self.gauge1)
        gauges_layout.addWidget(self.gauge2)
        gauges_layout.addWidget(self.gauge3)
        layout.addLayout(gauges_layout)
        
        # Graph
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground(COLOR_BG)
        self.graph_widget.setTitle("THERMAL HISTORY (60s)", color=COLOR_CYAN)
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        self.graph_widget.setYRange(0, 130) # Fixed Range
        
        # Alarm Line
        self.alarm_line = pg.InfiniteLine(pos=100, angle=0, pen=pg.mkPen(COLOR_RED, width=1, style=Qt.PenStyle.DashLine))
        self.graph_widget.addItem(self.alarm_line)

        self.curve1 = self.graph_widget.plot(pen=pg.mkPen(COLOR_CYAN, width=2))
        self.curve2 = self.graph_widget.plot(pen=pg.mkPen('m', width=2))
        self.curve3 = self.graph_widget.plot(pen=pg.mkPen('y', width=2))
        layout.addWidget(self.graph_widget)
        
        # Bottom Panel: Log + Controls
        bottom_layout = QHBoxLayout()
        
        log_frame = QFrame()
        log_layout = QVBoxLayout(log_frame)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(QLabel("EVENT LOG"))
        log_layout.addWidget(self.log_text)
        bottom_layout.addWidget(log_frame, stretch=2)
        
        ctrl_frame = QFrame()
        ctrl_layout = QVBoxLayout(ctrl_frame)
        
        btn_layout = QHBoxLayout()
        btn_export = QPushButton("EXPORT CSV")
        btn_export.clicked.connect(self.export_csv)
        btn_history = QPushButton("BROWSE LOGS")
        btn_history.clicked.connect(self.view_history)
        btn_layout.addWidget(btn_export)
        btn_layout.addWidget(btn_history)
        
        ctrl_layout.addWidget(QLabel("CONTROLS"))
        ctrl_layout.addLayout(btn_layout)
        ctrl_layout.addStretch()
        bottom_layout.addWidget(ctrl_frame, stretch=1)
        
        layout.addLayout(bottom_layout)

    def update_connection(self, connected):
        color = "#00FF00" if connected else "red"
        text = "CONNECTED" if connected else "DISCONNECTED"
        self.status_led.setStyleSheet(f"color: {color}; font-size: 20px;")
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")
        if connected:
            self.log_message("System Connected.")
        else:
            self.log_message("System Disconnected.")

    def log_message(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {msg}")

    def update_data(self, data):
        # Data format: {"t1": x, "t2": x, "t3": x, "alarm": bool (hardware)}
        t1, t2, t3 = data.get("t1", 0), data.get("t2", 0), data.get("t3", 0)
        
        # Logic: Use User defined alarm limit
        limit = self.alarm_spin.value()
        self.alarm_line.setPos(limit)
        
        # Determine Alarm State locally based on limit
        alarm = (t1 > limit) or (t2 > limit) or (t3 > limit)
        
        now = datetime.now()
        self.history_data.append({"time": now, "t1": t1, "t2": t2, "t3": t3, "alarm": alarm})
        
        # Trim history (keep last 60s roughly, assume 2s interval -> 30 samples, or just crop by time)
        # Simple count-based cropping for rolling window
        if len(self.history_data) > 60: 
            self.history_data.pop(0)

        # Update Gauges
        self.gauge1.update_value(t1, t1 > limit)
        self.gauge2.update_value(t2, t2 > limit)
        self.gauge3.update_value(t3, t3 > limit)

        if alarm:
            if not getattr(self, "last_alarm_state", False):
                self.log_message("!!! ALARM TRIGGERED !!!")
            self.last_alarm_state = True
        else:
            self.last_alarm_state = False

        # Update Graph
        times = [x for x in range(len(self.history_data))]
        d1 = [x["t1"] for x in self.history_data]
        d2 = [x["t2"] for x in self.history_data]
        d3 = [x["t3"] for x in self.history_data]
        
        self.curve1.setData(times, d1)
        self.curve2.setData(times, d2)
        self.curve3.setData(times, d3)

    def set_gauge_count(self, count):
        self.gauge1.setVisible(count >= 1)
        self.gauge2.setVisible(count >= 2)
        self.gauge3.setVisible(count >= 3)
        
        # Update graph to hide missing curves if desired (optional)
        self.curve1.setVisible(count >= 1)
        self.curve2.setVisible(count >= 2)
        self.curve3.setVisible(count >= 3)

    def export_csv(self):
        self._save_csv_file(f"thermal_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    def auto_save_log(self):
        if self.history_data:
            self._save_csv_file(f"autosave_thermal_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", silent=True)

    def _save_csv_file(self, filename, silent=False):
        if not self.history_data:
            if not silent: self.log_message("No data to export.")
            return
        
        try:
            df = pd.DataFrame(self.history_data)
            df.to_csv(filename, index=False)
            if not silent: self.log_message(f"Data exported to {filename}")
            print(f"Auto-saved log to {filename}")
        except Exception as e:
            if not silent: self.log_message(f"Export failed: {e}")
            print(f"Auto-save failed: {e}")

    def view_history(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open CSV Log", "", "CSV Files (*.csv)")
        if filename:
            dialog = LogViewerDialog(self)
            dialog.load_csv(filename)
            dialog.exec()
