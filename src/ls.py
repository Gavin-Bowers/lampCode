# Standard library
import sys

# Local Imports
from src.streamanalyzer import StreamAnalyzer
from src.pico_io import find_micropython

# QT6 Imports
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout, QSpinBox, QHBoxLayout, \
    QFormLayout, QGroupBox


class MainWindow(QMainWindow):
    ear: StreamAnalyzer | None = None
    port: str | None = None
    frequency_bins: int = 25
    window_size: int = 20
    smoothing_length: int = 20

    def __init__(self):
        super().__init__()

        self.port = find_micropython()
        if self.port is None:
            sys.exit(0)
        self.init_ear()

        self.setWindowTitle('Lamp Controller')
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create form group box
        form_group = QGroupBox("Audio Parameters")
        form_layout = QFormLayout()

        # Frequency bins input
        self.freq_bins_spin = QSpinBox()
        self.freq_bins_spin.setRange(1, 50)
        self.freq_bins_spin.setValue(25)
        self.freq_bins_spin.setToolTip("The FFT features are grouped in bins")
        form_layout.addRow("Frequency Bins:", self.freq_bins_spin)

        # Window size input
        self.window_size_spin = QSpinBox()
        self.window_size_spin.setRange(1, 100)
        self.window_size_spin.setValue(20)
        self.window_size_spin.setSuffix(" ms")
        self.window_size_spin.setToolTip("The size of audio samples in ms")
        form_layout.addRow("Window Size:", self.window_size_spin)

        # Smoothing length input
        self.smoothing_spin = QSpinBox()
        self.smoothing_spin.setRange(1, 100)
        self.smoothing_spin.setValue(20)
        self.smoothing_spin.setSuffix(" ms")
        self.smoothing_spin.setToolTip("The length of the audio smoothing sample in ms")
        form_layout.addRow("Smoothing Length:", self.smoothing_spin)

        form_group.setLayout(form_layout)
        main_layout.addWidget(form_group)

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

        # Timer to handle audiovisualizer updates
        self.timer = QTimer(self)
        self.timer.setSingleShot(False)
        self.timer.setInterval(5) # in milliseconds, ie 200 fps
        self.timer.timeout.connect(self.update_waveform)
        self.timer.start()

    def init_ear(self):
        self.ear = StreamAnalyzer(
            device=0, # Pyaudio (portaudio) device index, defaults to first mic input
            rate=None,  # Audio samplerate, None uses the default source settings
            FFT_window_size_ms=self.window_size,  # Window size used for the FFT transform
            smoothing_length_ms=self.smoothing_length,  # Apply some temporal smoothing to reduce noisy features
            n_frequency_bins=self.frequency_bins,  # The FFT features are grouped in bins
            serial_port=int(self.port[-1]),
            updates_per_second=4000,  # How often to read the audio stream for new data
            verbose=False  # Print running statistics (latency, fps, ...)
        )

    def update_waveform(self):
        self.ear.get_audio_features()

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
