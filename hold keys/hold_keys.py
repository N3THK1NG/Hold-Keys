import ctypes
import ctypes.wintypes
import threading
import tkinter as tk
from tkinter import ttk


user32 = ctypes.windll.user32
user32.SendInput.argtypes = (ctypes.c_uint, ctypes.c_void_p, ctypes.c_int)
user32.SendInput.restype = ctypes.c_uint
user32.RegisterHotKey.argtypes = (ctypes.wintypes.HWND, ctypes.c_int, ctypes.c_uint, ctypes.c_uint)
user32.RegisterHotKey.restype = ctypes.wintypes.BOOL
user32.UnregisterHotKey.argtypes = (ctypes.wintypes.HWND, ctypes.c_int)
user32.UnregisterHotKey.restype = ctypes.wintypes.BOOL
user32.GetMessageW.argtypes = (ctypes.POINTER(ctypes.wintypes.MSG), ctypes.wintypes.HWND, ctypes.c_uint, ctypes.c_uint)
user32.GetMessageW.restype = ctypes.c_int
user32.PostThreadMessageW.argtypes = (ctypes.c_uint, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t)
user32.PostThreadMessageW.restype = ctypes.wintypes.BOOL
kernel32 = ctypes.windll.kernel32
kernel32.GetCurrentThreadId.restype = ctypes.c_uint

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
XBUTTON1 = 1
XBUTTON2 = 2
WM_HOTKEY = 0x0312
WM_CHANGE_HOTKEY = 0x8001
HOTKEY_ID = 1
MOD_NOREPEAT = 0x4000


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", INPUT_UNION)]


KEYS = {
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45, "F": 0x46,
    "G": 0x47, "H": 0x48, "I": 0x49, "J": 0x4A, "K": 0x4B, "L": 0x4C,
    "M": 0x4D, "N": 0x4E, "O": 0x4F, "P": 0x50, "Q": 0x51, "R": 0x52,
    "S": 0x53, "T": 0x54, "U": 0x55, "V": 0x56, "W": 0x57, "X": 0x58,
    "Y": 0x59, "Z": 0x5A, "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33,
    "4": 0x34, "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    "Space": 0x20, "Enter": 0x0D, "Tab": 0x09, "Shift": 0x10, "Ctrl": 0x11,
    "Alt": 0x12, "Up": 0x26, "Down": 0x28, "Left": 0x25, "Right": 0x27,
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74,
    "F6": 0x75, "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A,
    "F12": 0x7B, "Esc": 0x1B, "Backspace": 0x08, "Backslash": 0xDC,
}
EXTENDED = {"Up", "Down", "Left", "Right"}
MOUSE = {
    "Left mouse": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, 0),
    "Right mouse": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP, 0),
    "Middle mouse": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP, 0),
    "Mouse button 4": (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON1),
    "Mouse button 5": (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON2),
}


def send(inputs):
    if inputs:
        array = (INPUT * len(inputs))(*inputs)
        sent = user32.SendInput(len(inputs), ctypes.cast(array, ctypes.c_void_p), ctypes.sizeof(INPUT))
        if sent != len(inputs):
            raise ctypes.WinError(ctypes.get_last_error())


def key_input(name, up=False):
    flags = 0
    if up:
        flags |= KEYEVENTF_KEYUP
    if name in EXTENDED:
        flags |= KEYEVENTF_EXTENDEDKEY
    return INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(KEYS[name], 0, flags, 0, None)))


def mouse_input(name, up=False):
    down, release, data = MOUSE[name]
    flags = release if up else down
    return INPUT(type=INPUT_MOUSE, union=INPUT_UNION(mi=MOUSEINPUT(0, 0, data, flags, 0, None)))


