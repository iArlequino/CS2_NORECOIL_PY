import win32api
import win32con
import time
import keyboard
import ctypes
import winsound
import os
import tkinter as tk
from tkinter import ttk
import json
from queue import Queue
import threading
import numpy as np

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_MOVE = 0x0001
ZOOM_SENS = 1.2  # Zoom sensitivity multiplier

# Additional Constants
VK_SPACE = 0x20
VK_MBUTTON = 0x04
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Weapon patterns
PATTERNS = {
    'ak47': [
        (-4, 7), (4, 19), (-3, 29), (-1, 31), (13, 31),
        (8, 28), (13, 21), (-17, 12), (-42, -3), (-21, 2),
        (12, 11), (-15, 7), (-26, -8), (-3, 4), (40, 1),
        (19, 7), (14, 10), (27, 0), (33, -10), (-21, -2),
        (7, 3), (-7, 9), (-8, 4), (19, -3), (5, 6),
        (-20, -1), (-33, -4), (-45, -21), (-14, 1)
    ],
    'm4a1': [
        (1, 6), (0, 4), (-4, 14), (4, 18), (-6, 21),
        (-4, 24), (14, 14), (8, 12), (18, 5), (-4, 10),
        (-14, 5), (-25, -3), (-19, 0), (-22, -3), (1, 3),
        (8, 3), (-9, 1), (-13, -2), (3, 2), (1, 1)
    ],
    'm4a4': [
        (2, 7), (0, 9), (-6, 16), (7, 21), (-9, 23),
        (-5, 27), (16, 15), (11, 13), (22, 5), (-4, 11),
        (-18, 6), (-30, -4), (-24, 0), (-25, -6), (0, 4),
        (8, 4), (-11, 1), (-13, -2), (2, 2), (33, -1),
        (10, 6), (27, 3), (10, 2), (11, 0), (-12, 0),
        (6, 5), (4, 5), (3, 1), (4, -1)
    ],
    'famas': [
        (-4, 5), (1, 4), (-6, 10), (-1, 17), (0, 20),
        (14, 18), (16, 12), (-6, 12), (-20, 8), (-16, 5),
        (-13, 2), (4, 5), (23, 4), (12, 6), (20, -3),
        (5, 0), (15, 0), (3, 5), (-4, 3), (-25, -1),
        (-3, 2), (11, 0), (15, -7), (15, -10)
    ],
    'galil': [
        (4, 4), (-2, 5), (6, 10), (12, 15), (-1, 21),
        (2, 24), (6, 16), (11, 10), (-4, 14), (-22, 8),
        (-30, -3), (-29, -13), (-9, 8), (-12, 2), (-7, 1),
        (0, 1), (4, 7), (25, 7), (14, 4), (25, -3),
        (31, -9), (6, 3), (-12, 3), (13, -1), (10, -1),
        (16, -4), (-9, 5), (-32, -5), (-24, -3), (-15, 5),
        (6, 8), (-14, -3), (-24, -14), (-13, -1)
    ],
    'ump': [
        (-1, 6), (-4, 8), (-2, 18), (-4, 23), (-9, 23),
        (-3, 26), (11, 17), (-4, 12), (9, 13), (18, 8),
        (15, 5), (-1, 3), (5, 6), (0, 6), (9, -3),
        (5, -1), (-12, 4), (-19, 1), (-1, -2), (15, -5),
        (17, -2), (-6, 3), (-20, -2), (-3, -1)
    ],
    'aug': [
        (5, 6), (0, 13), (-5, 22), (-7, 26), (5, 29),
        (9, 30), (14, 21), (6, 15), (14, 13), (-16, 11),
        (-5, 6), (13, 0), (1, 6), (-22, 5), (-38, -11),
        (-31, -13), (-3, 6), (-5, 5), (-9, 0), (24, 1),
        (32, 3), (15, 6), (-5, 1), (17, -3), (29, -11),
        (19, 0), (-16, 6), (-16, 3), (-4, 1)
    ],
    'sg': [
        (-4, 9), (-13, 15), (-9, 25), (-6, 29), (-8, 31),
        (-7, 36), (-20, 14), (14, 17), (-8, 12), (-15, 8),
        (-5, 5), (6, 5), (-8, 6), (2, 11), (-14, -6),
        (-20, -17), (-18, -9), (-8, -2), (41, 3), (56, -5),
        (43, -1), (18, 9), (14, 9), (6, 7), (21, -3),
        (29, -4), (-6, 8), (-15, 5), (-38, -5)
    ]
}

