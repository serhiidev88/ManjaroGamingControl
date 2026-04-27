import customtkinter as ctk
import tkinter as tk
import subprocess
import threading
import os
import glob
import time
import json
import urllib.request
import webbrowser
from datetime import datetime
import signal
import sys

# Импортируем настройки темы и наши модули вкладок
from theme import FONTS, DIMENSIONS, DARK_MODE, LIGHT_MODE
from about import AboutPage, ABOUT_LANGUAGES
from clean import CleanPage, CLEAN_LANGUAGES
from optimization import OptimizationPage, OPT_LANGUAGES

ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)

# --- УЛУЧШЕННАЯ ФУНКЦИЯ ПУТЕЙ (ДЛЯ PYINSTALLER 6+) ---
def resource_path(relative_path):
    """ Находит путь к файлу, учитывая структуру _internal в PyInstaller """
    try:
        # PyInstaller создает временную папку _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    # Сначала ищем в корне (для обычного запуска)
    path = os.path.join(base_path, relative_path)

    # Если файла нет и мы в сборке, ищем внутри папки _internal
    if not os.path.exists(path):
        path = os.path.join(base_path, "_internal", relative_path)

    return path

# ==================== ГЛАВНЫЙ СЛОВАРЬ ПЕРЕВОДОВ ====================
LANGUAGES = {
    "en": {
        "menu_home": "Home", "menu_clean": "System Clean", "menu_gpu": "Hardware & Drivers",
        "menu_game": "Game Optimization", "menu_overheat": "Overheat Protect",
        "menu_settings": "Settings", "menu_about": "About", "menu_log": "App Log",

        "tab_home_title": "Dashboard", "tt_home": "Welcome to Manjaro Gaming Control.\nHere you can see the overall status of your system at a glance.",
        "tab_nv_title": "Hardware & Drivers", "tt_nv": "Hardware detection, GPU driver updates, and safe rollbacks.\nKeep your system stable and fast.",
        "tab_overheat_title": "Overheat Protection", "tt_overheat": "Monitor temperatures, configure dynamic graphs, and set overheat alarms.",
        "set_title": "Application Settings", "tt_set": "Customize the app appearance and language.",
        "tab_log_title": "Developer Log", "tt_log": "Global application log to track errors and background commands.",

        "home_hero": "Get In. Game On.", "home_sub": "Optimize your Manjaro Linux for maximum performance.",
        "home_news_title": "Latest News & Tips", "news_1": "• Tip: Turn on Performance Mode before playing heavy games.\n• Clear shader cache if you experience micro-stuttering.",

        "btn_refresh": "Refresh Data", "lbl_nv_rollback": "Driver Rollback (Cache):", "btn_rollback": "Rollback",
        "lbl_lang": "Language:", "lbl_theme": "Theme:",
        "lbl_alarm": "Overheat Alarm Limit (°C):", "lbl_sound": "Alarm Sound:", "btn_test_sound": "Test Sound",
        "lbl_thresh_title": "Graph Color Thresholds (°C):", "lbl_yellow": "Yellow (Warm):", "lbl_red": "Red (Hot):",
        "theme_dark": "Dark", "theme_light": "Light",
        "btn_clear_log": "Clear Log", "graph_title": "Live Temperature Graph",
        "sw_prot_on": "Protection ON", "sw_prot_off": "Protection OFF", "time_1m": "1 Min", "time_5m": "5 Min",
    },
    "ru": {
        "menu_home": "Главная", "menu_clean": "Очистка системы", "menu_gpu": "Железо и Драйверы",
        "menu_game": "Оптимизация для игр", "menu_overheat": "Защита от перегрева",
        "menu_settings": "Настройки", "menu_about": "О программе", "menu_log": "Лог (Log)",

        "tab_home_title": "Обзор системы", "tt_home": "Добро пожаловать в Manjaro Gaming Control.\nЗдесь отображается общий статус вашего ПК.",
        "tab_nv_title": "Железо и Драйверы", "tt_nv": "Определение видеокарты, обновление и откат драйверов.\nПомогает держать систему стабильной и быстрой.",
        "tab_overheat_title": "Защита от перегрева", "tt_overheat": "Настройте звуковую тревогу и цвета графика для мониторинга температур.",
        "set_title": "Настройки приложения", "tt_set": "Здесь можно изменить язык интерфейса и визуальную тему.",
        "tab_log_title": "Лог для разработчика", "tt_log": "Глобальный журнал работы программы для отслеживания ошибок и команд.",

        "home_hero": "Войди в Игру.", "home_sub": "Эксклюзивная оптимизация Manjaro Linux для геймеров.",
        "home_news_title": "Новости и Советы", "news_1": "• Совет: Включайте Режим Производительности перед запуском тяжелых игр.\n• Очищайте кэш шейдеров при появлении микро-фризов в играх.",

        "btn_refresh": "Обновить данные", "lbl_nv_rollback": "Откат драйвера (из кэша):", "btn_rollback": "Выполнить откат",
        "lbl_lang": "Язык (Language):", "lbl_theme": "Тема оформления:",
        "lbl_alarm": "Лимит тревоги (Сирена) °C:", "lbl_sound": "Звук сирены:", "btn_test_sound": "Проверить",
        "lbl_thresh_title": "Цвета графика (Пороги °C):", "lbl_yellow": "Желтый (Нагрев):", "lbl_red": "Красный (Горячо):",
        "theme_dark": "Темная", "theme_light": "Светлая",
        "btn_clear_log": "Очистить лог", "graph_title": "График температур",
        "sw_prot_on": "Защита включена", "sw_prot_off": "Защита отключена", "time_1m": "1 Мин", "time_5m": "5 Мин",
    }
}

# Склеиваем словари из всех файлов в один глобальный
for lang in ["en", "ru"]:
    LANGUAGES[lang].update(ABOUT_LANGUAGES[lang])
    LANGUAGES[lang].update(CLEAN_LANGUAGES[lang])
    LANGUAGES[lang].update(OPT_LANGUAGES[lang])

