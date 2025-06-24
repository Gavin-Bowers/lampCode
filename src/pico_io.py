import serial
import serial.tools.list_ports
import time

def test_micropython_hardware_id(port):
    if port.vid is not None and port.pid is not None:
        vid_pid = (f"{port.vid:04X}", f"{port.pid:04X}")
        if vid_pid == ('239A', '80F4'):
            return True
    return False

def test_micropython_repl(port_name, timeout=1):
    """Test if a port responds to MicroPython REPL commands"""
    try:
        with serial.Serial(port_name, 115200, timeout=timeout) as ser:
            # Clear any existing data
            ser.reset_input_buffer()

            # Send Ctrl+C to interrupt any running program
            ser.write(b'\x03')
            time.sleep(0.1)

            # Read response
            response = ser.read(ser.in_waiting or 1000).decode('utf-8', errors='ignore')

            # Send Ctrl+D to do a soft reset
            ser.write(b'\x04')

            return 'KeyboardInterrupt:' in response

    except Exception as e:
        print(f"Error testing {port_name}: {e}")
        return False

def find_micropython() -> str | None:
    """Find MicroPython devices by device id, with serial connection
    check as a fallback"""

    for port in serial.tools.list_ports.comports():
        if test_micropython_hardware_id(port):
            return port.device

    for port in serial.tools.list_ports.comports():
        if test_micropython_repl(port.device):
            return port.device

    return None

if __name__ == '__main__':
    print(find_micropython())