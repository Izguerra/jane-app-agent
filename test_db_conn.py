import socket
import os

def test_conn(host, port):
    try:
        s = socket.create_connection((host, port), timeout=2)
        print(f"Success connecting to {host}:{port}")
        s.close()
    except Exception as e:
        print(f"Failed connecting to {host}:{port} - {e}")

test_conn("localhost", 54322)
test_conn("127.0.0.1", 54322)

