import math

import pyaudiowpatch as pyaudio
import numpy as np

from src.utils import NumpyDataBuffer, round_up_to_even

class StreamReader:

    def __init__(self, fft_window_size_ms):
        self.stream = None
        self.pa = pyaudio.PyAudio()
        self.target_device = self.pa.get_default_wasapi_loopback()
        self.rate = self.target_device["defaultSampleRate"]
        self.new_data = False
        self.update_window_n_frames = round_up_to_even(self.rate / 200) # hardcoded updates/s of 200
        fft_window_size = round_up_to_even(self.rate * fft_window_size_ms / 1000)
        self.data_windows_to_buffer = math.ceil(fft_window_size / self.update_window_n_frames)
        self.data_windows_to_buffer = max(1, self.data_windows_to_buffer)
        self.data_buffer = NumpyDataBuffer(self.data_windows_to_buffer, self.update_window_n_frames)
        self.start_recording()

    def callback(self, in_data, _frame_count, _time_info, _status):
        """Write frames and return PA flag"""
        self.data_buffer.append_data(np.frombuffer(in_data, dtype=np.float32))
        # self.data_buffer.append_data(in_data[:, 0])
        self.new_data = True
        return in_data, pyaudio.paContinue

    def start_recording(self):
        self.close_stream()
        # self.target_device["maxInputChannels"] for channels?
        self.stream = self.pa.open(format=pyaudio.paFloat32,
                                   channels=1,
                                   rate=int(self.target_device["defaultSampleRate"]),
                                   frames_per_buffer=self.update_window_n_frames,
                                   input=True,
                                   input_device_index=self.target_device["index"],
                                   stream_callback=self.callback
                                   )

    def stop_stream(self):
        self.stream.stop_stream()

    def start_stream(self):
        self.stream.start_stream()

    def close_stream(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    @property
    def stream_status(self):
        return "closed" if self.stream is None else "stopped" if self.stream.is_stopped() else "running"