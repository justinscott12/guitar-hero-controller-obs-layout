"""
NBCP guitar (keyboard keys) → WebSocket bridge for OBS overlay.
Uses global keyboard hook so it works when Clone Hero has focus.
Sends key_pressed/key_released on port 16899 (same format as index.html).
Run this, then use OBS Browser Source with index.html.
Stop: Ctrl+C in the terminal window.
"""
import json
import signal
import sys
import threading
import time

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
# up=38 strum up, down=40 strum down, alt_gr=9 whammy
KEY_TO_KEYCODE = {
    "v": 47,
    "c": 46,
    "x": 45,
    "z": 44,
    "shift": 42,
}
STRUM_UP_KEYCODE = 38
STRUM_DOWN_KEYCODE = 40
WHAMMY_KEYCODE = 9
ALT_MINUS_KEYCODE = 27   # ESC (side minus, slightly higher)
ALT_PLUS_KEYCODE = 13   # Enter (side plus, slightly lower)

WS_PORT = 16899
clients = set()
clients_lock = threading.Lock()
_listener_ref = []  # [Listener] so signal handler / on_release can stop it


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
    elif key == keyboard.Key.up:
        broadcast({"event_type": "key_pressed", "keycode": STRUM_UP_KEYCODE})
    elif key == keyboard.Key.down:
        broadcast({"event_type": "key_pressed", "keycode": STRUM_DOWN_KEYCODE})
    elif key == keyboard.Key.alt_gr:
        broadcast({"event_type": "key_pressed", "keycode": WHAMMY_KEYCODE})
    elif key == keyboard.Key.esc:
        broadcast({"event_type": "key_pressed", "keycode": ALT_MINUS_KEYCODE})
    elif key == keyboard.Key.enter:
        broadcast({"event_type": "key_pressed", "keycode": ALT_PLUS_KEYCODE})


def on_release(key):
    k = key.char.lower() if hasattr(key, "char") and key.char else None
    if k and k in KEY_TO_KEYCODE:
        broadcast({"event_type": "key_released", "keycode": KEY_TO_KEYCODE[k]})
    elif key == keyboard.Key.shift:
        broadcast({"event_type": "key_released", "keycode": 54})
    elif key == keyboard.Key.up:
        broadcast({"event_type": "key_released", "keycode": STRUM_UP_KEYCODE})
    elif key == keyboard.Key.down:
        broadcast({"event_type": "key_released", "keycode": STRUM_DOWN_KEYCODE})
    elif key == keyboard.Key.alt_gr:
        broadcast({"event_type": "key_released", "keycode": WHAMMY_KEYCODE})
    elif key == keyboard.Key.esc:
        broadcast({"event_type": "key_released", "keycode": ALT_MINUS_KEYCODE})
    elif key == keyboard.Key.enter:
        broadcast({"event_type": "key_released", "keycode": ALT_PLUS_KEYCODE})


def main():
    ws_thread = threading.Thread(target=websocket_server, daemon=True)
    ws_thread.start()

    def on_sigint(signum, frame):
        if _listener_ref:
            print("\nCtrl+C — stopping.")
            _listener_ref[0].stop()

    signal.signal(signal.SIGINT, on_sigint)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, on_sigint)

    print("NBCP keyboard bridge running. Press v/c/x/z/shift to test.")
    print("In OBS: Browser Source -> Local file -> index.html")
    print("Stop: Ctrl+C in this window.")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        _listener_ref.append(listener)
        try:
            # Sleep in a loop so main thread can receive Ctrl+C on Windows (listener.join() blocks and may not)
            while listener.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nCtrl+C — stopping.")
            listener.stop()
        finally:
            _listener_ref.clear()


if __name__ == "__main__":
    main()
