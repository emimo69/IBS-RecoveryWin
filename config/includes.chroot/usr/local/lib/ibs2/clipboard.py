"""Bidirectional UTF-8 clipboard bridge. Local UNIX socket, no network listener."""
import select
import socket
import struct
import subprocess
import time

LIMIT = 1024 * 1024
READY = 0xffffffff

class Frames:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        self.buffer.extend(data)
        messages = []
        while len(self.buffer) >= 8:
            magic, size = struct.unpack('<4sI', self.buffer[:8])
            if magic != b'IBC2' or (size > LIMIT and size != READY):
                raise ValueError('Protocollo appunti non valido')
            if size == READY:
                del self.buffer[:8]
                messages.append(None)
                continue
            if len(self.buffer) < size + 8:
                break
            text = bytes(self.buffer[8:8 + size]).decode('utf-8')
            if '\x00' in text:
                raise ValueError('Appunti con caratteri NUL')
            del self.buffer[:8 + size]
            messages.append(text)
        if len(self.buffer) > LIMIT + 8:
            raise ValueError('Appunti troppo grandi')
        return messages

def frame(text):
    raw = text.encode('utf-8')
    if len(raw) > LIMIT or '\x00' in text:
        raise ValueError('Appunti troppo grandi o non validi')
    return struct.pack('<4sI', b'IBC2', len(raw)) + raw

def read_clipboard():
    try:
        result = subprocess.run(['xclip', '-selection', 'clipboard', '-out'], capture_output=True, timeout=1)
        if result.returncode or len(result.stdout) > LIMIT:
            return None
        return result.stdout.decode('utf-8')
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        return None

def write_clipboard(text):
    # Foreground xclip is reaped when ownership changes; never leave zombies.
    return subprocess.Popen(['xclip', '-selection', 'clipboard', '-in', '-quiet'],
                            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def bridge(path, stop, ready_event=None):
    conn = socket.socket(socket.AF_UNIX)
    children = []
    try:
        while not stop.is_set():
            try:
                conn.connect(str(path))
                break
            except (FileNotFoundError, ConnectionRefusedError):
                stop.wait(.2)
        if stop.is_set():
            return
        parser = Frames()
        ready = True
        last = None
        while not stop.is_set():
            readable, _, _ = select.select([conn], [], [], .15)
            if readable:
                data = conn.recv(65536)
                if not data:
                    break
                for text in parser.feed(data):
                    if text is None:
                        ready = True
                        last = None
                        if ready_event:
                            ready_event.set()
                    elif ready:
                        if ready_event:
                            ready_event.set()
                        child = write_clipboard(text)
                        child.stdin.write(text.encode('utf-8'))
                        child.stdin.close()
                        children.append(child)
                        last = text
                        # Wait for X11 ownership before polling, avoiding stale echoes.
                        for _ in range(20):
                            if read_clipboard() == text:
                                break
                            stop.wait(.025)
            if ready:
                text = read_clipboard()
                if text is not None and text != last:
                    conn.sendall(frame(text))
                    last = text
            children[:] = [p for p in children if p.poll() is None]
    finally:
        conn.close()
        for child in children:
            child.terminate()
            child.wait(timeout=3)
