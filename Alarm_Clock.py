import json
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

# Cross-platform beep support
try:
    import winsound
    PLATFORM = "windows"
except ImportError:
    PLATFORM = "other"


ALARMS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarms.json")


# ----------------------------------------------------------------------
# THEME DEFINITIONS
# ----------------------------------------------------------------------
THEMES = {
    "dark": {
        "bg": "#1e1e2e",
        "panel_bg": "#27293d",
        "fg": "#f5f5f5",
        "subtle_fg": "#a0a0b8",
        "accent": "#7aa2f7",
        "danger": "#f7768e",
        "success": "#9ece6a",
        "warning": "#e0af68",
        "entry_bg": "#313244",
        "list_bg": "#27293d",
        "list_alt_bg": "#2f3149",
        "border": "#3b3d57",
    },
    "light": {
        "bg": "#f4f4f8",
        "panel_bg": "#ffffff",
        "fg": "#1e1e2e",
        "subtle_fg": "#5a5a72",
        "accent": "#3b5bdb",
        "danger": "#d6336c",
        "success": "#2f9e44",
        "warning": "#e8590c",
        "entry_bg": "#eeeef5",
        "list_bg": "#ffffff",
        "list_alt_bg": "#f0f0f7",
        "border": "#dcdce6",
    },
}


class Alarm:
    """Represents a single alarm."""

    def __init__(self, hour, minute, second, repeat_daily=False, enabled=True, alarm_id=None):
        self.hour = int(hour)
        self.minute = int(minute)
        self.second = int(second)
        self.repeat_daily = bool(repeat_daily)
        self.enabled = bool(enabled)
        self.id = alarm_id or f"{time.time_ns()}"

    def time_str(self):
        return f"{self.hour:02d}:{self.minute:02d}:{self.second:02d}"

    def matches(self, now: datetime) -> bool:
        return (
            self.enabled
            and now.hour == self.hour
            and now.minute == self.minute
            and now.second == self.second
        )

    def to_dict(self):
        return {
            "id": self.id,
            "hour": self.hour,
            "minute": self.minute,
            "second": self.second,
            "repeat_daily": self.repeat_daily,
            "enabled": self.enabled,
        }

    @staticmethod
    def from_dict(d):
        return Alarm(
            hour=d.get("hour", 0),
            minute=d.get("minute", 0),
            second=d.get("second", 0),
            repeat_daily=d.get("repeat_daily", False),
            enabled=d.get("enabled", True),
            alarm_id=d.get("id"),
        )


class AlarmClockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alarm Clock")
        self.root.geometry("520x620")
        self.root.minsize(460, 560)

        self.theme_name = "dark"
        self.theme = THEMES[self.theme_name]

        self.alarms = []
        self.load_alarms()

        self._last_triggered_second = None  # avoid re-triggering same second
        self._ringing_alarm_id = None
        self._beep_stop_flag = threading.Event()

        self._build_ui()
        self._apply_theme()
        self._tick()
        self._check_alarms()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # PERSISTENCE
    # ------------------------------------------------------------------
    def load_alarms(self):
        if os.path.exists(ALARMS_FILE):
            try:
                with open(ALARMS_FILE, "r") as f:
                    data = json.load(f)
                self.alarms = [Alarm.from_dict(d) for d in data]
            except (json.JSONDecodeError, OSError):
                self.alarms = []
        else:
            self.alarms = []

    def save_alarms(self):
        try:
            with open(ALARMS_FILE, "w") as f:
                json.dump([a.to_dict() for a in self.alarms], f, indent=2)
        except OSError as e:
            print(f"Failed to save alarms: {e}")

    # ------------------------------------------------------------------
    # UI CONSTRUCTION
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # ---- Top bar: theme toggle ----
        self.top_bar = tk.Frame(self.main_frame)
        self.top_bar.pack(fill="x", padx=16, pady=(12, 0))

        self.title_label = tk.Label(
            self.top_bar, text="⏰ Alarm Clock", font=("Segoe UI", 16, "bold")
        )
        self.title_label.pack(side="left")

        self.theme_btn = tk.Button(
            self.top_bar, text="☀️ Light Mode", command=self._toggle_theme,
            relief="flat", padx=10, pady=4, cursor="hand2"
        )
        self.theme_btn.pack(side="right")

        # ---- Clock display ----
        self.clock_frame = tk.Frame(self.main_frame)
        self.clock_frame.pack(fill="x", padx=16, pady=(10, 6))

        self.time_label = tk.Label(self.clock_frame, text="00:00:00", font=("Consolas", 40, "bold"))
        self.time_label.pack()

        self.date_label = tk.Label(self.clock_frame, text="", font=("Segoe UI", 12))
        self.date_label.pack()

        # ---- Active alarms counter ----
        self.counter_label = tk.Label(self.main_frame, text="", font=("Segoe UI", 10, "bold"))
        self.counter_label.pack(pady=(2, 8))

        # ---- Add alarm panel ----
        self.add_panel = tk.Frame(self.main_frame, relief="flat", bd=0)
        self.add_panel.pack(fill="x", padx=16, pady=(0, 10))

        add_inner = tk.Frame(self.add_panel)
        add_inner.pack(fill="x", padx=14, pady=12)

        tk.Label(add_inner, text="Add Alarm", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=6, sticky="w", pady=(0, 8)
        )

        tk.Label(add_inner, text="HH").grid(row=1, column=0, padx=(0, 4))
        tk.Label(add_inner, text="MM").grid(row=1, column=1, padx=4)
        tk.Label(add_inner, text="SS").grid(row=1, column=2, padx=4)

        self.hour_var = tk.StringVar(value="07")
        self.minute_var = tk.StringVar(value="00")
        self.second_var = tk.StringVar(value="00")

        validate_cmd = (self.root.register(self._validate_numeric), "%P")

        self.hour_entry = tk.Entry(
            add_inner, textvariable=self.hour_var, width=4, justify="center",
            font=("Consolas", 14), validate="key", validatecommand=validate_cmd
        )
        self.minute_entry = tk.Entry(
            add_inner, textvariable=self.minute_var, width=4, justify="center",
            font=("Consolas", 14), validate="key", validatecommand=validate_cmd
        )
        self.second_entry = tk.Entry(
            add_inner, textvariable=self.second_var, width=4, justify="center",
            font=("Consolas", 14), validate="key", validatecommand=validate_cmd
        )

        self.hour_entry.grid(row=2, column=0, padx=(0, 4))
        self.minute_entry.grid(row=2, column=1, padx=4)
        self.second_entry.grid(row=2, column=2, padx=4)

        self.repeat_var = tk.BooleanVar(value=False)
        self.repeat_check = tk.Checkbutton(
            add_inner, text="Repeat Daily", variable=self.repeat_var,
            font=("Segoe UI", 10)
        )
        self.repeat_check.grid(row=2, column=3, padx=(12, 4), sticky="w")

        self.add_btn = tk.Button(
            add_inner, text="➕ Add Alarm", command=self._add_alarm,
            relief="flat", padx=12, pady=6, cursor="hand2", font=("Segoe UI", 10, "bold")
        )
        self.add_btn.grid(row=2, column=4, columnspan=2, padx=(12, 0), sticky="e")

        add_inner.grid_columnconfigure(5, weight=1)

        # ---- Alarms list ----
        list_label_frame = tk.Frame(self.main_frame)
        list_label_frame.pack(fill="x", padx=16)
        tk.Label(list_label_frame, text="Your Alarms", font=("Segoe UI", 11, "bold")).pack(
            side="left", pady=(0, 4)
        )

        self.list_container = tk.Frame(self.main_frame)
        self.list_container.pack(fill="both", expand=True, padx=16, pady=(4, 12))

        self.canvas = tk.Canvas(self.list_container, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", tags="frame")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)       # Windows/Mac
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)         # Linux scroll up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)         # Linux scroll down

        self._refresh_alarm_list()

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig("frame", width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _validate_numeric(self, new_value):
        if new_value == "":
            return True
        if len(new_value) > 2:
            return False
        return new_value.isdigit()

    # ------------------------------------------------------------------
    # THEME HANDLING
    # ------------------------------------------------------------------
    def _toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.theme = THEMES[self.theme_name]
        self._apply_theme()

    def _apply_theme(self):
        t = self.theme
        self.root.configure(bg=t["bg"])
        self.main_frame.configure(bg=t["bg"])
        self.top_bar.configure(bg=t["bg"])
        self.title_label.configure(bg=t["bg"], fg=t["fg"])
        self.theme_btn.configure(
            bg=t["accent"], fg="#ffffff",
            activebackground=t["accent"], activeforeground="#ffffff",
            text=("☀️ Light Mode" if self.theme_name == "dark" else "🌙 Dark Mode")
        )

        self.clock_frame.configure(bg=t["bg"])
        self.time_label.configure(bg=t["bg"], fg=t["accent"])
        self.date_label.configure(bg=t["bg"], fg=t["subtle_fg"])
        self.counter_label.configure(bg=t["bg"], fg=t["success"])

        self.add_panel.configure(bg=t["panel_bg"], highlightbackground=t["border"], highlightthickness=1)
        for child in self.add_panel.winfo_children():
            child.configure(bg=t["panel_bg"])
            for sub in child.winfo_children():
                if isinstance(sub, tk.Label):
                    sub.configure(bg=t["panel_bg"], fg=t["fg"])
                elif isinstance(sub, tk.Checkbutton):
                    sub.configure(
                        bg=t["panel_bg"], fg=t["fg"],
                        activebackground=t["panel_bg"], selectcolor=t["entry_bg"]
                    )
                elif isinstance(sub, tk.Entry):
                    sub.configure(
                        bg=t["entry_bg"], fg=t["fg"],
                        insertbackground=t["fg"], relief="flat",
                        highlightbackground=t["border"], highlightthickness=1
                    )
                elif isinstance(sub, tk.Button):
                    sub.configure(
                        bg=t["success"], fg="#ffffff",
                        activebackground=t["success"], activeforeground="#ffffff"
                    )

        self.list_container.configure(bg=t["bg"])
        self.canvas.configure(bg=t["bg"])
        self.scrollable_frame.configure(bg=t["bg"])

        # Re-render rows with new theme colors
        self._refresh_alarm_list()

    # ------------------------------------------------------------------
    # CLOCK TICK
    # ------------------------------------------------------------------
    def _tick(self):
        now = datetime.now()
        self.time_label.configure(text=now.strftime("%H:%M:%S"))
        self.date_label.configure(text=now.strftime("%A, %B %d, %Y"))
        self.root.after(200, self._tick)

    # ------------------------------------------------------------------
    # ALARM LIST MANAGEMENT
    # ------------------------------------------------------------------
    def _add_alarm(self):
        try:
            h = int(self.hour_var.get() or 0)
            m = int(self.minute_var.get() or 0)
            s = int(self.second_var.get() or 0)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for time.")
            return

        if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
            messagebox.showerror(
                "Invalid Time",
                "Hour must be 0-23, minute and second must be 0-59."
            )
            return

        alarm = Alarm(h, m, s, repeat_daily=self.repeat_var.get())
        self.alarms.append(alarm)
        self.save_alarms()
        self._refresh_alarm_list()

        # Reset the inputs to a friendly default
        self.repeat_var.set(False)

    def _delete_alarm(self, alarm_id):
        self.alarms = [a for a in self.alarms if a.id != alarm_id]
        self.save_alarms()
        self._refresh_alarm_list()

    def _toggle_alarm_enabled(self, alarm_id, var):
        for a in self.alarms:
            if a.id == alarm_id:
                a.enabled = var.get()
        self.save_alarms()
        self._update_counter()

    def _refresh_alarm_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        t = self.theme

        if not self.alarms:
            empty_label = tk.Label(
                self.scrollable_frame,
                text="No alarms yet. Add one above to get started!",
                font=("Segoe UI", 10, "italic"),
                bg=t["bg"], fg=t["subtle_fg"]
            )
            empty_label.pack(pady=24)
        else:
            sorted_alarms = sorted(self.alarms, key=lambda a: (a.hour, a.minute, a.second))
            for i, alarm in enumerate(sorted_alarms):
                row_bg = t["list_bg"] if i % 2 == 0 else t["list_alt_bg"]
                row = tk.Frame(self.scrollable_frame, bg=row_bg, highlightbackground=t["border"],
                                highlightthickness=1)
                row.pack(fill="x", pady=3, padx=1)

                inner = tk.Frame(row, bg=row_bg)
                inner.pack(fill="x", padx=10, pady=8)

                enabled_var = tk.BooleanVar(value=alarm.enabled)
                chk = tk.Checkbutton(
                    inner, variable=enabled_var, bg=row_bg,
                    activebackground=row_bg, selectcolor=t["entry_bg"],
                    command=lambda aid=alarm.id, v=enabled_var: self._toggle_alarm_enabled(aid, v)
                )
                chk.pack(side="left", padx=(0, 8))

                time_lbl = tk.Label(
                    inner, text=alarm.time_str(), font=("Consolas", 16, "bold"),
                    bg=row_bg, fg=t["fg"]
                )
                time_lbl.pack(side="left")

                if alarm.repeat_daily:
                    repeat_lbl = tk.Label(
                        inner, text="🔁 Daily", font=("Segoe UI", 9),
                        bg=row_bg, fg=t["accent"]
                    )
                    repeat_lbl.pack(side="left", padx=(10, 0))

                del_btn = tk.Button(
                    inner, text="🗑️", relief="flat", bg=row_bg, fg=t["danger"],
                    activebackground=row_bg, cursor="hand2", font=("Segoe UI", 11),
                    command=lambda aid=alarm.id: self._delete_alarm(aid)
                )
                del_btn.pack(side="right")

        self._update_counter()

    def _update_counter(self):
        active = sum(1 for a in self.alarms if a.enabled)
        total = len(self.alarms)
        self.counter_label.configure(
            text=f"📊 {active} active alarm{'s' if active != 1 else ''} (of {total} total)"
        )

    # ------------------------------------------------------------------
    # ALARM CHECKING LOOP
    # ------------------------------------------------------------------
    def _check_alarms(self):
        now = datetime.now()
        current_key = now.strftime("%H:%M:%S")

        if current_key != self._last_triggered_second:
            self._last_triggered_second = current_key
            if self._ringing_alarm_id is None:  # only trigger if nothing currently ringing
                for alarm in self.alarms:
                    if alarm.matches(now):
                        self._trigger_alarm(alarm)
                        break

        self.root.after(500, self._check_alarms)

    def _trigger_alarm(self, alarm: Alarm):
        self._ringing_alarm_id = alarm.id
        self._beep_stop_flag.clear()

        # Play beeps in a background thread so the UI doesn't freeze
        beep_thread = threading.Thread(target=self._play_beeps, daemon=True)
        beep_thread.start()

        self._show_ringing_popup(alarm)

    def _play_beeps(self, count=5):
        for _ in range(count):
            if self._beep_stop_flag.is_set():
                return
            if PLATFORM == "windows":
                try:
                    winsound.Beep(1000, 400)
                except RuntimeError:
                    print("\a", end="", flush=True)
            else:
                print("\a", end="", flush=True)  # terminal bell fallback
            time.sleep(0.5)

    def _show_ringing_popup(self, alarm: Alarm):
        t = self.theme
        popup = tk.Toplevel(self.root)
        popup.title("⏰ Alarm Ringing!")
        popup.geometry("360x220")
        popup.resizable(False, False)
        popup.configure(bg=t["panel_bg"])
        popup.attributes("-topmost", True)
        popup.grab_set()

        # Center the popup over the main window
        popup.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 180
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 110
        popup.geometry(f"+{x}+{y}")

        tk.Label(
            popup, text="⏰ Wake Up!", font=("Segoe UI", 20, "bold"),
            bg=t["panel_bg"], fg=t["accent"]
        ).pack(pady=(20, 6))

        tk.Label(
            popup, text=f"Alarm set for {alarm.time_str()}",
            font=("Segoe UI", 12), bg=t["panel_bg"], fg=t["fg"]
        ).pack(pady=(0, 20))

        btn_frame = tk.Frame(popup, bg=t["panel_bg"])
        btn_frame.pack()

        def stop_action():
            self._stop_alarm(alarm, popup)

        def snooze_action():
            self._snooze_alarm(alarm, popup)

        stop_btn = tk.Button(
            btn_frame, text="🛑 Stop", font=("Segoe UI", 11, "bold"),
            bg=t["danger"], fg="#ffffff", activebackground=t["danger"],
            relief="flat", padx=16, pady=8, cursor="hand2", command=stop_action
        )
        stop_btn.grid(row=0, column=0, padx=8)

        snooze_btn = tk.Button(
            btn_frame, text="😴 Snooze 5 min", font=("Segoe UI", 11, "bold"),
            bg=t["warning"], fg="#ffffff", activebackground=t["warning"],
            relief="flat", padx=16, pady=8, cursor="hand2", command=snooze_action
        )
        snooze_btn.grid(row=0, column=1, padx=8)

        # If the user closes the popup via the window manager, treat it as "Stop"
        popup.protocol("WM_DELETE_WINDOW", stop_action)

    def _stop_alarm(self, alarm: Alarm, popup):
        self._beep_stop_flag.set()
        self._ringing_alarm_id = None
        popup.destroy()

        if alarm.repeat_daily:
            # Daily alarms simply remain enabled and will fire again tomorrow
            pass
        else:
            # One-time alarms are disabled after ringing (kept in list, unchecked)
            for a in self.alarms:
                if a.id == alarm.id:
                    a.enabled = False
            self.save_alarms()
            self._refresh_alarm_list()

    def _snooze_alarm(self, alarm: Alarm, popup):
        self._beep_stop_flag.set()
        self._ringing_alarm_id = None
        popup.destroy()

        snooze_time = datetime.now() + timedelta(minutes=5)
        snoozed = Alarm(
            hour=snooze_time.hour,
            minute=snooze_time.minute,
            second=snooze_time.second,
            repeat_daily=False,
            enabled=True,
        )
        self.alarms.append(snoozed)

        if not alarm.repeat_daily:
            for a in self.alarms:
                if a.id == alarm.id:
                    a.enabled = False

        self.save_alarms()
        self._refresh_alarm_list()
        messagebox.showinfo(
            "Snoozed",
            f"Alarm snoozed until {snooze_time.strftime('%H:%M:%S')}."
        )

    # ------------------------------------------------------------------
    # SHUTDOWN
    # ------------------------------------------------------------------
    def _on_close(self):
        self._beep_stop_flag.set()
        self.save_alarms()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = AlarmClockApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
