import argparse
from tokenize import String
from src.stream_analyzer import Stream_Analyzer
import time
import serial

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=int, default=6, dest='device',
                        help='pyaudio (portaudio) device index')
    parser.add_argument('--n_frequency_bins', type=int, default=25, dest='frequency_bins',
                        help='The FFT features are grouped in bins')
    parser.add_argument('--port', type=int, default=4, dest='port',
                        help='The serial port the lamp is connected to'),
    parser.add_argument('--window_size', type=int, default=20, dest='window_size',
                        help='The size of audio samples in ms'),
    parser.add_argument('--smoothing_length', type=int, default=20, dest='smoothing_length',
                        help='The length of the audio smoothing sample in ms')
    return parser.parse_args()

def convert_window_ratio(window_ratio):
    if '/' in window_ratio:
        dividend, divisor = window_ratio.split('/')
        try:
            float_ratio = float(dividend) / float(divisor)
        except:
            raise ValueError('window_ratio should be in the format: float/float')
        return float_ratio
    raise ValueError('window_ratio should be in the format: float/float')

def run_FFT_analyzer():
    args = parse_args()
    window_ratio = convert_window_ratio('24/9')

    ear = Stream_Analyzer(
                    device = args.device,        # Pyaudio (portaudio) device index, defaults to first mic input
                    rate   = None,               # Audio samplerate, None uses the default source settings
                    FFT_window_size_ms  = args.window_size,    # Window size used for the FFT transform
                    smoothing_length_ms = args.smoothing_length,    # Apply some temporal smoothing to reduce noisy features
                    n_frequency_bins = args.frequency_bins, # The FFT features are grouped in bins
                    serial_port = args.port,
                    updates_per_second  = 4000,  # How often to read the audio stream for new data
                    visualize = 0,               # Visualize the FFT features with PyGame
                    verbose   = False,    # Print running statistics (latency, fps, ...)
                    height    = 450,     # Height, in pixels, of the visualizer window,
                    window_ratio = '24/9'  # Float ratio of the visualizer window. e.g 24/9
                    )

    fps = 200  #How often to update the FFT features + display
    last_update = time.time()
    while True:
        if (time.time() - last_update) > (1./fps):
            last_update = time.time()
            raw_fftx, raw_fft, binned_fftx, binned_fft = ear.get_audio_features()

if __name__ == '__main__':
    run_FFT_analyzer()
