"""
Poll keyboard and print key events with character and keycode.
Use this to see what the guitar/controller keys translate to (char, vk, name).
Stop: Ctrl+C in terminal, or press Escape.
"""
import signal
import sys

try:
    from pynput import keyboard
except ImportError:
    print("Install pynput: pip install pynput")
    sys.exit(1)

_listener_ref = []


def key_repr(key):
    """Return (char_or_none, keycode_int_or_none, name_str)."""
    char = getattr(key, "char", None)
    vk = getattr(key, "vk", None)
    if char is not None:
        # KeyCode: char and vk
        return (char, ord(char) if len(char) == 1 else None, vk, repr(char))
    # Key enum (shift, alt, etc.)
    name = getattr(key, "name", None) or str(key).replace("Key.", "")
    return (None, None, vk, name)


def on_press(key):
    try:
        char, ord_val, vk, name = key_repr(key)
        parts = ["PRESS "]
        if char is not None:
            parts.append(f"char={repr(char)} ord={ord_val}")
        if vk is not None:
            parts.append(f" vk={vk}")
        if name:
            parts.append(f" name={name}")
        print("".join(parts))
    except Exception as e:
        print(f"PRESS (error: {e}) key={key!r}")


def on_release(key):
    try:
        if key == keyboard.Key.esc:
            if _listener_ref:
                print("\nEscape pressed — stopping.")
                _listener_ref[0].stop()
            return
        char, ord_val, vk, name = key_repr(key)
        parts = ["RELEASE "]
        if char is not None:
            parts.append(f"char={repr(char)} ord={ord_val}")
        if vk is not None:
            parts.append(f" vk={vk}")
        if name:
            parts.append(f" name={name}")
        print("".join(parts))
    except Exception as e:
        print(f"RELEASE (error: {e}) key={key!r}")


def main():
    def on_sigint(signum, frame):
        if _listener_ref:
            print("\nCtrl+C — stopping.")
            _listener_ref[0].stop()

    signal.signal(signal.SIGINT, on_sigint)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, on_sigint)

    print("Guitar key poll — press keys to see char / ord / vk / name.")
    print("Stop: Ctrl+C in this window, or press Escape.\n")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        _listener_ref.append(listener)
        try:
            listener.join()
        finally:
            _listener_ref.clear()


if __name__ == "__main__":
    main()
