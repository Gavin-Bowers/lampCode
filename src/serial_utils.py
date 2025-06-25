import serial
import serial.tools.list_ports
from serial import SerialException
import threading

class SerialConnection:
    ser: serial.Serial | None = None
    port_name: str = ""
    status: str = ""

    def __init__(self, port_name):
        self.ser = None
        self.port_name = port_name
        self._connection_lock = threading.Lock()
        self._disconnected = False

        self.open()

    def handle_serial_error(self, error):
        """Handle serial port specific errors"""
        error_msg = str(error).lower()

        if "access is denied" in error_msg or "permission denied" in error_msg:
            self.status = f"Error: Port {self.port_name} is already in use by another application"
        elif "could not open port" in error_msg or "no such file" in error_msg:
            self.status = f"Error: Port {self.port_name} does not exist"
        elif "specified port does not exist" in error_msg:
            self.status = f"Error: Port {self.port_name} is not available"
        else:
            self.status = f"Serial port error: {error}"

        self.ser = None
        self._disconnected = True

    def is_connected(self):
        """Check if serial connection is active"""
        if self._disconnected:
            return False
        if self.ser is None:
            return False

        # Additional check: try to get port status
        try:
            return self.ser.is_open and self.ser.in_waiting >= 0
        except (OSError, SerialException):
            # Port was disconnected
            self._disconnected = True
            self.ser = None
            return False

    def write_data(self, data):
        """Safely write data to serial port with comprehensive error handling"""
        with self._connection_lock:
            if not self.is_connected():
                self.status = "Could not connect to device. Make sure it's plugged in and the cable isn't power-only"
                return False

            try:
                if isinstance(data, str):
                    data = data.encode('utf-8')

                # Check if port is still valid before writing
                if not self.ser or not self.ser.is_open:
                    self.status = "Port closed during write"
                    return False

                self.ser.write(data)
                self.ser.flush()
                return True

            except serial.SerialTimeoutException:
                # Handle timeout - try to recover
                try:
                    if self.ser and self.ser.is_open:
                        self.ser.reset_input_buffer()
                        self.ser.reset_output_buffer()
                    return True  # Consider timeout as success if we can recover
                except:
                    # If we can't recover, try to reconnect
                    self.status = "Timeout occurred, attempting reconnect"
                    self.attempt_reconnect()
                    return False

            except (OSError, IOError) as e:
                # This catches device disconnection at OS level
                error_msg = str(e).lower()
                if "device is not ready" in error_msg or "no such device" in error_msg or "broken pipe" in error_msg:
                    self.status = "Device unplugged or disconnected"
                else:
                    self.status = f"OS error (device may be unplugged): {e}"

                self._disconnected = True
                self.ser = None
                print(f"Device disconnection detected: {e}")
                return False

            except SerialException as e:
                error_msg = str(e).lower()
                if "port not open" in error_msg or "device not found" in error_msg:
                    self.status = "Serial device disconnected"
                    self._disconnected = True
                    self.ser = None
                else:
                    self.status = f"Serial error: {e}"
                print(f"Serial exception: {e}")
                return False

            except Exception as e:
                # Catch any other unexpected errors that might terminate the program
                self.status = f"Unexpected error during write: {e}"
                print(f"Unexpected error in write_data: {e}")

                # Assume connection is lost for safety
                self._disconnected = True
                self.ser = None
                return False

    def attempt_reconnect(self):
        """Try to reconnect after an error"""
        try:
            if self.ser:
                self.ser.close()
        except Exception:
            pass  # Ignore errors when closing

        self.ser = None
        self._disconnected = False

        # Try to reopen
        self.open()

    def open(self):
        """Open serial port with comprehensive error handling"""
        with self._connection_lock:
            try:
                # First check if the port exists
                available_ports = [port.device for port in serial.tools.list_ports.comports()]
                if self.port_name not in available_ports:
                    self.status = f"Port {self.port_name} not found in available ports: {available_ports}"
                    return False

                self.ser = serial.Serial(
                    port=self.port_name,
                    timeout=0.1,
                    write_timeout=0.1
                )

                # Test the connection
                if not self.ser.is_open:
                    raise SerialException("Port failed to open")

                self.status = f"Connected to device on {self.port_name}"
                self._disconnected = False
                return True

            except (OSError, IOError) as e:
                # Handle OS-level errors (common when device is unplugged)
                self.status = f"OS error opening {self.port_name}: {e}"
                self.ser = None
                self._disconnected = True
                return False

            except SerialException as e:
                self.handle_serial_error(e)
                return False

            except Exception as e:
                self.status = f"Unexpected error opening serial port {self.port_name}: {e}"
                print(f"Unexpected error in open(): {e}")
                self.ser = None
                self._disconnected = True
                return False

    def close(self):
        """Close the serial connection safely"""
        with self._connection_lock:
            try:
                if self.ser and self.ser.is_open:
                    self.ser.close()
                    self.status = f"Closed connection to {self.port_name}"
            except Exception as e:
                self.status = f"Error closing port: {e}"
                print(f"Error during close(): {e}")
            finally:
                self.ser = None
                self._disconnected = True

    def get_status(self):
        return self.status