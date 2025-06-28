import time

import serial
import serial.tools.list_ports

class SerialConnection:
    ser = None
    status = ""

    def __init__(self):

        self.port = find_pico()
        if self.port is None:
            self.status = "No device found. Make sure it's connected and the cable isn't power only"
        else:
            self.open()

    def write_data(self, data: bytes):
        if self.ser is None:
            return False
        try:
            self.ser.write(data)
            self.ser.flush()
            return True
        except serial.SerialTimeoutException: # Try to recover from timeout
            print("timeout")
            if self.ser and self.ser.is_open:
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                return True
            else:
                print("Timeout occurred, attempting reconnect")
                self.status = "Timeout occurred, attempting reconnect"
                self.attempt_reconnect()
                return False

        except Exception as e:
            self.status = f'Error writing data: {e}'
            self.ser = None
            return False

    def read_data(self) -> str | None:
        if self.ser is None:
            return None
        try:
            if self.ser.in_waiting > 0:
                return self.ser.readline().decode('utf-8').rstrip()
            return None
        except Exception as e:
            self.status = f'Error reading data: {e}'

    def attempt_reconnect(self):
        if self.port is None:
            self.port = find_pico()

        if self.port is None: # If it's still none, then find_pico failed
            self.status = "No device found. Make sure it's connected and the cable isn't power only"
            return

        if self.ser:
            self.ser.close()
            self.ser = None
        self.open()

    def open(self):
        try:
            self.ser = serial.Serial(port=self.port, timeout=0.1, write_timeout=0.1)
            self.status = f"Connected to device on {self.port}"
            return True
        except Exception as e:
            self.ser = None
            self.status = f"Error opening {self.port}: {e}"
            return False

def is_pico(port):
    """Uses hardware id to check if a COM port is a Raspberry Pi Pico"""
    if port.vid is not None and port.pid is not None:
        vid_pid = (f"{port.vid:04X}", f"{port.pid:04X}")
        if vid_pid == ('239A', '80F4'):
            return True
    return False

def find_pico() -> str | None:
    """Checks each COM port to see if any are a Raspberry Pi Pico. Returns the first one, or None"""
    for port in serial.tools.list_ports.comports():
        if is_pico(port):
            return port.device
    return None