SOUND_FILES = {
    "Siren (3x Warning)": {"file": "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga", "loops": 3},
    "Alarm Clock (Long)": {"file": "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga", "loops": 1},
    "Phone Ring": {"file": "/usr/share/sounds/freedesktop/stereo/phone-incoming-call.oga", "loops": 1},
    "Error (Short)": {"file": "/usr/share/sounds/freedesktop/stereo/dialog-error.oga", "loops": 1},
    "Sonar (Short)": {"file": "/usr/share/sounds/freedesktop/stereo/bell.oga", "loops": 1}
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Manjaro Gaming Control v1.0.0")
        self.geometry("1200x900")
        self.minsize(1050, 800)

        # Загрузка иконки через resource_path
        try:
            icon_path = resource_path("icon.png")
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.wm_iconphoto(True, img)
        except: pass

        self.bg_frames = []
        self.card_frames = []
        self.consoles = []
        self.accent_labels = []
        self.primary_buttons = []
        self.checkboxes = []
        self.info_icons = []

        self.nav_text_color_idle = DARK_MODE["nav_text_idle"]
        self.nav_text_color_active = DARK_MODE["nav_text_active"]
        self.nav_bg_color_active = DARK_MODE["primary_color"]
        self.current_text_color = DARK_MODE["text_main"]
        self.current_card_color = DARK_MODE["card_color"]

        self.lang = "en"
        self.last_alarm_time = 0

        self.temp_history = {"GPU": [], "CPU": []}
        self.current_graph_points = []
        self.last_mouse_x = None

        self.main_font = ctk.CTkFont(family=FONTS["main_family"], size=FONTS["main_size"])
        self.title_font = ctk.CTkFont(family=FONTS["title_family"], size=FONTS["title_size"], weight=FONTS["title_weight"])
        self.console_font = ctk.CTkFont(family=FONTS["console_family"], size=FONTS["console_size"])
        self.hero_font = ctk.CTkFont(family=FONTS["hero_family"], size=FONTS["hero_size"], weight="bold")
        self.logo_font = ctk.CTkFont(family=FONTS["logo_family"], size=FONTS["logo_size"], weight="bold")
        self.subtitle_font = ctk.CTkFont(family=FONTS["main_family"], size=18, weight="bold")

        self.cached_drivers = {}
        self.current_driver_ver = "0"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_ui()
        self.update_texts()
        self.change_theme("Dark")
        self.show_home_frame()

        self.app_log("=== MANJARO GAMING CONTROL v1.0.0 STARTED ===")
        self.app_log("Theme applied. Initializing auto-refresh system.")
        self.auto_refresh_system()

    def t(self, key): return LANGUAGES[self.lang].get(key, key)

    def get_btn_style(self):
        return {
            "corner_radius": DIMENSIONS["corner_radius"],
            "height": DIMENSIONS["btn_height"],
            "font": ctk.CTkFont(family=FONTS["main_family"], size=FONTS["btn_size"], weight="bold")
        }

    def get_cb_style(self):
        return {
            "checkbox_width": DIMENSIONS["checkbox_size"],
            "checkbox_height": DIMENSIONS["checkbox_size"],
            "border_width": DIMENSIONS["checkbox_border"],
            "corner_radius": DIMENSIONS["corner_radius"],
            "font": self.main_font
        }

    def play_sound(self, is_timer=False):
        def _play():
            try:
                if is_timer:
                    file_path = "/usr/share/sounds/freedesktop/stereo/message.oga"
                    loops = 1
                else:
                    chosen = self.combo_sound.get()
                    config = SOUND_FILES.get(chosen, SOUND_FILES["Siren (3x Warning)"])
                    file_path = config["file"]
                    loops = config["loops"]

                for _ in range(loops):
                    if os.path.exists(file_path):
                        subprocess.run(["paplay", file_path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                    else:
                        print('\a', end='', flush=True)
                        time.sleep(0.5)
            except: pass
        threading.Thread(target=_play, daemon=True).start()

    def app_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        def write_to_ui():
            if hasattr(self, 'dev_log_box'):
                self.dev_log_box.configure(state="normal")
                self.dev_log_box.insert("end", log_line)
                self.dev_log_box.see("end")
                self.dev_log_box.configure(state="disabled")
        self.after(0, write_to_ui)

    def clear_app_log(self):
        self.dev_log_box.configure(state="normal")
        self.dev_log_box.delete("0.0", "end")
        self.dev_log_box.configure(state="disabled")
        self.app_log("Log cleared.")

    def get_cpu_temp(self):
        max_temp = 0
        try:
            for zone in glob.glob('/sys/class/thermal/thermal_zone*/temp'):
                with open(zone, 'r') as f:
                    temp_val = int(f.read().strip()) / 1000.0
                    if temp_val > max_temp and temp_val < 150:
                        max_temp = temp_val
        except: pass
        return int(max_temp)

    def build_tooltip_engine(self):
        self.tooltip_frame = ctk.CTkFrame(self, corner_radius=0, border_width=2)
        self.tooltip_label = ctk.CTkLabel(self.tooltip_frame, text="", font=self.main_font, justify="left")
        self.tooltip_label.pack(padx=20, pady=15)

    def show_tooltip(self, widget, text_key):
        self.tooltip_label.configure(text=self.t(text_key))
        x = widget.winfo_rootx() - self.winfo_rootx() + 40
        y = widget.winfo_rooty() - self.winfo_rooty() + 20
        self.tooltip_frame.place(x=x, y=y)
        self.tooltip_frame.lift()

    def hide_tooltip(self, event=None):
        self.tooltip_frame.place_forget()

    def create_title(self, parent, title_key, tooltip_key):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=0, columnspan=3, padx=DIMENSIONS["pad_window"], pady=(30, 20), sticky="w")
        lbl_title = ctk.CTkLabel(frame, text=self.t(title_key), font=self.title_font)
        lbl_title.pack(side="left")
        self.accent_labels.append(lbl_title)
        icon = ctk.CTkLabel(frame, text=" ( i ) ", font=ctk.CTkFont(family=FONTS["main_family"], size=22, weight="bold"), cursor="hand2")
        icon.pack(side="left", padx=20)
        self.info_icons.append(icon)
        icon.bind("<Enter>", lambda e: self.show_tooltip(icon, tooltip_key))
        icon.bind("<Leave>", self.hide_tooltip)
        return lbl_title

    def build_ui(self):
        self.build_tooltip_engine()

        sidebar_width = DIMENSIONS.get("sidebar_width", 250)
        self.sidebar_frame = ctk.CTkFrame(self, width=sidebar_width, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="MANJARO\nGAMING CONTROL", font=self.logo_font)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(40, 50))

        btn_nav_style = {
            "corner_radius": DIMENSIONS["corner_radius"], "height": DIMENSIONS["nav_btn_height"],
            "fg_color": "transparent", "anchor": "w", "font": ctk.CTkFont(family=FONTS["main_family"], size=FONTS["btn_size"], weight="bold")
        }

        self.btn_nav_home = ctk.CTkButton(self.sidebar_frame, command=self.show_home_frame, **btn_nav_style)
        self.btn_nav_clean = ctk.CTkButton(self.sidebar_frame, command=self.show_clean_frame, **btn_nav_style)
        self.btn_nav_info = ctk.CTkButton(self.sidebar_frame, command=self.show_info_frame, **btn_nav_style)
        self.btn_nav_game = ctk.CTkButton(self.sidebar_frame, command=self.show_game_frame, **btn_nav_style)
        self.btn_nav_overheat = ctk.CTkButton(self.sidebar_frame, command=self.show_overheat_frame, **btn_nav_style)
        self.btn_nav_settings = ctk.CTkButton(self.sidebar_frame, command=self.show_settings_frame, **btn_nav_style)
        self.btn_nav_about = ctk.CTkButton(self.sidebar_frame, command=self.show_about_frame, **btn_nav_style)
        self.btn_nav_log = ctk.CTkButton(self.sidebar_frame, command=self.show_log_frame, **btn_nav_style)

        main_btns = [self.btn_nav_home, self.btn_nav_clean, self.btn_nav_info, self.btn_nav_game, self.btn_nav_overheat, self.btn_nav_settings, self.btn_nav_about]
        for i, btn in enumerate(main_btns):
            btn.grid(row=i+1, column=0, padx=0, pady=2, sticky="ew")

        self.sidebar_frame.grid_rowconfigure(8, weight=1)
        self.btn_nav_log.grid(row=9, column=0, padx=0, pady=(0, 20), sticky="ew")

        self.home_frame = ctk.CTkFrame(self, corner_radius=0)
        self.clean_frame = ctk.CTkFrame(self, corner_radius=0)
        self.info_frame = ctk.CTkFrame(self, corner_radius=0)
        self.game_frame = ctk.CTkFrame(self, corner_radius=0)
        self.overheat_frame = ctk.CTkFrame(self, corner_radius=0)
        self.settings_frame = ctk.CTkFrame(self, corner_radius=0)
        self.about_frame = ctk.CTkFrame(self, corner_radius=0)
        self.log_frame = ctk.CTkFrame(self, corner_radius=0)

        self.bg_frames.extend([self.home_frame, self.clean_frame, self.info_frame, self.game_frame, self.overheat_frame, self.settings_frame, self.about_frame, self.log_frame])

        self.build_home_frame()

        self.clean_page = CleanPage(self, self.clean_frame)
        self.build_info_frame()
        self.optimization_page = OptimizationPage(self, self.game_frame)
        self.build_overheat_frame()
        self.build_settings_frame()
        self.about_page = AboutPage(self, self.about_frame)

        self.build_log_frame()

    def build_log_frame(self):
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(2, weight=1)
        self.lbl_log_title = self.create_title(self.log_frame, "tab_log_title", "tt_log")
        self.btn_clear_log = ctk.CTkButton(self.log_frame, text="", fg_color="#555555", hover_color="#333333", command=self.clear_app_log, **self.get_btn_style())
        self.btn_clear_log.grid(row=1, column=0, padx=DIMENSIONS["pad_window"], pady=(0, 10), sticky="w")
        self.dev_log_box = ctk.CTkTextbox(self.log_frame, font=self.console_font, corner_radius=DIMENSIONS["corner_radius"])
        self.dev_log_box.grid(row=2, column=0, padx=DIMENSIONS["pad_window"], pady=(10, DIMENSIONS["pad_window"]), sticky="nsew")
        self.consoles.append(self.dev_log_box)

    def build_home_frame(self):
        self.home_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.home_frame.grid_rowconfigure(3, weight=1)
        self.lbl_home_title = self.create_title(self.home_frame, "tab_home_title", "tt_home")

        self.hero_card = ctk.CTkFrame(self.home_frame, corner_radius=DIMENSIONS["corner_radius"])
        self.hero_card.grid(row=1, column=0, columnspan=3, padx=DIMENSIONS["pad_window"], pady=(0, 20), sticky="nsew")
        self.card_frames.append(self.hero_card)

        self.lbl_hero_title = ctk.CTkLabel(self.hero_card, text="", font=self.hero_font)
        self.lbl_hero_title.pack(pady=(40, 10), padx=40, anchor="w")
        self.accent_labels.append(self.lbl_hero_title)
        self.lbl_hero_sub = ctk.CTkLabel(self.hero_card, text="", font=self.main_font)
        self.lbl_hero_sub.pack(pady=(0, 40), padx=40, anchor="w")

        self.tile1 = ctk.CTkFrame(self.home_frame, corner_radius=DIMENSIONS["corner_radius"]); self.tile1.grid(row=2, column=0, padx=(DIMENSIONS["pad_window"], 10), pady=10, sticky="nsew")
        self.tile2 = ctk.CTkFrame(self.home_frame, corner_radius=DIMENSIONS["corner_radius"]); self.tile2.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.tile3 = ctk.CTkFrame(self.home_frame, corner_radius=DIMENSIONS["corner_radius"]); self.tile3.grid(row=2, column=2, padx=(10, DIMENSIONS["pad_window"]), pady=10, sticky="nsew")
        self.card_frames.extend([self.tile1, self.tile2, self.tile3])

        tile_val_font = ctk.CTkFont(family=FONTS["main_family"], size=24, weight="bold")
        ctk.CTkLabel(self.tile1, text="CPU Status", font=self.main_font, text_color=DARK_MODE["text_muted"]).pack(pady=(20,0), padx=20, anchor="w")
        self.lbl_tile_cpu = ctk.CTkLabel(self.tile1, text="Checking...", font=tile_val_font); self.lbl_tile_cpu.pack(pady=(5,20), padx=20, anchor="w")
        self.accent_labels.append(self.lbl_tile_cpu)

        ctk.CTkLabel(self.tile2, text="GPU Driver", font=self.main_font, text_color=DARK_MODE["text_muted"]).pack(pady=(20,0), padx=20, anchor="w")
        self.lbl_tile_gpu = ctk.CTkLabel(self.tile2, text="Checking...", font=tile_val_font); self.lbl_tile_gpu.pack(pady=(5,20), padx=20, anchor="w")
        self.accent_labels.append(self.lbl_tile_gpu)

        ctk.CTkLabel(self.tile3, text="Shader Cache", font=self.main_font, text_color=DARK_MODE["text_muted"]).pack(pady=(20,0), padx=20, anchor="w")
        self.lbl_tile_cache = ctk.CTkLabel(self.tile3, text="Unknown", font=tile_val_font); self.lbl_tile_cache.pack(pady=(5,20), padx=20, anchor="w")
        self.accent_labels.append(self.lbl_tile_cache)

        self.news_card = ctk.CTkFrame(self.home_frame, corner_radius=DIMENSIONS["corner_radius"])
        self.news_card.grid(row=3, column=0, columnspan=3, padx=DIMENSIONS["pad_window"], pady=20, sticky="nsew")
        self.card_frames.append(self.news_card)
        self.lbl_news_title = ctk.CTkLabel(self.news_card, text="", font=self.subtitle_font)
        self.lbl_news_title.pack(pady=(20, 10), padx=20, anchor="w")
        self.accent_labels.append(self.lbl_news_title)
        self.lbl_news_text = ctk.CTkLabel(self.news_card, text="", font=self.main_font, justify="left")
        self.lbl_news_text.pack(pady=(0, 20), padx=20, anchor="w")

    def build_info_frame(self):
        self.info_frame.grid_columnconfigure(0, weight=1)
        self.lbl_nv_title = self.create_title(self.info_frame, "tab_nv_title", "tt_nv")

        self.btn_nv_refresh = ctk.CTkButton(self.info_frame, text="", command=lambda: self.run_in_thread(self.refresh_sys_info), **self.get_btn_style())
        self.btn_nv_refresh.grid(row=1, column=0, padx=DIMENSIONS["pad_window"], pady=(0, 10), sticky="w")
        self.primary_buttons.append(self.btn_nv_refresh)

        gpu_box = ctk.CTkFrame(self.info_frame, corner_radius=DIMENSIONS["corner_radius"])
        gpu_box.grid(row=2, column=0, padx=DIMENSIONS["pad_window"], pady=5, sticky="ew")
        gpu_box.grid_columnconfigure(1, weight=1)
        self.card_frames.append(gpu_box)

        self.lbl_gpu_name = ctk.CTkLabel(gpu_box, text="GPU: ...", font=self.main_font); self.lbl_gpu_name.grid(row=0, column=0, padx=25, pady=25, sticky="w")
        self.lbl_gpu_vram = ctk.CTkLabel(gpu_box, text="VRAM: ...", font=self.main_font); self.lbl_gpu_vram.grid(row=0, column=1, padx=25, pady=25, sticky="w")
        self.lbl_gpu_temp = ctk.CTkLabel(gpu_box, text="Temp: ...", font=self.subtitle_font); self.lbl_gpu_temp.grid(row=0, column=2, padx=25, pady=25, sticky="w")
        self.accent_labels.extend([self.lbl_gpu_name, self.lbl_gpu_vram])

        drv_box = ctk.CTkFrame(self.info_frame, corner_radius=DIMENSIONS["corner_radius"])
        drv_box.grid(row=3, column=0, padx=DIMENSIONS["pad_window"], pady=10, sticky="ew")
        self.card_frames.append(drv_box)
        self.lbl_current_driver = ctk.CTkLabel(drv_box, text="Current: ...", font=self.subtitle_font)
        self.lbl_current_driver.grid(row=0, column=0, padx=25, pady=30, sticky="w")
        self.lbl_actual_driver = ctk.CTkLabel(drv_box, text="Available: ...", font=self.subtitle_font)
        self.lbl_actual_driver.grid(row=0, column=1, padx=40, pady=30, sticky="w")
        self.btn_update_driver = ctk.CTkButton(drv_box, text="Update", state="disabled", command=self.update_driver, **self.get_btn_style())
        self.btn_update_driver.grid(row=0, column=2, padx=25, pady=30, sticky="e")
        self.primary_buttons.append(self.btn_update_driver)

        rb_box = ctk.CTkFrame(self.info_frame, corner_radius=DIMENSIONS["corner_radius"])
        rb_box.grid(row=4, column=0, padx=DIMENSIONS["pad_window"], pady=10, sticky="ew")
        self.card_frames.append(rb_box)
        self.lbl_nv_rollback = ctk.CTkLabel(rb_box, text="", font=self.main_font)
        self.lbl_nv_rollback.grid(row=0, column=0, padx=25, pady=30, sticky="w")
        self.accent_labels.append(self.lbl_nv_rollback)
        self.combo_rollback = ctk.CTkOptionMenu(rb_box, values=["Searching..."], width=200, corner_radius=DIMENSIONS["corner_radius"], font=self.main_font)
        self.combo_rollback.grid(row=0, column=1, padx=20, pady=30, sticky="w")
        self.btn_rollback = ctk.CTkButton(rb_box, text="", command=self.rollback_driver, **self.get_btn_style())
        self.btn_rollback.grid(row=0, column=2, padx=25, pady=30, sticky="w")

        self.lbl_nv_status = ctk.CTkLabel(self.info_frame, text="", font=self.main_font, text_color="#F39C12")
        self.lbl_nv_status.grid(row=5, column=0, padx=DIMENSIONS["pad_window"], pady=10, sticky="w")

    def build_overheat_frame(self):
        self.overheat_frame.grid_columnconfigure(0, weight=1)
        self.overheat_frame.grid_rowconfigure(3, weight=1)
        self.lbl_overheat_title = self.create_title(self.overheat_frame, "tab_overheat_title", "tt_overheat")

        alarm_card = ctk.CTkFrame(self.overheat_frame, corner_radius=DIMENSIONS["corner_radius"])
        alarm_card.grid(row=1, column=0, padx=DIMENSIONS["pad_window"], pady=(5, 10), sticky="ew")
        self.card_frames.append(alarm_card)

        self.switch_overheat = ctk.CTkSwitch(alarm_card, text="", command=self.toggle_protection, font=self.main_font, switch_width=45, switch_height=22)
        self.switch_overheat.grid(row=0, column=0, columnspan=2, padx=25, pady=(20, 10), sticky="w")
        self.switch_overheat.select()

        self.lbl_alarm_text = ctk.CTkLabel(alarm_card, text="", font=self.main_font)
        self.lbl_alarm_text.grid(row=1, column=0, padx=25, pady=(10, 5), sticky="w")
        self.entry_alarm = ctk.CTkEntry(alarm_card, width=100, corner_radius=DIMENSIONS["corner_radius"], font=self.main_font)
        self.entry_alarm.grid(row=2, column=0, padx=25, pady=(0, 20), sticky="w")
        self.entry_alarm.insert(0, "90")

        self.lbl_sound_text = ctk.CTkLabel(alarm_card, text="", font=self.main_font)
        self.lbl_sound_text.grid(row=1, column=1, padx=25, pady=(10, 5), sticky="w")

        sound_box = ctk.CTkFrame(alarm_card, fg_color="transparent")
        sound_box.grid(row=2, column=1, padx=25, pady=(0, 20), sticky="w")
        self.combo_sound = ctk.CTkOptionMenu(sound_box, values=list(SOUND_FILES.keys()), corner_radius=DIMENSIONS["corner_radius"], font=self.main_font)
        self.combo_sound.grid(row=0, column=0, padx=(0, 10))
        self.combo_sound.set("Siren (3x Warning)")
        self.btn_test_sound = ctk.CTkButton(sound_box, text="", width=80, command=lambda: self.play_sound(is_timer=False), **self.get_btn_style())
        self.btn_test_sound.grid(row=0, column=1)
        self.primary_buttons.append(self.btn_test_sound)
        self.accent_labels.extend([self.lbl_alarm_text, self.lbl_sound_text, self.switch_overheat])

        thresh_card = ctk.CTkFrame(self.overheat_frame, corner_radius=DIMENSIONS["corner_radius"])
        thresh_card.grid(row=2, column=0, padx=DIMENSIONS["pad_window"], pady=10, sticky="ew")
        self.card_frames.append(thresh_card)

        self.lbl_thresh_title = ctk.CTkLabel(thresh_card, text="", font=self.subtitle_font)
        self.lbl_thresh_title.grid(row=0, column=0, columnspan=2, padx=25, pady=(20, 15), sticky="w")

        self.lbl_yellow = ctk.CTkLabel(thresh_card, text="", font=self.main_font)
        self.lbl_yellow.grid(row=1, column=0, padx=25, pady=(0, 5), sticky="w")
        self.entry_yellow = ctk.CTkEntry(thresh_card, width=100, corner_radius=DIMENSIONS["corner_radius"], font=self.main_font)
        self.entry_yellow.grid(row=2, column=0, padx=25, pady=(0, 20), sticky="w")
        self.entry_yellow.insert(0, "60")

        self.lbl_red = ctk.CTkLabel(thresh_card, text="", font=self.main_font)
        self.lbl_red.grid(row=1, column=1, padx=25, pady=(0, 5), sticky="w")
        self.entry_red = ctk.CTkEntry(thresh_card, width=100, corner_radius=DIMENSIONS["corner_radius"], font=self.main_font)
        self.entry_red.grid(row=2, column=1, padx=25, pady=(0, 20), sticky="w")
        self.entry_red.insert(0, "75")

        self.accent_labels.extend([self.lbl_thresh_title, self.lbl_yellow, self.lbl_red])

        self.graph_card = ctk.CTkFrame(self.overheat_frame, corner_radius=DIMENSIONS["corner_radius"])
        self.graph_card.grid(row=3, column=0, padx=DIMENSIONS["pad_window"], pady=(10, DIMENSIONS["pad_window"]), sticky="nsew")
        self.card_frames.append(self.graph_card)
        self.graph_card.grid_columnconfigure(0, weight=1)
        self.graph_card.grid_rowconfigure(1, weight=1)

        top_g_box = ctk.CTkFrame(self.graph_card, fg_color="transparent")
        top_g_box.grid(row=0, column=0, sticky="ew", padx=25, pady=(20,10))

        self.lbl_graph_title = ctk.CTkLabel(top_g_box, text="", font=self.subtitle_font)
        self.lbl_graph_title.pack(side="left")
        self.accent_labels.append(self.lbl_graph_title)

        self.seg_time = ctk.CTkSegmentedButton(top_g_box, values=["1 Min", "5 Min"], command=lambda e: self.draw_graph())
        self.seg_time.pack(side="right", padx=(10, 0))
        self.seg_time.set("5 Min")

        self.seg_graph = ctk.CTkSegmentedButton(top_g_box, values=["GPU", "CPU"], command=lambda e: self.draw_graph())
        self.seg_graph.pack(side="right")
        self.seg_graph.set("GPU")

        self.graph_canvas = tk.Canvas(self.graph_card, bg=self.current_card_color, highlightthickness=0)
        self.graph_canvas.grid(row=1, column=0, sticky="nsew", padx=25, pady=(0, 20))

        self.graph_canvas.bind("<Configure>", lambda e: self.draw_graph())
        self.graph_canvas.bind("<Motion>", self.on_graph_hover)
        self.graph_canvas.bind("<Leave>", self.on_graph_leave)

    def build_settings_frame(self):
        self.settings_frame.grid_columnconfigure(0, weight=1)
        self.lbl_set_title = self.create_title(self.settings_frame, "set_title", "tt_set")

        self.lbl_lang_text = ctk.CTkLabel(self.settings_frame, text="", font=self.main_font)
        self.lbl_lang_text.grid(row=1, column=0, padx=DIMENSIONS["pad_window"], sticky="w")
        self.combo_lang = ctk.CTkOptionMenu(self.settings_frame, values=["English", "Русский"], corner_radius=DIMENSIONS["corner_radius"], font=self.main_font, command=self.change_language)
        self.combo_lang.grid(row=2, column=0, padx=DIMENSIONS["pad_window"], pady=(5, 25), sticky="w")
        self.combo_lang.set("English")

        self.lbl_theme_text = ctk.CTkLabel(self.settings_frame, text="", font=self.main_font)
        self.lbl_theme_text.grid(row=3, column=0, padx=DIMENSIONS["pad_window"], sticky="w")
        self.combo_theme = ctk.CTkOptionMenu(self.settings_frame, values=["Dark", "Light"], corner_radius=DIMENSIONS["corner_radius"], font=self.main_font, command=self.change_theme_trigger)
        self.combo_theme.grid(row=4, column=0, padx=DIMENSIONS["pad_window"], pady=(5, 25), sticky="w")
        self.accent_labels.extend([self.lbl_lang_text, self.lbl_theme_text])

    # ==================== ДВИЖОК ТЕМ И ПЕРЕВОДОВ ====================
    def update_texts(self):
        nav_indent = "   "

        self.btn_nav_home.configure(text=nav_indent + self.t("menu_home"))
        self.btn_nav_clean.configure(text=nav_indent + self.t("menu_clean"))
        self.btn_nav_info.configure(text=nav_indent + self.t("menu_gpu"))
        self.btn_nav_game.configure(text=nav_indent + self.t("menu_game"))
        self.btn_nav_overheat.configure(text=nav_indent + self.t("menu_overheat"))
        self.btn_nav_settings.configure(text=nav_indent + self.t("menu_settings"))
        self.btn_nav_about.configure(text=nav_indent + self.t("menu_about"))
        self.btn_nav_log.configure(text=nav_indent + self.t("menu_log"))

        self.lbl_hero_title.configure(text=self.t("home_hero"))
        self.lbl_hero_sub.configure(text=self.t("home_sub"))
        self.lbl_news_title.configure(text=self.t("home_news_title"))
        self.lbl_news_text.configure(text=self.t("news_1"))

        self.clean_page.update_texts()
        self.optimization_page.update_texts()
        self.about_page.update_texts()

        self.lbl_nv_title.configure(text=self.t("tab_nv_title"))
        self.btn_nv_refresh.configure(text=self.t("btn_refresh"))
        self.lbl_nv_rollback.configure(text=self.t("lbl_nv_rollback"))
        self.btn_rollback.configure(text=self.t("btn_rollback"))

        self.lbl_overheat_title.configure(text=self.t("tab_overheat_title"))
        self.lbl_graph_title.configure(text=self.t("graph_title"))
        self.toggle_protection()

        self.lbl_set_title.configure(text=self.t("set_title"))
        self.lbl_lang_text.configure(text=self.t("lbl_lang"))
        self.lbl_theme_text.configure(text=self.t("lbl_theme"))

        self.lbl_alarm_text.configure(text=self.t("lbl_alarm"))
        self.lbl_sound_text.configure(text=self.t("lbl_sound"))
        self.btn_test_sound.configure(text=self.t("btn_test_sound"))
        self.lbl_thresh_title.configure(text=self.t("lbl_thresh_title"))
        self.lbl_yellow.configure(text=self.t("lbl_yellow"))
        self.lbl_red.configure(text=self.t("lbl_red"))

        self.seg_time.configure(values=[self.t("time_1m"), self.t("time_5m")])
        if self.seg_time.get() not in [self.t("time_1m"), self.t("time_5m")]:
            self.seg_time.set(self.t("time_5m"))

        self.lbl_log_title.configure(text=self.t("tab_log_title"))
        self.btn_clear_log.configure(text=self.t("btn_clear_log"))

        themes = [self.t("theme_dark"), self.t("theme_light")]
        curr = self.combo_theme.get()
        self.combo_theme.configure(values=themes)
        if curr not in themes: self.combo_theme.set(themes[0])

        if hasattr(self, 'graph_canvas'): self.draw_graph()

    def change_language(self, value):
        self.lang = "ru" if value == "Русский" else "en"
        self.update_texts()
        self.app_log(f"Language changed to: {self.lang}")

    def change_theme_trigger(self, value):
        self.change_theme(value)
        if self.home_frame.winfo_ismapped(): self.show_home_frame()
        elif self.clean_frame.winfo_ismapped(): self.show_clean_frame()
        elif self.info_frame.winfo_ismapped(): self.show_info_frame()
        elif self.game_frame.winfo_ismapped(): self.show_game_frame()
        elif self.overheat_frame.winfo_ismapped(): self.show_overheat_frame()
        elif self.settings_frame.winfo_ismapped(): self.show_settings_frame()
        elif self.about_frame.winfo_ismapped(): self.show_about_frame()
        elif self.log_frame.winfo_ismapped(): self.show_log_frame()

    def change_theme(self, value):
        is_dark = "Dark" in value or "Темная" in value
        ctk.set_appearance_mode("Dark" if is_dark else "Light")

        theme = DARK_MODE if is_dark else LIGHT_MODE

        self.nav_text_color_idle = theme["nav_text_idle"]
        self.nav_text_color_active = theme["nav_text_active"]
        self.nav_bg_color_active = theme["primary_color"]
        self.current_text_color = theme["text_main"]
        self.current_card_color = theme["card_color"]

        self.sidebar_frame.configure(fg_color=theme["sidebar_color"])
        for f in self.bg_frames: f.configure(fg_color=theme["bg_color"])
        for c in self.card_frames: c.configure(fg_color=theme["card_color"])
        for c in self.consoles: c.configure(fg_color=theme["console_bg"], text_color=theme["console_text"])

        for l in self.accent_labels: l.configure(text_color=theme["text_main"])
        self.tooltip_frame.configure(fg_color=theme["sidebar_color"], border_color=theme["primary_color"])
        self.tooltip_label.configure(text_color=theme["text_main"])
        for icon in self.info_icons: icon.configure(text_color=theme["primary_color"])

        for cb in self.checkboxes:
            cb.configure(fg_color=theme["primary_color"], hover_color=theme["primary_hover"])

        for combo in [self.combo_lang, self.combo_theme, self.combo_rollback, getattr(self, 'combo_sound', None)]:
            if combo:
                combo.configure(fg_color=theme["card_color"], button_color=theme["primary_color"],
                                button_hover_color=theme["primary_hover"], text_color=theme["text_main"])

        if hasattr(self, 'switch_overheat'): self.switch_overheat.configure(progress_color=theme["primary_color"])

        self.clean_page.change_theme(theme)
        self.optimization_page.change_theme(theme)

        if hasattr(self, 'btn_rollback'): self.btn_rollback.configure(fg_color=theme["danger_color"], hover_color=theme["danger_hover"])

        for b in self.primary_buttons:
            b.configure(fg_color=theme["primary_color"], hover_color=theme["primary_hover"], text_color=theme["primary_text"])

        for b in [self.btn_nav_home, self.btn_nav_clean, self.btn_nav_info, self.btn_nav_game, self.btn_nav_overheat, self.btn_nav_settings, self.btn_nav_about, self.btn_nav_log]:
            b.configure(fg_color="transparent", text_color=self.nav_text_color_idle)

        if hasattr(self, 'lbl_tile_gpu') and self.current_driver_ver != "0":
            self.lbl_tile_gpu.configure(text_color=self.nav_bg_color_active)

        if hasattr(self, 'graph_canvas'):
            self.graph_canvas.configure(bg=self.current_card_color)
            self.draw_graph()

    # ==================== СИСТЕМА И ТЕМПЕРАТУРА ====================
    def refresh_sys_info(self):
        self.app_log("Manual hardware refresh triggered.")
        self.refresh_sys_info_quiet(check_updates=True)

    def refresh_sys_info_quiet(self, check_updates=False):
        actual_driver = "0"
        temp_gpu = 0
        try:
            result = subprocess.run(["nvidia-smi", "--query-gpu=name,temperature.gpu,memory.used,memory.total,driver_version,utilization.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True)
            if result.stdout:
                data = result.stdout.strip().split('\n')[0].split(', ')
                self.lbl_gpu_name.configure(text=f"GPU: {data[0]}")
                self.lbl_gpu_vram.configure(text=f"VRAM: {data[2]} / {data[3]} MiB")
                temp_gpu = int(data[1])
                self.lbl_gpu_temp.configure(text=f"GPU Temp: {temp_gpu}°C" if self.lang=="en" else f"Температура: {temp_gpu}°C")
                self.current_driver_ver = data[4].strip()
                self.lbl_current_driver.configure(text=f"Current: {self.current_driver_ver}" if self.lang=="en" else f"Текущий: {self.current_driver_ver}")

                if hasattr(self, 'lbl_tile_gpu'): self.lbl_tile_gpu.configure(text=self.current_driver_ver, text_color=self.nav_bg_color_active)

                if hasattr(self, 'optimization_page') and self.optimization_page.is_telemetry_running:
                    gpu_util = int(data[5]) if data[5].isdigit() else 0
                    cpu_util, ram_util = self.get_cpu_ram_usage()
                    self.optimization_page.telemetry_data.append({"gpu_temp": temp_gpu, "gpu_util": gpu_util, "vram": int(data[2]), "cpu_util": cpu_util, "ram_util": ram_util})
        except: pass

        temp_cpu = self.get_cpu_temp()

        self.temp_history["GPU"].append(temp_gpu)
        self.temp_history["CPU"].append(temp_cpu)
        if len(self.temp_history["GPU"]) > 60: self.temp_history["GPU"].pop(0)
        if len(self.temp_history["CPU"]) > 60: self.temp_history["CPU"].pop(0)

        if hasattr(self, 'overheat_frame') and self.overheat_frame.winfo_ismapped():
            self.draw_graph()

        if hasattr(self, 'switch_overheat') and self.switch_overheat.get() == 1:
            try: alarm_limit = int(self.entry_alarm.get())
            except: alarm_limit = 90

            if temp_gpu >= alarm_limit or temp_cpu >= alarm_limit:
                self.lbl_gpu_temp.configure(text_color="#E74C3C")
                current_time = time.time()
                if current_time - getattr(self, 'last_alarm_time', 0) > 15:
                    self.app_log(f"⚠️ ALARM: High Temperature! GPU: {temp_gpu}°C | CPU: {temp_cpu}°C (Limit: {alarm_limit}°C)")
                    self.play_sound()
                    self.last_alarm_time = current_time
            else:
                if hasattr(self, 'current_text_color'):
                    self.lbl_gpu_temp.configure(text_color=self.current_text_color)

        if check_updates:
            self.app_log("Checking for Nvidia driver updates via pacman...")
            try:
                pacman_result = subprocess.run(["pacman", "-Si", "nvidia-utils"], capture_output=True, text=True)
                if pacman_result.stdout:
                    for line in pacman_result.stdout.split('\n'):
                        if line.startswith("Version") or line.startswith("Версия"):
                            actual_driver = line.split(":")[1].strip()
                            self.lbl_actual_driver.configure(text=f"Available: {actual_driver}" if self.lang=="en" else f"Доступный: {actual_driver}")
                            self.app_log(f"Found available driver version: {actual_driver}")
                            break
            except Exception as e:
                self.app_log(f"Failed to check driver updates: {e}")

            if self.current_driver_ver != "0" and actual_driver != "0":
                cmp_current = self.current_driver_ver if "-" in self.current_driver_ver else f"{self.current_driver_ver}-1"
                cmp_actual = actual_driver if "-" in actual_driver else f"{actual_driver}-1"
                try:
                    cmp_result = subprocess.run(["vercmp", cmp_current, cmp_actual], capture_output=True, text=True)
                    if int(cmp_result.stdout.strip()) < 0:
                        self.lbl_current_driver.configure(text_color="#E74C3C")
                        self.lbl_actual_driver.configure(text_color="#2ECC71")
                        self.btn_update_driver.configure(state="normal")
                    else:
                        self.btn_update_driver.configure(state="disabled")
                except: pass
            self.find_cached_drivers()

    def find_cached_drivers(self):
        self.cached_drivers.clear()
        files = glob.glob("/var/cache/pacman/pkg/nvidia-utils-*.pkg.tar.zst")
        valid_versions =[]
        for f in files:
            ver = os.path.basename(f).replace("nvidia-utils-", "").replace(".pkg.tar.zst", "").replace("-x86_64", "").replace("-any", "")
            if self.current_driver_ver != "0":
                cmp_curr = self.current_driver_ver if "-" in self.current_driver_ver else f"{self.current_driver_ver}-1"
                cmp_cache = ver if "-" in ver else f"{ver}-1"
                try:
                    res = subprocess.run(["vercmp", cmp_cache, cmp_curr], capture_output=True, text=True)
                    if int(res.stdout.strip()) < 0:
                        valid_versions.append(ver)
                        self.cached_drivers[ver] = f
                except: pass
        if valid_versions:
            valid_versions.sort(reverse=True)
            self.combo_rollback.configure(values=valid_versions)
            self.combo_rollback.set(valid_versions[0])
            self.btn_rollback.configure(state="normal")
        else:
            self.combo_rollback.configure(values=["No old versions" if self.lang=="en" else "Нет старых версий"])
            self.btn_rollback.configure(state="disabled")

    def update_driver(self):
        self.app_log("Opening pamac-manager to update driver...")
        subprocess.Popen(["pamac-manager", "--details=nvidia-utils"])

    def rollback_driver(self):
        target = self.combo_rollback.get()
        if target in self.cached_drivers:
            self.app_log(f"Attempting to rollback driver to {target} via pkexec pacman...")
            subprocess.Popen(["pkexec", "pacman", "-U", "--noconfirm", self.cached_drivers[target]])

    def on_graph_leave(self, event):
        self.last_mouse_x = None
        if hasattr(self, 'graph_canvas'): self.graph_canvas.delete("hover")

    def on_graph_hover(self, event=None, x_pos=None):
        if not hasattr(self, 'graph_canvas'): return
        self.graph_canvas.delete("hover")
        if not hasattr(self, 'current_graph_points') or not self.current_graph_points: return

        x = event.x if event else x_pos
        if x is None: return
        self.last_mouse_x = x

        w = self.graph_canvas.winfo_width()
        h = self.graph_canvas.winfo_height()
        if x < 10 or x > w - 10: return

        closest_pt = min(self.current_graph_points, key=lambda pt: abs(pt[0] - x))
        cx, cy, cval, ccolor = closest_pt
        if abs(cx - x) > (w / len(self.current_graph_points)) * 2: return

        self.graph_canvas.create_line(cx, 20, cx, h-20, fill=self.nav_text_color_idle, dash=(2, 2), tags="hover")
        self.graph_canvas.create_oval(cx-6, cy-6, cx+6, cy+6, fill=self.current_card_color, outline=ccolor, width=3, tags="hover")
        self.graph_canvas.create_rectangle(cx-22, cy-35, cx+22, cy-10, fill=self.current_card_color, outline=ccolor, tags="hover")
        self.graph_canvas.create_text(cx, cy-22, text=f"{cval}°C", fill=self.current_text_color, font=(FONTS["main_family"], 10, "bold"), tags="hover")

    def draw_graph(self):
        if not hasattr(self, 'graph_canvas'): return
        self.graph_canvas.delete("all")
        mode = self.seg_graph.get()
        raw_data = self.temp_history[mode]

        if self.seg_time.get() in [self.t("time_1m"), "1 Min", "1 Мин"]:
            data = raw_data[-12:]
        else:
            data = raw_data

        w = self.graph_canvas.winfo_width()
        h = self.graph_canvas.winfo_height()

        if w < 10 or h < 10 or len(data) < 2:
            self.graph_canvas.create_text(w/2, h/2, text="Collecting data..." if self.lang=="en" else "Сбор данных...", fill=self.current_text_color, font=(FONTS["main_family"], 12))
            return

        try: y_th = int(self.entry_yellow.get())
        except: y_th = 60
        try: r_th = int(self.entry_red.get())
        except: r_th = 75

        pad_x = 45; pad_y = 20
        max_val = max(100, max(data) + 10, r_th + 10)
        min_val = min(30, min(data) - 10)
        val_range = max_val - min_val

        self.graph_canvas.create_line(pad_x, h-pad_y, w-pad_x, h-pad_y, fill=self.nav_text_color_idle, dash=(4, 4))
        self.graph_canvas.create_line(pad_x, pad_y, w-pad_x, pad_y, fill=self.nav_text_color_idle, dash=(4, 4))
        self.graph_canvas.create_text(pad_x - 10, pad_y, text=f"{max_val}°", fill=self.current_text_color, anchor="e")
        self.graph_canvas.create_text(pad_x - 10, h-pad_y, text=f"{min_val}°", fill=self.current_text_color, anchor="e")

        step_x = (w - 2*pad_x) / (len(data) - 1)
        self.current_graph_points = []
        for i, val in enumerate(data):
            x = pad_x + i * step_x
            y = h - pad_y - ((val - min_val) / val_range) * (h - 2*pad_y)
            if val >= r_th: color = "#E74C3C"
            elif val >= y_th: color = "#F1C40F"
            else: color = self.nav_bg_color_active
            self.current_graph_points.append((x, y, val, color))

        for i in range(len(self.current_graph_points) - 1):
            x1, y1, v1, c1 = self.current_graph_points[i]
            x2, y2, v2, c2 = self.current_graph_points[i+1]
            self.graph_canvas.create_line(x1, y1, x2, y2, fill=c2, width=3, capstyle=tk.ROUND)

        last_x, last_y, last_val, last_color = self.current_graph_points[-1]
        self.graph_canvas.create_oval(last_x-4, last_y-4, last_x+4, last_y+4, fill=last_color, outline="", tags="base")
        self.graph_canvas.create_text(last_x, last_y - 15, text=f"{last_val}°", fill=last_color, font=(FONTS["main_family"], 12, "bold"), tags="base")

        self.on_graph_hover(x_pos=getattr(self, 'last_mouse_x', None))

    def toggle_protection(self):
        state_on = self.switch_overheat.get() == 1
        txt = self.t("sw_prot_on") if state_on else self.t("sw_prot_off")
        self.switch_overheat.configure(text=txt)
        self.app_log(f"Overheat protection is now {'ENABLED' if state_on else 'DISABLED'}.")
        if not state_on and hasattr(self, 'current_text_color'):
            self.lbl_gpu_temp.configure(text_color=self.current_text_color)

    def run_in_thread(self, func):
        threading.Thread(target=func, daemon=True).start()

    def auto_refresh_system(self):
        self.refresh_sys_info_quiet()
        if hasattr(self, 'optimization_page'):
            self.optimization_page.load_game_booster_data()
        self.after(5000, self.auto_refresh_system)

    def hide_all(self):
        self.home_frame.grid_forget()
        self.clean_frame.grid_forget()
        self.info_frame.grid_forget()
        self.game_frame.grid_forget()
        self.overheat_frame.grid_forget()
        self.settings_frame.grid_forget()
        self.about_frame.grid_forget()
        self.log_frame.grid_forget()
        for b in [self.btn_nav_home, self.btn_nav_clean, self.btn_nav_info, self.btn_nav_game, self.btn_nav_overheat, self.btn_nav_settings, self.btn_nav_about, self.btn_nav_log]:
            b.configure(fg_color="transparent", text_color=self.nav_text_color_idle)

    def highlight_btn(self, active_btn):
        if active_btn is not None:
            active_btn.configure(fg_color=self.nav_bg_color_active, text_color=self.nav_text_color_active)

    def show_home_frame(self):
        self.hide_all()
        self.home_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.highlight_btn(self.btn_nav_home)
        if hasattr(self, 'optimization_page'):
            self.run_in_thread(self.optimization_page.analyze_shaders)

    def show_clean_frame(self):
        self.hide_all()
        self.clean_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.highlight_btn(self.btn_nav_clean)

    def show_info_frame(self):
        self.hide_all()
        self.info_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.highlight_btn(self.btn_nav_info)
        self.refresh_sys_info_quiet(check_updates=True)

    def show_game_frame(self):
        self.hide_all()
        self.game_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.highlight_btn(self.btn_nav_game)
        if hasattr(self, 'optimization_page'):
            self.optimization_page.load_game_booster_data()

    def show_overheat_frame(self):
        self.hide_all()
        self.overheat_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.highlight_btn(self.btn_nav_overheat)
        self.draw_graph()

    def show_settings_frame(self):
        self.hide_all()
        self.settings_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.highlight_btn(self.btn_nav_settings)

    def show_about_frame(self):
        self.hide_all()
        self.about_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.highlight_btn(self.btn_nav_about)

    def show_log_frame(self):
        self.hide_all()
        self.log_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.highlight_btn(self.btn_nav_log)

if __name__ == "__main__":
    app = App()
    app.mainloop()