WEAPON_KEYS = {
    'f4': 'ak47',
    'f6': 'm4a1',
    'f7': 'm4a4',
    'f8': 'famas',
    'f9': 'galil',
    'f12': 'ump',
    'home': 'aug',
    'end': 'sg'
}

def mouse_move(x, y, modifier=1, zoom=False):
    if zoom:
        zoom_modifier = ZOOM_SENS/1.2
        x = int(x * modifier * zoom_modifier)
        y = int(y * modifier * zoom_modifier)
    else:
        x = int(x * modifier)
        y = int(y * modifier)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, x, y, 0, 0)

def interpolate_pattern(pattern, smoothness):
    if smoothness == 0:
        return pattern
        
    points = np.array(pattern)
    num_points = len(pattern)
    new_points_count = num_points + int(num_points * (smoothness / 100))
    
    t = np.linspace(0, num_points - 1, num_points)
    t_new = np.linspace(0, num_points - 1, new_points_count)
    
    x_interpolated = np.interp(t_new, t, points[:, 0])
    y_interpolated = np.interp(t_new, t, points[:, 1])
    
    smoothed_pattern = list(zip(x_interpolated, y_interpolated))
    return smoothed_pattern

class RecoilControlGUI:
    def __init__(self, control, queue):
        self.control = control
        self.queue = queue
        self.root = tk.Tk()
        self.root.title("CS2 ROFLS")
        self.root.geometry("400x800")
        self.root.resizable(False, False)
        self.sensitivity = tk.StringVar(value="3.0")
        self.base_modifier = 2.5
        self.smoothness = tk.IntVar(value=0)
        
        self.setup_gui()
        
        self.check_queue()
        
    def setup_gui(self):
        status_frame = ttk.LabelFrame(self.root, text="Status", padding=10)
        status_frame.pack(fill="x", padx=5, pady=5)
        
        self.enabled_label = ttk.Label(status_frame, text="Disabled", foreground="red")
        self.enabled_label.pack()
        
        features_frame = ttk.LabelFrame(self.root, text="Features", padding=10)
        features_frame.pack(fill="x", padx=5, pady=5)
        
        self.bhop_label = ttk.Label(features_frame, text="Bhop: OFF", foreground="red")
        self.bhop_label.pack()
        
        self.rapid_fire_label = ttk.Label(features_frame, text="Rapid Fire: OFF", foreground="red")
        self.rapid_fire_label.pack()
        
        self.current_weapon_label = ttk.Label(features_frame, text="Current Weapon: None")
        self.current_weapon_label.pack()
        
        binds_frame = ttk.LabelFrame(self.root, text="Weapon Binds", padding=10)
        binds_frame.pack(fill="x", padx=5, pady=5)
        
        self.bind_entries = {}
        row = 0
        for weapon in PATTERNS.keys():
            ttk.Label(binds_frame, text=weapon.upper()).grid(row=row, column=0, padx=5, pady=2)
            entry = ttk.Entry(binds_frame, width=10)
            entry.insert(0, next(key for key, val in WEAPON_KEYS.items() if val == weapon))
            entry.grid(row=row, column=1, padx=5, pady=2)
            self.bind_entries[weapon] = entry
            row += 1
            
        ttk.Button(binds_frame, text="Save Binds", command=self.save_binds).grid(row=row, column=0, columnspan=2, pady=10)
        
        info_frame = ttk.LabelFrame(self.root, text="Information", padding=10)
        info_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(info_frame, text="CAPSLOCK - Toggle globally\nESC - Exit\nF1 - Toggle Bhop\nF2 - Toggle Rapid Fire").pack()
        
        sens_frame = ttk.LabelFrame(self.root, text="Sensitivity Settings", padding=10)
        sens_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(sens_frame, text="Game Sensitivity:").pack(side=tk.LEFT, padx=5)
        sens_entry = ttk.Entry(sens_frame, width=10, textvariable=self.sensitivity)
        sens_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(sens_frame, text="Apply", command=self.update_sensitivity).pack(side=tk.LEFT, padx=5)
        
        smooth_frame = ttk.LabelFrame(self.root, text="Pattern Smoothness", padding=10)
        smooth_frame.pack(fill="x", padx=5, pady=5)
        
        self.smooth_label = ttk.Label(smooth_frame, text="Smoothness: 0%")
        self.smooth_label.pack()
        
        smooth_slider = ttk.Scale(
            smooth_frame,
            from_=0,
            to=100,
            orient='horizontal',
            variable=self.smoothness,
            command=self.update_smoothness
        )
        smooth_slider.pack(fill='x', padx=5)
        
    def update_sensitivity(self):
        try:
            sens = float(self.sensitivity.get())
            if sens <= 0:
                raise ValueError
            self.control.update_modifier(self.base_modifier / sens)
            self.save_settings()
        except ValueError:
            self.sensitivity.set("3.0")
            self.control.update_modifier(self.base_modifier / 3.0)
            
    def update_smoothness(self, *args):
        value = self.smoothness.get()
        self.smooth_label.config(text=f"Smoothness: {value}%")
        self.control.update_smoothness(value)
        self.save_settings()
        
    def save_binds(self):
        new_binds = {}
        for weapon, entry in self.bind_entries.items():
            new_binds[entry.get().lower()] = weapon
        
        global WEAPON_KEYS
        WEAPON_KEYS = new_binds
        
        with open(os.path.join(SCRIPT_DIR, 'binds.json'), 'w') as f:
            json.dump(new_binds, f)
        self.save_settings()
            
    def save_settings(self):
        settings = {
            'sensitivity': float(self.sensitivity.get()),
            'smoothness': self.smoothness.get(),
            'binds': WEAPON_KEYS
        }
        with open(os.path.join(SCRIPT_DIR, 'settings.json'), 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open(os.path.join(SCRIPT_DIR, 'settings.json'), 'r') as f:
                settings = json.load(f)
                self.sensitivity.set(str(settings.get('sensitivity', 3.0)))
                self.update_sensitivity()
                self.smoothness.set(settings.get('smoothness', 0))
                self.update_smoothness()
        except:
            self.sensitivity.set("3.0")
            self.update_sensitivity()
            
    def check_queue(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg == "quit":
                    self.root.quit()
                    return
        except:
            pass
            
        self.enabled_label.config(
            text="Enabled" if self.control.enabled else "Disabled",
            foreground="green" if self.control.enabled else "red"
        )
        
        self.bhop_label.config(
            text=f"Bhop: {'ON' if self.control.bhop_enabled else 'OFF'}",
            foreground="green" if self.control.bhop_enabled else "red"
        )
        
        self.rapid_fire_label.config(
            text=f"Rapid Fire: {'ON' if self.control.rapid_fire_enabled else 'OFF'}",
            foreground="green" if self.control.rapid_fire_enabled else "red"
        )
        
        self.current_weapon_label.config(
            text=f"Current Weapon: {self.control.current_weapon.upper()}"
        )
        
        self.root.after(100, self.check_queue)

class RecoilControl:
    def __init__(self):
        self.enabled = False
        self.modifier = 1
        self.current_weapon = 'ak47'
        self.bhop_enabled = False
        self.rapid_fire_enabled = False
        self.queue = Queue()
        self.running = True
        self.load_binds()
        self.base_modifier = 2.5
        self.modifier = self.base_modifier / 3.0
        self.smoothness = 0
        self.smoothed_patterns = {weapon: pattern for weapon, pattern in PATTERNS.items()}
        
    def load_binds(self):
        try:
            with open(os.path.join(SCRIPT_DIR, 'binds.json'), 'r') as f:
                global WEAPON_KEYS
                WEAPON_KEYS = json.load(f)
        except:
            pass
            
    def toggle_bhop(self):
        self.bhop_enabled = not self.bhop_enabled
        winsound.PlaySound(os.path.join(SCRIPT_DIR, '12.mp3'), winsound.SND_ASYNC)
        print(f"Bhop {'enabled' if self.bhop_enabled else 'disabled'}")
        
    def toggle_rapid_fire(self):
        self.rapid_fire_enabled = not self.rapid_fire_enabled
        winsound.PlaySound(os.path.join(SCRIPT_DIR, '13.mp3'), winsound.SND_ASYNC)
        print(f"Rapid fire {'enabled' if self.rapid_fire_enabled else 'disabled'}")

    def handle_bhop(self):
        if self.bhop_enabled and keyboard.is_pressed('space'):
            ctypes.windll.user32.keybd_event(VK_SPACE, 0, 0, 0)
            time.sleep(0.001)
            ctypes.windll.user32.keybd_event(VK_SPACE, 0, 2, 0)

    def handle_rapid_fire(self):
        if self.rapid_fire_enabled and win32api.GetKeyState(VK_MBUTTON) < 0:
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.001)
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def update_modifier(self, new_modifier):
        self.modifier = new_modifier
        print(f"Sensitivity modifier updated to: {self.modifier:.2f}")

    def update_smoothness(self, value):
        self.smoothness = value
        self.smoothed_patterns = {
            weapon: interpolate_pattern(pattern, value)
            for weapon, pattern in PATTERNS.items()
        }
        print(f"Pattern smoothness updated to: {value}%")

    def control_loop(self):
        while self.running:
            if keyboard.is_pressed('f1'):
                self.toggle_bhop()
                time.sleep(0.3)
            if keyboard.is_pressed('f2'):
                self.toggle_rapid_fire()
                time.sleep(0.3)

            self.handle_bhop()
            self.handle_rapid_fire()

            # Weapon selection
            for key, weapon in WEAPON_KEYS.items():
                if keyboard.is_pressed(key):
                    self.current_weapon = weapon
                    print(f"Selected weapon: {weapon.upper()}")
                    time.sleep(0.3)

            caps_state = win32api.GetKeyState(win32con.VK_CAPITAL)
            lmb_state = win32api.GetKeyState(0x01)
            rmb_state = win32api.GetKeyState(0x02)
            
            if caps_state & 0x1:
                self.enabled = True
            else:
                self.enabled = False
                
            if self.enabled and lmb_state < 0:
                pattern = self.smoothed_patterns[self.current_weapon]
                pattern_complete = False
                
                for x, y in pattern:
                    current_lmb_state = win32api.GetKeyState(0x01)
                    current_rmb_state = win32api.GetKeyState(0x02)
                    
                    if current_lmb_state >= 0 or not self.enabled:
                        break
                        
                    is_zoomed = self.current_weapon in ['aug', 'sg'] and current_rmb_state < 0
                    mouse_move(x, y, self.modifier, is_zoomed)
                    time.sleep(0.099)
                else:
                    pattern_complete = True
                
                if pattern_complete:
                    while win32api.GetKeyState(0x01) < 0 and self.enabled:
                        time.sleep(0.001)
            
            time.sleep(0.001)

    def run(self):
        control_thread = threading.Thread(target=self.control_loop)
        control_thread.daemon = True
        control_thread.start()

        self.gui = RecoilControlGUI(self, self.queue)
        self.gui.load_settings()  # Загружаем настройки
        self.gui.root.mainloop()

        self.running = False
        control_thread.join()

def main():
    control = RecoilControl()
    control.run()

if __name__ == "__main__":
    main()
