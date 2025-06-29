# Standard library
import queue
import sys, threading
import time

from PyQt6.QtGui import QIcon

# Local Imports
from stream_analyzer import StreamAnalyzer
from serial_utils import SerialConnection

# QT6 Imports
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout, QSpinBox, QHBoxLayout, \
    QFormLayout, QGroupBox, QLabel, QSlider


class ThreadSafeData:
    def __init__(self):
        self._lock = threading.Lock()
        self._data: bytes = b''

    def set(self, data: bytes):
        with self._lock:
            self._data = data

    def read(self):
        with self._lock:
            return self._data

class MainWindow(QMainWindow):
    stream_analyzer: StreamAnalyzer | None = None
    connection: SerialConnection | None = None

    frequency_bins: int = 25
    window_size: int = 20
    smoothing_length: int = 20
    commands = queue.Queue() # Commands is a queue of strings to be sent to the pico
    brightness = 100
    new_brightness = 100
    lightshow_data = ThreadSafeData()

    def __init__(self):
        super().__init__()

        self.connection = SerialConnection()
        self.init_ear()

        self.setWindowTitle('Lamp Controller')
        # self.setWindowIcon(QIcon('resources/icon.ico'))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        connection_group = QGroupBox("Serial Connection")
        connection_layout = QFormLayout()
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)

        self.connection_status = QLabel()
        self.connection_status.setText("Trying to connect")
        connection_layout.addRow("Connection Status:", self.connection_status)

        self.reconnect_button = QPushButton("Try to reconnect")
        self.reconnect_button.clicked.connect(self.connection.attempt_reconnect)
        connection_layout.addRow(self.reconnect_button)

        self.reboot_button = QPushButton("Reboot")
        self.reboot_button.clicked.connect(self.soft_reboot)
        connection_layout.addRow(self.reboot_button)

        self.change_mode_button = QPushButton("Change Mode")
        self.change_mode_button.clicked.connect(self.change_mode)
        connection_layout.addRow(self.change_mode_button)

        self.change_color_button = QPushButton("Change Color Scheme")
        self.change_color_button.clicked.connect(self.change_color)
        connection_layout.addRow(self.change_color_button)

        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setMinimum(0)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setValue(100)
        connection_layout.addRow(self.brightness_slider)
        self.brightness_slider.valueChanged.connect(self.change_brightness)

        # Create form group box
        settings_group = QGroupBox("Audio Parameters")
        settings_layout = QFormLayout()
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Frequency bins input
        self.freq_bins_spin = QSpinBox()
        self.freq_bins_spin.setRange(1, 50)
        self.freq_bins_spin.setValue(25)
        self.freq_bins_spin.setToolTip("The FFT features are grouped in bins")
        settings_layout.addRow("Frequency Bins:", self.freq_bins_spin)

        # Window size input
        self.window_size_spin = QSpinBox()
        self.window_size_spin.setRange(1, 100)
        self.window_size_spin.setValue(20)
        self.window_size_spin.setSuffix(" ms")
        self.window_size_spin.setToolTip("The size of audio samples in ms")
        settings_layout.addRow("Window Size:", self.window_size_spin)

        # Smoothing length input
        self.smoothing_spin = QSpinBox()
        self.smoothing_spin.setRange(1, 100)
        self.smoothing_spin.setValue(20)
        self.smoothing_spin.setSuffix(" ms")
        self.smoothing_spin.setToolTip("The length of the audio smoothing sample in ms")
        settings_layout.addRow("Smoothing Length:", self.smoothing_spin)

        # Button layout
        button_layout = QHBoxLayout()

        # Apply button
        self.apply_button = QPushButton("Apply Settings")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)

        # Reset button
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_defaults)
        button_layout.addWidget(self.reset_button)

        settings_layout.addRow(button_layout)

        # Add stretch to push everything to the top
        main_layout.addStretch()

        self.timer = QTimer(self)
        self.timer.setSingleShot(False)
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.main_loop)
        self.timer.start()

        worker_thread = threading.Thread(target=self.lightshow_worker)
        worker_thread.daemon = True # Dies when main thread dies
        worker_thread.start()

        comm_worker_thread = threading.Thread(target=self.communication_worker)
        comm_worker_thread.daemon = True
        comm_worker_thread.start()

    def init_ear(self):
        self.stream_analyzer = StreamAnalyzer(
            fft_window_size_ms=self.window_size,  # Window size used for the FFT transform
            smoothing_length_ms=self.smoothing_length,  # Apply some temporal smoothing to reduce noisy features
            n_frequency_bins=self.frequency_bins,  # The FFT features are grouped in bins
        )

    def main_loop(self):
        if self.connection_status.text() != self.connection.status:
            self.connection_status.setText(self.connection.status)

    def soft_reboot(self):
        self.connection.write_data(b'\x03') # Ctrl-C
        self.connection.write_data(b'\x04') # Ctrl-D

    def apply_settings(self):
        self.window_size = self.window_size_spin.value()
        self.smoothing_length = self.smoothing_spin.value()
        self.frequency_bins = self.freq_bins_spin.value()
        self.init_ear()

    def reset_defaults(self):
        """Reset all values to their defaults"""
        self.freq_bins_spin.setValue(25)
        self.window_size_spin.setValue(20)
        self.smoothing_spin.setValue(20)
        self.apply_settings()

    def communication_worker(self):
        while True:
            # Call and response system ensures that the pico only gets input when it's ready
            # Although there are still occasional instances of data being mangled, so that still needs to be handled
            data = self.connection.read_data()
            # if data is not None and not "pico_ready" in data and not "lightshow_data" in data: print(data)
            if data is not None and "pico_ready" in data:
                # Only send one line at a time, either a command, or a lightshow update
                if not self.commands.empty():
                    self.connection.write_data(self.commands.get_nowait())
                elif self.brightness != self.new_brightness:
                    self.brightness = self.new_brightness
                    self.connection.write_data(f'change_brightness {self.brightness}\r'.encode())
                else:
                    # self.connection.write_data(b'lightshow_data 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 \r')
                    self.connection.write_data(self.lightshow_data.read())
            time.sleep(0.001)

    def lightshow_worker(self):
        while True:
            self.stream_analyzer.get_audio_features()
            self.lightshow_data.set(self.stream_analyzer.get_lightshow_data())
            time.sleep(0.001)

    # The carriage return (\r) is REQUIRED for pico to respond

    def change_color(self):
        self.commands.put(b'change_color\r')

    def change_mode(self):
        self.commands.put(b'change_mode\r')

    def change_brightness(self):
        self.new_brightness = self.brightness_slider.value()

def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
