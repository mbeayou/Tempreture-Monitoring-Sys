import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, QSettings
from ui import DashboardUI, STYLESHEET
from backend import WebSocketWorker, MockWorker

# Configuration
# Configuration
DEFAULT_IP = "192.168.1.100"
USE_MOCK = False # Set to False to use real hardware (can also toggle relative to UI if needed, but keeping global for now)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Temperature monitoring system")
        self.resize(1000, 700)
        
        # Set Window Icon
        icon_path = self.resource_path("app_icon.png")
        self.setWindowIcon(QIcon(icon_path))
        
        self.ui = DashboardUI()
        self.setCentralWidget(self.ui)
        
        # Persistence Settings
        self.settings = QSettings("CyberpunkThermal", "Dashboard")
        last_ip = self.settings.value("last_ip", DEFAULT_IP)
        self.ui.ip_input.setText(str(last_ip))
        
        # Connect UI Signals
        self.ui.btn_connect.clicked.connect(self.reconnect_system)
        self.ui.sensor_spin.valueChanged.connect(self.ui.set_gauge_count)
        
        # Initial Setup from UI defaults
        self.start_worker(str(last_ip))

    def start_worker(self, ip_address):
        # Backend Thread
        self.thread = QThread()
        if USE_MOCK:
            self.worker = MockWorker()
            self.ui.log_message("Request: Using MOCK data source.")
        else:
            self.worker = WebSocketWorker(ip_address)
            self.ui.log_message(f"Request: Connecting to {ip_address}...")
            
        self.worker.moveToThread(self.thread)
        
        # Connect Signals
        self.thread.started.connect(self.worker.run)
        self.worker.data_received.connect(self.ui.update_data)
        self.worker.connection_status.connect(self.ui.update_connection)
        
        # Start
        self.thread.start()

    def reconnect_system(self):
        # Get new IP
        new_ip = self.ui.ip_input.text().strip()
        if not new_ip:
            self.ui.log_message("Error: IP cannot be empty.")
            return

        self.ui.log_message(f"Reconnecting to {new_ip}...")
        
        # Stop existing worker
        if hasattr(self, 'worker'):
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()
            
        # Start new worker
        self.start_worker(new_ip)
        
        # Update gauge visibility immediately (just in case)
        self.ui.set_gauge_count(self.ui.sensor_spin.value())

    def closeEvent(self, event):
        # Save IP
        self.settings.setValue("last_ip", self.ui.ip_input.text())
        
        # Auto-save Log
        self.ui.auto_save_log()
        
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        event.accept()

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
