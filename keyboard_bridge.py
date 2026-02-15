"""
NBCP guitar (keyboard keys) → WebSocket bridge for OBS overlay.
Uses global keyboard hook so it works when Clone Hero has focus.
Sends key_pressed/key_released on port 16899 (same format as index.html).
Run this, then use OBS Browser Source with index.html.
"""
import json
import sys
import threading

try:
    from pynput import keyboard
except ImportError:
    print("Install pynput: pip install pynput")
    sys.exit(1)

try:
    from websockets.sync.server import serve
except ImportError:
    print("Install websockets: pip install websockets")
    sys.exit(1)

# NBCP key map (Clone Hero default) → keycodes (matches index.html)
# v=47 green, c=46 red, x=45 yellow, z=44 blue, shift=42/54 orange
KEY_TO_KEYCODE = {
    "v": 47,
    "c": 46,
    "x": 45,
    "z": 44,
    "shift": 42,
}

WS_PORT = 16899
clients = set()
clients_lock = threading.Lock()


def broadcast(msg):
    """Send JSON message to all connected WebSocket clients."""
    data = json.dumps(msg)
    with clients_lock:
        for ws in list(clients):
            try:
                ws.send(data)
            except Exception:
                clients.discard(ws)


def websocket_server():
    """WebSocket server on port 16899."""
    def handler(websocket):
        with clients_lock:
            clients.add(websocket)
        try:
            for _ in websocket:
                pass
        finally:
            with clients_lock:
                clients.discard(websocket)

    with serve(handler, "127.0.0.1", WS_PORT) as server:
        print(f"WebSocket server on ws://127.0.0.1:{WS_PORT}")
        server.serve_forever()


def on_press(key):
    k = key.char.lower() if hasattr(key, "char") and key.char else None
    if k and k in KEY_TO_KEYCODE:
        broadcast({"event_type": "key_pressed", "keycode": KEY_TO_KEYCODE[k]})
    elif key == keyboard.Key.shift:
        broadcast({"event_type": "key_pressed", "keycode": 54})


def on_release(key):
    k = key.char.lower() if hasattr(key, "char") and key.char else None
    if k and k in KEY_TO_KEYCODE:
        broadcast({"event_type": "key_released", "keycode": KEY_TO_KEYCODE[k]})
    elif key == keyboard.Key.shift:
        broadcast({"event_type": "key_released", "keycode": 54})


def main():
    ws_thread = threading.Thread(target=websocket_server, daemon=True)
    ws_thread.start()

    print("NBCP keyboard bridge running. Press v/c/x/z/shift to test.")
    print("In OBS: Browser Source -> Local file -> index.html")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    main()
