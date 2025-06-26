import serial
import serial.tools.list_ports

class SerialConnection:

    def __init__(self, port_name):
        self.ser = None
        self.port_name = port_name
        self.status = ""
        self.open()

    def write_data_packet(self, data):
        packet = f"<{data}>\r".encode() # Wrap in delimiters
        return self.write_data(packet)

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
        if self.ser:
            self.ser.close()
            self.ser = None
        self.open()

    def open(self):
        try:
            self.ser = serial.Serial(
                port=self.port_name,
                timeout=0.1,
                write_timeout=0.1
            )
            self.status = f"Connected to device on {self.port_name}"
            return True

        except Exception as e:
            self.ser = None
            self.status = f"Error opening {self.port_name}: {e}"
            return False