class HoldKeysApp:
    def __init__(self, root):
        self.root = root
        root.title("Hold Keys")
        root.resizable(False, False)
        root.configure(padx=22, pady=18)
        self.selected = set()
        self.held = []
        self.active = False
        self.capture_for = None
        self.rows = {}
        self.toggle_name = tk.StringVar(value="Backslash")
        self.hotkey_thread_id = 0

        ttk.Label(root, text="Hold keys and mouse buttons", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(root, text="Choose what to hold and set the global start/stop key.", foreground="#555").pack(anchor="w", pady=(3, 14))

        toggle_row = ttk.Frame(root)
        toggle_row.pack(anchor="w", fill="x", pady=(0, 12))
        ttk.Label(toggle_row, text="Toggle key:").pack(side="left", padx=(0, 8))
        toggle_picker = ttk.Combobox(toggle_row, textvariable=self.toggle_name,
                                     values=list(KEYS), state="readonly", width=16)
        toggle_picker.pack(side="left")
        ttk.Button(toggle_row, text="Apply", command=self.change_hotkey).pack(side="left", padx=8)

        area = ttk.Frame(root)
        area.pack(fill="x")
        self.add_group(area, "Keyboard", list(KEYS))
        self.add_group(area, "Mouse buttons", list(MOUSE))

        self.status = ttk.Label(root, text="Stopped", foreground="#555", font=("Segoe UI", 10, "bold"))
        self.status.pack(anchor="w", pady=(14, 8))
        ttk.Label(root, text="The toggle works while this window is minimized. Closing the window releases everything.", foreground="#666").pack(anchor="w")

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.hotkey_thread = threading.Thread(target=self.hotkey_loop, daemon=True)
        self.hotkey_thread.start()
        self.root.after(100, self.drain_events)

    def add_group(self, parent, title, options):
        box = ttk.LabelFrame(parent, text=title, padding=10)
        box.pack(side="left", fill="y", padx=(0, 10))
        canvas = tk.Canvas(box, width=175, height=250, highlightthickness=0)
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=canvas.yview)
        inside = ttk.Frame(canvas)
        inside.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
        canvas.create_window((0, 0), window=inside, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        for name in options:
            var = tk.BooleanVar(value=False)
            self.rows[name] = var
            ttk.Checkbutton(inside, text=name, variable=var, command=lambda n=name, v=var: self.select(n, v)).pack(anchor="w", pady=2)
        canvas.pack(side="left", fill="y")
        scrollbar.pack(side="right", fill="y")

    def select(self, name, var):
        if self.active:
            var.set(name in self.selected)
            return
        if var.get():
            self.selected.add(name)
        else:
            self.selected.discard(name)

    def hotkey_loop(self):
        # Register and read the hotkey on this same thread. Windows delivers
        # WM_HOTKEY to the message queue of the thread that registered it.
        self.hotkey_thread_id = kernel32.GetCurrentThreadId()
        current_vk = KEYS["Backslash"]
        registered = bool(user32.RegisterHotKey(None, HOTKEY_ID, MOD_NOREPEAT, current_vk))
        self.root.after(0, lambda: self.show_hotkey_status(registered))
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_CHANGE_HOTKEY:
                previous_vk = current_vk
                if registered:
                    user32.UnregisterHotKey(None, HOTKEY_ID)
                requested_vk = int(msg.wParam)
                requested_ok = bool(user32.RegisterHotKey(None, HOTKEY_ID, MOD_NOREPEAT, requested_vk))
                if requested_ok:
                    current_vk = requested_vk
                    registered = True
                else:
                    # Keep the previous working toggle if the new one is taken.
                    current_vk = previous_vk
                    registered = bool(user32.RegisterHotKey(None, HOTKEY_ID, MOD_NOREPEAT, previous_vk))
                self.root.after(0, lambda ok=registered, vk=current_vk: self.show_hotkey_status(ok, vk))
            elif msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.root.after(0, self.toggle)
        if registered:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    def show_hotkey_status(self, registered, active_vk=None):
        if active_vk is not None:
            self.toggle_name.set(next(name for name, vk in KEYS.items() if vk == active_vk))
        if registered:
            self.status.configure(text=f"Stopped — {self.toggle_name.get()} is ready", foreground="#555")
        else:
            self.status.configure(text=f"{self.toggle_name.get()} is in use; choose another toggle key", foreground="#b45309")

    def change_hotkey(self):
        name = self.toggle_name.get()
        vk = KEYS.get(name)
        if not vk or not self.hotkey_thread_id:
            return
        if not user32.PostThreadMessageW(self.hotkey_thread_id, WM_CHANGE_HOTKEY, vk, 0):
            self.status.configure(text="Could not change the toggle key", foreground="#b91c1c")
        else:
            self.status.configure(text=f"Setting {name} as the toggle key…", foreground="#555")

    def drain_events(self):
        self.root.after(100, self.drain_events)

    def toggle(self):
        if self.active:
            self.release_all()
            return
        if not self.selected:
            self.status.configure(text="Select at least one key or mouse button", foreground="#b45309")
            return
        inputs = []
        self.held = sorted(self.selected)
        for name in self.held:
            inputs.append(mouse_input(name) if name in MOUSE else key_input(name))
        try:
            send(inputs)
        except OSError as exc:
            self.held = []
            self.status.configure(text=f"Windows blocked the key press: {exc}", foreground="#b91c1c")
            return
        self.active = True
        self.status.configure(text=f"Holding — press {self.toggle_name.get()} to release", foreground="#15803d")

    def release_all(self):
        if self.active:
            try:
                send([mouse_input(n, True) if n in MOUSE else key_input(n, True) for n in reversed(self.held)])
            except OSError:
                pass
        self.active = False
        self.held = []
        self.status.configure(text="Stopped", foreground="#555")

    def close(self):
        self.release_all()
        if self.hotkey_thread_id:
            user32.PostThreadMessageW(self.hotkey_thread_id, 0x0012, 0, 0)  # WM_QUIT
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    HoldKeysApp(root)
    root.mainloop()
