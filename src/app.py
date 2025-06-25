# Standard library
import sys

# Local Imports
from src.stream_analyzer import StreamAnalyzer
from src.pico_io import find_micropython
from src.serial_utils import SerialConnection

# QT6 Imports
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout, QSpinBox, QHBoxLayout, \
    QFormLayout, QGroupBox, QLabel


class MainWindow(QMainWindow):
    stream_analyzer: StreamAnalyzer | None = None
    port: str | None = None
    connection: SerialConnection | None = None

    frequency_bins: int = 25
    window_size: int = 20
    smoothing_length: int = 20

    def __init__(self):
        super().__init__()

        self.port = find_micropython()
        if self.port is None:
            print("No lamp found")

        self.connection = SerialConnection(self.port)
        self.init_ear()

        self.setWindowTitle('Lamp Controller')
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

        main_layout.addLayout(button_layout)

        # Add stretch to push everything to the top
        main_layout.addStretch()

        # Timer to handle updates
        self.timer = QTimer(self)
        self.timer.setSingleShot(False)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.update_waveform)
        self.timer.start()

    def init_ear(self):
        self.stream_analyzer = StreamAnalyzer(
            fft_window_size_ms=self.window_size,  # Window size used for the FFT transform
            smoothing_length_ms=self.smoothing_length,  # Apply some temporal smoothing to reduce noisy features
            n_frequency_bins=self.frequency_bins,  # The FFT features are grouped in bins
        )

    def update_waveform(self):
        self.stream_analyzer.get_audio_features()
        lightshow = self.stream_analyzer.get_lightshow_data()
        self.connection_status.setText(self.connection.status)
        self.connection.write_data(lightshow)
        # print(self.connection.get_received_data())

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

def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
