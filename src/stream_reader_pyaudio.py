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


# if __name__ == "__main__":
#     p = pyaudio.PyAudio()
#     audio_queue = Queue()
#     ar = AudioRecorder(p, audio_queue)
#
#     help_msg = 30 * "-" + "\n\n\nStatus:\nRunning=%s | Device=%s | output=%s\n\nCommands:\nlist\nrecord {device_index\\default}\npause\ncontinue\nstop {*.wav\\default}\n"
#
#     target_device = None
#
#     try:
#         while True:
#             print(help_msg % (
#             ar.stream_status, target_device["index"] if target_device is not None else "None", filename))
#             com = input("Enter command: ").split()
#
#             if com[0] == "list":
#                 p.print_detailed_system_info()
#
#             elif com[0] == "record":
#
#                 if len(com) > 1 and com[1].isdigit():
#                     target_device = p.get_device_info_by_index(int(com[1]))
#                 else:
#                     try:
#                         target_device = ar.get_default_wasapi_device(p)
#                     except ARException as E:
#                         print(f"Something went wrong... {type(E)} = {str(E)[:30]}...\n")
#                         continue
#                 ar.start_recording(target_device)
#
#             elif com[0] == "pause":
#                 ar.stop_stream()
#             elif com[0] == "continue":
#                 ar.start_stream()
#             elif com[0] == "stop":
#                 ar.close_stream()
#
#                 if len(com) > 1 and com[1].endswith(".wav") and os.path.exists(
#                         os.path.dirname(os.path.realpath(com[1]))):
#                     filename = com[1]
#
#                 wave_file = wave.open(filename, 'wb')
#                 wave_file.setnchannels(target_device["maxInputChannels"])
#                 wave_file.setsampwidth(pyaudio.get_sample_size(DATA_FORMAT))
#                 wave_file.setframerate(int(target_device["defaultSampleRate"]))
#
#                 while not audio_queue.empty():
#                     wave_file.writeframes(audio_queue.get())
#                 wave_file.close()
#
#                 print(f"The audio is written to a [{filename}]. Exit...")
#                 break
#
#             else:
#                 print(f"[{com[0]}] is unknown command")
#
#     except KeyboardInterrupt:
#         print("\n\nExit without saving...")
#     finally:
#         ar.close_stream()
#         p.terminate()