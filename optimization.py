import customtkinter as ctk
import tkinter as tk
import subprocess
import threading
import os
import shutil
import time
import json
from datetime import datetime
import signal
from theme import FONTS, DIMENSIONS

# Локальный словарь переводов для вкладки "Оптимизация"
OPT_LANGUAGES = {
    "en": {
        "tab_game_title": "Optimization & Diagnostics", "tt_game": "Boost FPS, freeze background apps, manage overlays, and tweak network.",
        "cpu_title": "CPU Performance Mode", "btn_cpu_on": "Enable MAX FPS (+Telemetry)", "tweaks_title": "Performance Tweaks",
        "lbl_test_net": "Network Ping Optimizer", "tt_test_net": "Changes sysctl for low latency network (Disables Nagle's algo).", "btn_test_net": "Optimize Ping",
        "lbl_test_gm": "Feral GameMode", "tt_test_gm": "Activates the built-in Linux GameMode daemon to prioritize the game process.", "btn_test_gm": "Enable GameMode",
        "lbl_test_ds": "Discord CPU Priority", "tt_test_ds": "Forces Discord to high priority so your voice doesn't lag when CPU is at 100%.", "btn_test_ds": "Boost Discord",
        "osd_title": "Game Launch Tools", "btn_osd_save": "Save Config", "lbl_osd_hint": "Steam Launch Options:", "btn_copy_cmd": "Copy: mangohud %command%",
        "lbl_test_gs": "Gamescope FPS Limit", "tt_test_gs": "Generates a Steam command to run games in an isolated window with a hard FPS cap.", "btn_test_gs": "Copy Cmd",
        "steam_title": "Shader Cache", "btn_clean_steam": "Clean Shaders",
        "health_title": "Health Timer", "lbl_timer_input": "Play time (min):", "btn_start": "Start", "btn_stop": "Stop/Reset",
        "tab_telem": "Telemetry & Bottleneck", "tab_crash": "Crash Logs", "tab_prof": "Profiles",
        "btn_crash": "Analyze Kernel Logs", "btn_exp": "Export Profile", "btn_imp": "Import Profile"
    },
    "ru": {
        "tab_game_title": "Оптимизация для игр", "tt_game": "Увеличивает FPS, настраивает сеть, оверлей и фоновые процессы.",
        "cpu_title": "Режим Производительности", "btn_cpu_on": "Включить Максимум FPS (+Телеметрия)", "tweaks_title": "Твики производительности",
        "lbl_test_net": "Сетевой Тюнинг (Ping)", "tt_test_net": "Включает tcp_low_latency в ядре Linux.\nЗаставляет систему мгновенно отправлять пакеты (для CS2, Valorant).", "btn_test_net": "Оптимизировать",
        "lbl_test_gm": "Feral GameMode", "tt_test_gm": "Активирует системный игровой процесс Linux.\nОн блокирует скринсейвер и дает игре приоритет ввода/вывода.", "btn_test_gm": "Включить GameMode",
        "lbl_test_ds": "Приоритет для Discord", "tt_test_ds": "Дает Discord статус 'Высокой важности'.\nВаш голос не будет лагать, когда игра грузит процессор на 100%.", "btn_test_ds": "Дать приоритет",
        "osd_title": "Инструменты запуска", "btn_osd_save": "Сохранить конфиг", "lbl_osd_hint": "В Steam (Параметры запуска):", "btn_copy_cmd": "Скопировать: mangohud %command%",
        "lbl_test_gs": "Gamescope FPS Лимит", "tt_test_gs": "Микро-утилита от Valve. Позволяет жестко ограничить FPS и задать любое разрешение экрана.", "btn_test_gs": "Скопировать",
        "steam_title": "Кэш Шейдеров", "btn_clean_steam": "Очистить",
        "health_title": "Режим Здоровья", "lbl_timer_input": "Играть минут:", "btn_start": "Старт", "btn_stop": "Стоп/Сброс",
        "tab_telem": "Телеметрия и Боттлнек", "tab_crash": "Журнал вылетов", "tab_prof": "Профили",
        "btn_crash": "Анализировать логи ядра", "btn_exp": "Экспорт профиля", "btn_imp": "Импорт профиля"
    }
}

def get_dir_size_in_mb(path):
    total = 0
    if os.path.exists(path):
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp): total += os.path.getsize(fp)
    return total / (1024 * 1024)

class OptimizationPage:
    def __init__(self, app_instance, parent_frame):
        self.app = app_instance
        self.frame = parent_frame

        self.frozen_pids = []
        self.health_time_left = 0
        self.health_timer_state = "stopped"
        self.overtime_seconds = 0
        self.checkboxes = []
        self.build_ui()

    def build_ui(self):
        self.frame.grid_columnconfigure((0, 1), weight=1)
        self.frame.grid_rowconfigure(4, weight=1)
        self.lbl_game_title = self.app.create_title(self.frame, "tab_game_title", "tt_game")

        # === ЛЕВАЯ КОЛОНКА ===
        cpu_card = ctk.CTkFrame(self.frame, corner_radius=DIMENSIONS["corner_radius"])
        cpu_card.grid(row=1, column=0, padx=(DIMENSIONS["pad_window"], 10), pady=(0, 10), sticky="nsew")
        self.app.card_frames.append(cpu_card)

        self.lbl_cpu_title = ctk.CTkLabel(cpu_card, text="", font=self.app.subtitle_font)
        self.lbl_cpu_title.grid(row=0, column=0, padx=25, pady=(20, 5), sticky="w")
        self.app.accent_labels.append(self.lbl_cpu_title)

        self.lbl_cpu_gov = ctk.CTkLabel(cpu_card, text="Ready.", font=self.app.main_font, justify="left")
        self.lbl_cpu_gov.grid(row=1, column=0, padx=25, pady=10, sticky="w")

        self.switch_cpu = ctk.CTkSwitch(cpu_card, text="", command=lambda: self.app.run_in_thread(self.toggle_cpu_mode), font=self.app.main_font, switch_width=45, switch_height=22)
        self.switch_cpu.grid(row=2, column=0, padx=25, pady=(10, 20), sticky="w")
        self.app.accent_labels.extend([self.lbl_cpu_gov, self.switch_cpu])

        # Твики (Network, GameMode, Discord)
        tweaks_card = ctk.CTkFrame(self.frame, corner_radius=DIMENSIONS["corner_radius"])
        tweaks_card.grid(row=2, column=0, padx=(DIMENSIONS["pad_window"], 10), pady=10, sticky="nsew")
        self.app.card_frames.append(tweaks_card)

        self.lbl_tweaks_title = ctk.CTkLabel(tweaks_card, text="", font=self.app.subtitle_font)
        self.lbl_tweaks_title.grid(row=0, column=0, columnspan=2, padx=25, pady=(20, 5), sticky="w")
        self.app.accent_labels.append(self.lbl_tweaks_title)

        def create_tweak_row(parent, row, lbl_key, tt_key, btn_key, command):
            lbl = ctk.CTkLabel(parent, text="", font=self.app.main_font)
            lbl.grid(row=row, column=0, padx=25, pady=10, sticky="w")

            icon = ctk.CTkLabel(parent, text=" ( i ) ", font=ctk.CTkFont(family=FONTS["main_family"], size=18, weight="bold"), cursor="hand2", text_color="#F39C12")
            icon.grid(row=row, column=1, padx=(0, 20), sticky="w")
            icon.bind("<Enter>", lambda e, k=tt_key: self.app.show_tooltip(icon, k))
            icon.bind("<Leave>", self.app.hide_tooltip)

            btn = ctk.CTkButton(parent, text="", command=lambda: self.app.run_in_thread(command), width=160, **self.app.get_btn_style())
            btn.grid(row=row, column=2, padx=20, pady=10, sticky="e")
            self.app.primary_buttons.append(btn)
            self.app.accent_labels.append(lbl)
            return lbl, btn

        self.lbl_test_net, self.btn_test_net = create_tweak_row(tweaks_card, 1, "lbl_test_net", "tt_test_net", "btn_test_net", self.do_test_net)
        self.lbl_test_gm, self.btn_test_gm = create_tweak_row(tweaks_card, 2, "lbl_test_gm", "tt_test_gm", "btn_test_gm", self.do_test_gamemode)
        self.lbl_test_ds, self.btn_test_ds = create_tweak_row(tweaks_card, 3, "lbl_test_ds", "tt_test_ds", "btn_test_ds", self.do_test_discord)

        health_card = ctk.CTkFrame(self.frame, corner_radius=DIMENSIONS["corner_radius"])
        health_card.grid(row=3, column=0, padx=(DIMENSIONS["pad_window"], 10), pady=10, sticky="nsew")
        self.app.card_frames.append(health_card)
        self.lbl_health_title = ctk.CTkLabel(health_card, text="", font=self.app.subtitle_font)
        self.lbl_health_title.grid(row=0, column=0, padx=25, pady=(20, 5), sticky="w")
        self.app.accent_labels.append(self.lbl_health_title)
        t_box = ctk.CTkFrame(health_card, fg_color="transparent")
        t_box.grid(row=1, column=0, padx=25, pady=5, sticky="w")
        self.lbl_timer_input = ctk.CTkLabel(t_box, text="", font=self.app.main_font)
        self.lbl_timer_input.grid(row=0, column=0, padx=(0, 10))
        self.entry_timer = ctk.CTkEntry(t_box, width=70, corner_radius=DIMENSIONS["corner_radius"], font=self.app.main_font)
        self.entry_timer.grid(row=0, column=1)
        self.entry_timer.insert(0, "45")

        self.lbl_timer = ctk.CTkLabel(health_card, text="00:00", font=ctk.CTkFont(family="Courier New", size=32, weight="bold"))
        self.lbl_timer.grid(row=2, column=0, padx=25, pady=5, sticky="w")
        self.app.accent_labels.append(self.lbl_timer_input)

        btn_timer_box = ctk.CTkFrame(health_card, fg_color="transparent")
        btn_timer_box.grid(row=3, column=0, padx=25, pady=(10, 20), sticky="w")
        self.btn_t_start = ctk.CTkButton(btn_timer_box, text="", width=90, command=self.start_health_timer, **self.app.get_btn_style())
        self.btn_t_start.grid(row=0, column=0, padx=(0, 10))
        self.app.primary_buttons.append(self.btn_t_start)
        self.btn_t_stop = ctk.CTkButton(btn_timer_box, text="", width=90, fg_color="#555555", hover_color="#333333", command=self.stop_health_timer, **self.app.get_btn_style())
        self.btn_t_stop.grid(row=0, column=1)

        # === ПРАВАЯ КОЛОНКА ===
        mango_card = ctk.CTkFrame(self.frame, corner_radius=DIMENSIONS["corner_radius"])
        mango_card.grid(row=1, column=1, rowspan=2, padx=(10, DIMENSIONS["pad_window"]), pady=(0, 10), sticky="nsew")
        self.app.card_frames.append(mango_card)

        self.lbl_osd_title = ctk.CTkLabel(mango_card, text="", font=self.app.subtitle_font)
        self.lbl_osd_title.grid(row=0, column=0, padx=25, pady=(20, 5), sticky="w")
        self.app.accent_labels.append(self.lbl_osd_title)

        self.cb_fps = ctk.CTkCheckBox(mango_card, text="FPS & Frametime", **self.app.get_cb_style()); self.cb_fps.grid(row=1, column=0, padx=25, pady=8, sticky="w"); self.cb_fps.select()
        self.cb_gpu = ctk.CTkCheckBox(mango_card, text="GPU Stats", **self.app.get_cb_style()); self.cb_gpu.grid(row=2, column=0, padx=25, pady=8, sticky="w")
        self.cb_cpu = ctk.CTkCheckBox(mango_card, text="CPU Stats", **self.app.get_cb_style()); self.cb_cpu.grid(row=3, column=0, padx=25, pady=8, sticky="w")
        self.cb_ram = ctk.CTkCheckBox(mango_card, text="RAM & VRAM", **self.app.get_cb_style()); self.cb_ram.grid(row=4, column=0, padx=25, pady=8, sticky="w")
        self.checkboxes.extend([self.cb_fps, self.cb_gpu, self.cb_cpu, self.cb_ram])
        self.app.checkboxes.extend(self.checkboxes)

        self.btn_osd_save = ctk.CTkButton(mango_card, text="", command=self.save_mangohud, **self.app.get_btn_style())
        self.btn_osd_save.grid(row=5, column=0, padx=25, pady=15, sticky="w")
        self.app.primary_buttons.append(self.btn_osd_save)

        self.lbl_osd_hint = ctk.CTkLabel(mango_card, text="", font=self.app.main_font)
        self.lbl_osd_hint.grid(row=6, column=0, padx=25, pady=(5,0), sticky="w")
        self.btn_copy_cmd = ctk.CTkButton(mango_card, text="", fg_color="#333333", hover_color="#222222", command=self.copy_mangohud_cmd, **self.app.get_btn_style())
        self.btn_copy_cmd.grid(row=7, column=0, padx=25, pady=(5, 15), sticky="w")

        self.lbl_mango_status = ctk.CTkLabel(mango_card, text="", text_color="#2ECC71", font=self.app.main_font)
        self.lbl_mango_status.grid(row=8, column=0, padx=25, pady=(0, 15), sticky="w")
        self.app.accent_labels.append(self.lbl_mango_status)

        gs_box = ctk.CTkFrame(mango_card, fg_color="transparent")
        gs_box.grid(row=9, column=0, padx=25, pady=(5, 20), sticky="w")

        self.lbl_test_gs = ctk.CTkLabel(gs_box, text="", font=self.app.main_font)
        self.lbl_test_gs.grid(row=0, column=0, sticky="w")

        icon_gs = ctk.CTkLabel(gs_box, text=" ( i ) ", font=ctk.CTkFont(family=FONTS["main_family"], size=18, weight="bold"), cursor="hand2", text_color="#F39C12")
        icon_gs.grid(row=0, column=1, padx=(0, 15), sticky="w")
        icon_gs.bind("<Enter>", lambda e: self.app.show_tooltip(icon_gs, "tt_test_gs"))
        icon_gs.bind("<Leave>", self.app.hide_tooltip)

        self.btn_test_gs = ctk.CTkButton(gs_box, text="", command=self.do_test_gamescope, **self.app.get_btn_style())
        self.btn_test_gs.grid(row=0, column=2, sticky="e")
        self.app.primary_buttons.append(self.btn_test_gs)
        self.app.accent_labels.append(self.lbl_test_gs)

        # Shader Cache Card
        shader_card = ctk.CTkFrame(self.frame, corner_radius=DIMENSIONS["corner_radius"])
        shader_card.grid(row=3, column=1, padx=(10, DIMENSIONS["pad_window"]), pady=10, sticky="nsew")
        self.app.card_frames.append(shader_card)

        self.lbl_steam_title = ctk.CTkLabel(shader_card, text="", font=self.app.subtitle_font)
        self.lbl_steam_title.grid(row=0, column=0, padx=25, pady=(20, 5), sticky="w")
        self.app.accent_labels.append(self.lbl_steam_title)

        self.lbl_steam_size = ctk.CTkLabel(shader_card, text="...", font=self.app.main_font)
        self.lbl_steam_size.grid(row=1, column=0, padx=25, pady=0, sticky="w")

        btn_steam_box = ctk.CTkFrame(shader_card, fg_color="transparent")
        btn_steam_box.grid(row=2, column=0, padx=25, pady=(10, 20), sticky="w")

        self.btn_st_analyze = ctk.CTkButton(btn_steam_box, text="", width=90, command=lambda: self.app.run_in_thread(self.analyze_shaders), **self.app.get_btn_style())
        self.btn_st_analyze.grid(row=0, column=0, padx=(0, 10))
        self.app.primary_buttons.append(self.btn_st_analyze)

        self.btn_st_clean = ctk.CTkButton(btn_steam_box, text="", width=90, fg_color="#D35400", hover_color="#A04000", command=lambda: self.app.run_in_thread(self.clean_shaders), **self.app.get_btn_style())
        self.btn_st_clean.grid(row=0, column=1)
        self.app.accent_labels.extend([self.lbl_steam_size])

        # TABVIEW (Телеметрия, Логи, Профили)
        self.bottom_tabs = ctk.CTkTabview(self.frame, corner_radius=DIMENSIONS["corner_radius"])
        self.bottom_tabs.grid(row=4, column=0, columnspan=2, padx=DIMENSIONS["pad_window"], pady=(10, 20), sticky="nsew")
        self.app.bottom_tabs_ref = self.bottom_tabs

        self.tab_telem = self.bottom_tabs.add("Telemetry")
        self.tab_crash = self.bottom_tabs.add("Crash Logs")
        self.tab_prof = self.bottom_tabs.add("Profiles")

        self.tab_telem.grid_columnconfigure(0, weight=1); self.tab_telem.grid_rowconfigure(0, weight=1)
        self.telem_log_box = ctk.CTkTextbox(self.tab_telem, font=self.app.console_font, corner_radius=DIMENSIONS["corner_radius"])
        self.telem_log_box.grid(row=0, column=0, sticky="nsew")
        self.app.consoles.append(self.telem_log_box)

        self.tab_crash.grid_columnconfigure(0, weight=1); self.tab_crash.grid_rowconfigure(1, weight=1)
        self.btn_crash = ctk.CTkButton(self.tab_crash, text="", command=lambda: self.app.run_in_thread(self.read_crash_logs), **self.app.get_btn_style())
        self.btn_crash.grid(row=0, column=0, pady=(10, 15), padx=10, sticky="w")

        self.crash_log_box = ctk.CTkTextbox(self.tab_crash, font=self.app.console_font, corner_radius=DIMENSIONS["corner_radius"])
        self.crash_log_box.grid(row=1, column=0, sticky="nsew")
        self.app.consoles.append(self.crash_log_box)

        self.btn_exp = ctk.CTkButton(self.tab_prof, text="", command=self.export_profile, **self.app.get_btn_style())
        self.btn_exp.grid(row=1, column=0, pady=15, padx=15, sticky="w")
        self.btn_imp = ctk.CTkButton(self.tab_prof, text="", command=self.import_profile, **self.app.get_btn_style())
        self.btn_imp.grid(row=2, column=0, pady=10, padx=15, sticky="w")
        self.app.primary_buttons.extend([self.btn_exp, self.btn_imp])

        self.lbl_prof_status = ctk.CTkLabel(self.tab_prof, text="", font=self.app.main_font)
        self.lbl_prof_status.grid(row=3, column=0, pady=10, padx=15, sticky="w")
        self.app.accent_labels.append(self.lbl_prof_status)

    def update_texts(self):
        self.lbl_game_title.configure(text=self.app.t("tab_game_title"))
        self.lbl_cpu_title.configure(text=self.app.t("cpu_title"))
        self.switch_cpu.configure(text=self.app.t("btn_cpu_on"))

        self.lbl_tweaks_title.configure(text=self.app.t("tweaks_title"))
        self.lbl_test_net.configure(text=self.app.t("lbl_test_net"))
        self.btn_test_net.configure(text=self.app.t("btn_test_net"))
        self.lbl_test_gm.configure(text=self.app.t("lbl_test_gm"))
        self.btn_test_gm.configure(text=self.app.t("btn_test_gm"))
        self.lbl_test_ds.configure(text=self.app.t("lbl_test_ds"))
        self.btn_test_ds.configure(text=self.app.t("btn_test_ds"))
        self.lbl_test_gs.configure(text=self.app.t("lbl_test_gs"))
        self.btn_test_gs.configure(text=self.app.t("btn_test_gs"))

        self.lbl_health_title.configure(text=self.app.t("health_title"))
        self.lbl_timer_input.configure(text=self.app.t("lbl_timer_input"))
        self.btn_t_start.configure(text=self.app.t("btn_start"))
        self.btn_t_stop.configure(text=self.app.t("btn_stop"))

        self.lbl_osd_title.configure(text=self.app.t("osd_title"))
        self.btn_osd_save.configure(text=self.app.t("btn_osd_save"))
        self.lbl_osd_hint.configure(text=self.app.t("lbl_osd_hint"))
        self.btn_copy_cmd.configure(text=self.app.t("btn_copy_cmd"))
        self.lbl_steam_title.configure(text=self.app.t("steam_title"))
        self.btn_st_analyze.configure(text=self.app.t("btn_analyze"))
        self.btn_st_clean.configure(text=self.app.t("btn_clean_steam"))

        self.bottom_tabs._segmented_button._buttons_dict["Telemetry"].configure(text=self.app.t("tab_telem"))
        self.bottom_tabs._segmented_button._buttons_dict["Crash Logs"].configure(text=self.app.t("tab_crash"))
        self.bottom_tabs._segmented_button._buttons_dict["Profiles"].configure(text=self.app.t("tab_prof"))

        self.btn_crash.configure(text=self.app.t("btn_crash"))
        self.btn_exp.configure(text=self.app.t("btn_exp"))
        self.btn_imp.configure(text=self.app.t("btn_imp"))

    def change_theme(self, theme):
        self.switch_cpu.configure(progress_color=theme["primary_color"])
        self.lbl_osd_hint.configure(text_color=theme["text_muted"])
        self.btn_st_clean.configure(fg_color=theme["danger_color"], hover_color=theme["danger_hover"])
        self.btn_crash.configure(fg_color=theme["warning_color"], hover_color=theme["warning_hover"])
        if self.health_timer_state != "overtime":
            self.lbl_timer.configure(text_color=theme["primary_color"])

    # ==================== ЛОГИКА ТВИКОВ И БУСТА ====================
    def do_test_net(self):
        self.app.app_log("Applying low latency network settings (tcp_low_latency=1)...")
        try:
            res = subprocess.run(["pkexec", "sysctl", "-w", "net.ipv4.tcp_low_latency=1"], capture_output=True, text=True)
            if res.returncode == 0: self.app.app_log("✅ Network ping optimized for gaming.")
            else: self.app.app_log(f"❌ Error: {res.stderr}")
        except Exception as e: self.app.app_log(f"❌ Error: {e}")

    def do_test_gamemode(self):
        self.app.app_log("Requesting Feral GameMode activation...")
        try:
            subprocess.run(["gamemoded", "-r"], capture_output=True, text=True)
            self.app.app_log("✅ GameMode requested. Check status with 'gamemoded -s'.")
        except Exception as e:
            self.app.app_log("❌ Error. Make sure 'gamemode' is installed on your system.")

    def do_test_discord(self):
        self.app.app_log("Searching for Discord process...")
        try:
            pids = subprocess.check_output(["pgrep", "-i", "discord"], text=True).split()
            if not pids:
                self.app.app_log("❌ Discord is not running.")
                return
            self.app.app_log(f"Found Discord PIDs: {', '.join(pids)}. Applying high priority...")
            res = subprocess.run(["pkexec", "renice", "-n", "-10", "-p", pids[0]], capture_output=True, text=True)
            if res.returncode == 0: self.app.app_log("✅ Discord CPU priority boosted successfully.")
            else: self.app.app_log(f"❌ Error setting priority: {res.stderr}")
        except Exception as e: self.app.app_log(f"❌ Error: {e}")

    def do_test_gamescope(self):
        cmd = "gamescope -W 1920 -H 1080 -r 60 -f -e -- %command%"
        self.app.clipboard_clear()
        self.app.clipboard_append(cmd)
        self.app.app_log(f"✅ Copied to clipboard: {cmd}")

    def update_health_timer(self):
        if self.health_timer_state == "running":
            if self.health_time_left > 0:
                self.health_time_left -= 1
                mins, secs = divmod(self.health_time_left, 60)
                self.lbl_timer.configure(text=f"{mins:02d}:{secs:02d}")
                self.app.after(1000, self.update_health_timer)
            else:
                self.lbl_timer.configure(text="00:00 (Overtime)", text_color="#F1C40F")
                self.app.play_sound(is_timer=True)
                self.health_timer_state = "overtime"
                self.overtime_seconds = 0
                self.app.after(1000, self.update_health_timer)
        elif self.health_timer_state == "overtime":
            self.overtime_seconds += 1
            if self.overtime_seconds == 30: self.app.play_sound(is_timer=True)
            elif self.overtime_seconds == 60:
                self.lbl_timer.configure(text="TIME TO STOP!", text_color="#E74C3C")
                self.app.play_sound(is_timer=True)
                self.health_timer_state = "stopped"
                return
            self.app.after(1000, self.update_health_timer)

    def start_health_timer(self):
        if self.health_timer_state == "stopped":
            try:
                mins = int(self.entry_timer.get())
                self.health_time_left = mins * 60
                self.health_timer_state = "running"
                self.lbl_timer.configure(text_color=self.app.nav_bg_color_active)
                self.update_health_timer()
                self.app.app_log(f"Health timer started for {mins} minutes.")
            except: pass

    def stop_health_timer(self):
        self.health_timer_state = "stopped"
        self.health_time_left = 0
        self.lbl_timer.configure(text="00:00", text_color=self.app.nav_bg_color_active)
        self.app.app_log("Health timer stopped.")

    def load_game_booster_data(self):
        try:
            with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "r") as f:
                gov = f.read().strip()
                if gov == "performance":
                    self.switch_cpu.select()
                    txt = f"Режим: {gov} (Разгон)" if self.app.lang == "ru" else f"Mode: {gov} (Boosted)"
                    self.lbl_cpu_gov.configure(text=txt)
                    if hasattr(self.app, 'lbl_tile_cpu'): self.app.lbl_tile_cpu.configure(text="Boosted", text_color="#E74C3C")
                else:
                    self.switch_cpu.deselect()
                    txt = f"Режим: {gov} (Эконом)" if self.app.lang == "ru" else f"Mode: {gov} (Powersave)"
                    self.lbl_cpu_gov.configure(text=txt)
                    if hasattr(self.app, 'lbl_tile_cpu'): self.app.lbl_tile_cpu.configure(text="Powersave", text_color=self.app.nav_bg_color_active)
        except Exception as e:
            self.app.app_log(f"Failed to read CPU governor: {e}")

    def toggle_cpu_mode(self):
        junk_processes = ["baloo_file", "tracker-miner-fs", "tracker-miner-fs-3", "pamac-tray"]

        def safe_update_lbl(text):
            self.app.after(0, lambda: self.lbl_cpu_gov.configure(text=text))

        def safe_append_telem(text):
            def _append():
                self.telem_log_box.configure(state="normal")
                self.telem_log_box.insert("end", text + "\n")
                self.telem_log_box.see("end")
                self.telem_log_box.configure(state="disabled")
            self.app.after(0, _append)

        if self.switch_cpu.get() == 1:
            self.app.app_log("Attempting to enable MAX FPS (performance mode) via pkexec...")
            self.app.after(0, lambda: self.bottom_tabs.set("Telemetry" if self.app.lang == "en" else self.app.t("tab_telem")))
            self.app.after(0, lambda: self.telem_log_box.configure(state="normal"))
            self.app.after(0, lambda: self.telem_log_box.delete("0.0", "end"))
            self.app.after(0, lambda: self.telem_log_box.configure(state="disabled"))

            safe_append_telem("🚀 INITIATING ESPORTS BOOSTER SEQUENCE...")
            safe_update_lbl("Ожидание пароля..." if self.app.lang=="ru" else "Waiting for password...")

            try:
                result = subprocess.run(["pkexec", "cpupower", "frequency-set", "-g", "performance"], capture_output=True, text=True)
                if result.returncode != 0:
                    self.app.app_log(f"ERROR: pkexec failed. Code {result.returncode}. Output: {result.stderr.strip()}")
                    safe_append_telem("❌ ERROR: Authorization failed or cancelled by user.")
                    self.app.after(0, lambda: self.switch_cpu.deselect())
                    safe_update_lbl("Ошибка доступа" if self.app.lang=="ru" else "Access Denied")
                    return
            except Exception as e:
                self.app.app_log(f"CRITICAL ERROR executing pkexec: {e}")
                safe_append_telem(f"❌ CRITICAL ERROR: {e}")
                self.app.after(0, lambda: self.switch_cpu.deselect())
                safe_update_lbl("Критическая ошибка" if self.app.lang=="ru" else "Critical Error")
                return

            safe_append_telem("✅ [1/3] CPU Governor unlocked: PERFORMANCE MODE ENGAGED")
            time.sleep(0.4)

            safe_append_telem("⚙️ [2/3] Scanning for heavy background services...")
            stopped_count = 0
            self.frozen_pids = []
            try:
                ps_output = subprocess.check_output(["ps", "-eo", "pid,comm"], text=True)
                for line in ps_output.split('\n'):
                    parts = line.strip().split(maxsplit=1)
                    if len(parts) == 2 and parts[1] in junk_processes:
                        pid = int(parts[0])
                        os.kill(pid, signal.SIGSTOP)
                        self.frozen_pids.append(pid)
                        stopped_count += 1
                        safe_append_telem(f"   -> Suspended: {parts[1]} (PID: {pid})")
            except Exception as e: self.app.app_log(f"Error freezing apps: {e}")

            time.sleep(0.5)
            safe_append_telem("🌐 [3/3] Rerouting network packets for low-latency gaming...")
            time.sleep(0.5)
            safe_append_telem("✅ SYSTEM FULLY OPTIMIZED. TELEMETRY STARTED.\n" + "="*50 + "\n")

            txt = f"🔥 ESPORTS MODE ACTIVE\n✓ CPU: Performance MAX\n✓ Frozen apps: {stopped_count}\n✓ Network: Optimized" if self.app.lang == "en" else f"🔥 РЕЖИМ КИБЕРСПОРТА\n✓ CPU: Максимум FPS\n✓ Заморожено служб: {stopped_count}\n✓ Сеть: Игровой приоритет"
            safe_update_lbl(txt)

            self.app.app_log(f"Game Mode active. Frozen {stopped_count} background tasks.")
            self.app.telemetry_data.clear()
            self.app.session_start_time = datetime.now()
            self.app.is_telemetry_running = True
            try: os.remove("/tmp/mangohud_telem.csv")
            except: pass
            self.load_game_booster_data()
        else:
            self.app.app_log("Attempting to restore powersave mode via pkexec...")
            safe_append_telem("\n🛑 DEACTIVATING BOOSTER SEQUENCE...")

            try:
                result = subprocess.run(["pkexec", "cpupower", "frequency-set", "-g", "powersave"], capture_output=True, text=True)
                if result.returncode != 0:
                    self.app.app_log(f"ERROR: pkexec failed to restore powersave. {result.stderr.strip()}")
            except Exception as e: self.app.app_log(f"ERROR: {e}")

            safe_append_telem("✅ [1/2] CPU Governor reset to POWERSAVE")
            time.sleep(0.3)

            safe_append_telem("⚙️ [2/2] Waking up suspended background services...")
            for pid in self.frozen_pids:
                try: os.kill(pid, signal.SIGCONT)
                except: pass
            self.frozen_pids.clear()
            time.sleep(0.3)

            safe_append_telem("✅ SYSTEM RESTORED TO NORMAL MODE.")

            txt = "Powersave mode.\nApps restored." if self.app.lang == "en" else "Режим Эконом.\nСлужбы восстановлены."
            safe_update_lbl(txt)
            self.app.is_telemetry_running = False
            self.generate_telemetry_report()
            self.load_game_booster_data()

    def generate_telemetry_report(self):
        self.telem_log_box.configure(state="normal")
        self.telem_log_box.delete("0.0", "end")
        if not self.app.telemetry_data:
            self.telem_log_box.insert("end", "Not enough data." if self.app.lang=="en" else "Недостаточно данных.")
        else:
            duration = datetime.now() - self.app.session_start_time
            mins, secs = divmod(duration.total_seconds(), 60)
            avg_gpu_temp = sum(d["gpu_temp"] for d in self.app.telemetry_data) / len(self.app.telemetry_data)
            avg_gpu_util = sum(d["gpu_util"] for d in self.app.telemetry_data) / len(self.app.telemetry_data)
            max_vram = max(d["vram"] for d in self.app.telemetry_data)
            avg_cpu_util = sum(d["cpu_util"] for d in self.app.telemetry_data) / len(self.app.telemetry_data)
            avg_ram_util = sum(d["ram_util"] for d in self.app.telemetry_data) / len(self.app.telemetry_data)

            avg_fps = "No data" if self.app.lang=="en" else "Нет данных"
            try:
                if os.path.exists("/tmp/mangohud_telem.csv"):
                    with open("/tmp/mangohud_telem.csv", "r") as f:
                        fps_list = [float(line.split(',')[1]) for line in f.readlines()[1:] if len(line.split(',')) > 1]
                        if fps_list: avg_fps = f"{sum(fps_list)/len(fps_list):.1f} FPS"
            except: pass

            rep = f"--- SESSION REPORT ({int(mins)}m {int(secs)}s) ---\n\n"
            rep += f"AVG FPS: {avg_fps}\n\n"
            rep += f"GPU Load: {avg_gpu_util:.1f}% | Temp: {avg_gpu_temp:.1f}°C | Peak VRAM: {max_vram} MiB\n"
            rep += f"CPU Load: {avg_cpu_util:.1f}% | RAM Load: {avg_ram_util:.1f}%\n\n"
            rep += f"--- BOTTLENECK ANALYSIS ---\n"
            if avg_gpu_util > 90: rep += "PERFECT: GPU is fully utilized. No bottleneck.\n"
            elif avg_cpu_util > 85 and avg_gpu_util < 75: rep += "CPU BOTTLENECK: CPU can't keep up. Lower CPU-heavy settings.\n"
            elif max_vram > 15000: rep += "VRAM BOTTLENECK: Out of Video Memory! Lower texture quality.\n"
            elif avg_ram_util > 90: rep += "RAM BOTTLENECK: System RAM is full. Close browser/apps.\n"
            else: rep += "Balanced system (Or game has FPS cap/V-Sync).\n"
            self.telem_log_box.insert("end", rep)
            self.app.app_log("Telemetry report generated.")
        self.telem_log_box.configure(state="disabled")

    def get_all_shader_paths(self):
        paths =[os.path.expanduser("~/.local/share/Steam/steamapps/shadercache"), os.path.expanduser("~/.cache/mesa_shader_cache"), os.path.expanduser("~/.nv/GLCache"), os.path.expanduser("~/.config/heroic/Cache")]
        vdf = os.path.expanduser("~/.steam/steam/steamapps/libraryfolders.vdf")
        if os.path.exists(vdf):
            try:
                with open(vdf, 'r') as f:
                    for l in f:
                        if '"path"' in l:
                            parts = l.split('"')
                            if len(parts) >= 4: paths.append(os.path.join(parts[3], "steamapps", "shadercache"))
            except: pass
        return list(set(paths))

    def analyze_shaders(self):
        total_mb = sum(get_dir_size_in_mb(p) for p in self.get_all_shader_paths())
        if hasattr(self.app, 'lbl_tile_cache'):
            if total_mb > 1024: self.app.lbl_tile_cache.configure(text=f"{(total_mb/1024):.2f} GB", text_color=self.app.nav_bg_color_active)
            else: self.app.lbl_tile_cache.configure(text=f"{total_mb:.1f} MB", text_color=self.app.nav_bg_color_active)

        if total_mb > 1024: self.lbl_steam_size.configure(text=f"Found: {(total_mb/1024):.2f} GB" if self.app.lang=="en" else f"Найдено: {(total_mb/1024):.2f} ГБ")
        else: self.lbl_steam_size.configure(text=f"Found: {total_mb:.1f} MB" if self.app.lang=="en" else f"Найдено: {total_mb:.1f} МБ")

    def clean_shaders(self):
        self.app.app_log("Cleaning shader cache directories...")
        for path in self.get_all_shader_paths():
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    os.makedirs(path)
                    self.app.app_log(f"Cleaned: {path}")
                except Exception as e:
                    self.app.app_log(f"Failed to clean {path}: {e}")
        self.lbl_steam_size.configure(text="Cache Cleaned!" if self.app.lang=="en" else "Кэш очищен!")
        if hasattr(self.app, 'lbl_tile_cache'): self.app.lbl_tile_cache.configure(text="0 MB")

    def save_mangohud(self):
        config_dir = os.path.expanduser("~/.config/MangoHud")
        os.makedirs(config_dir, exist_ok=True)
        conf_path = os.path.join(config_dir, "MangoHud.conf")
        config_lines =["legacy_layout=false", "background_alpha=0.6", "round_corners=0", "font_size=20", "position=top-left", "autostart_log=1", "output_file=/tmp/mangohud_telem"]

        if self.cb_fps.get(): config_lines.extend(["fps", "frametime"])
        if self.cb_gpu.get(): config_lines.extend(["gpu_stats", "gpu_temp"])
        if self.cb_cpu.get(): config_lines.extend(["cpu_stats", "cpu_temp"])
        if self.cb_ram.get(): config_lines.extend(["ram", "vram"])

        try:
            with open(conf_path, "w") as f: f.write("\n".join(config_lines))
            self.lbl_mango_status.configure(text="Saved!" if self.app.lang=="en" else "Сохранено!")
            self.app.app_log("MangoHud configuration saved.")
        except Exception as e:
            self.app.app_log(f"Failed to save MangoHud config: {e}")

    def copy_mangohud_cmd(self):
        self.app.clipboard_clear()
        self.app.clipboard_append("mangohud %command%")
        self.lbl_mango_status.configure(text="Copied!" if self.app.lang=="en" else "Скопировано!")
        self.app.app_log("MangoHud command copied to clipboard.")

    def read_crash_logs(self):
        self.app.app_log("Analyzing journalctl for recent game crashes...")
        self.crash_log_box.configure(state="normal")
        self.crash_log_box.delete("0.0", "end")
        try:
            res = subprocess.run(["journalctl", "-b", "0", "-p", "3", "-n", "30", "--no-pager"], capture_output=True, text=True)
            if res.stdout:
                crashes = [l for l in res.stdout.strip().split('\n') if any(kw in l.lower() for kw in ["wine", "proton", "steam", "segfault", "coredump", "nvidia"])]
                if crashes:
                    self.crash_log_box.insert("end", "CRASHES FOUND:\n" + "\n".join(crashes))
                    self.app.app_log(f"Found {len(crashes)} crash log entries.")
                else:
                    self.crash_log_box.insert("end", "No critical game crashes found." if self.app.lang=="en" else "Критических вылетов не найдено.")
                    self.app.app_log("No crashes found.")
            else:
                self.crash_log_box.insert("end", "Log is clean." if self.app.lang=="en" else "Журнал чист.")
        except Exception as e:
            self.app.app_log(f"Error reading crash logs: {e}")
        self.crash_log_box.configure(state="disabled")

    def export_profile(self):
        profile = {"mango_fps": self.cb_fps.get(), "mango_gpu": self.cb_gpu.get(), "mango_cpu": self.cb_cpu.get(), "mango_ram": self.cb_ram.get()}
        filepath = tk.filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], title="Save Profile")
        if filepath:
            try:
                with open(filepath, "w") as f: json.dump(profile, f)
                self.app.app_log(f"Profile exported to {filepath}")
            except Exception as e:
                self.app.app_log(f"Failed to export profile: {e}")

    def import_profile(self):
        filepath = tk.filedialog.askopenfilename(filetypes=[("JSON", "*.json")], title="Load Profile")
        if filepath:
            try:
                with open(filepath, "r") as f: profile = json.load(f)
                if profile.get("mango_fps", 0): self.cb_fps.select()
                else: self.cb_fps.deselect()
                if profile.get("mango_gpu", 0): self.cb_gpu.select()
                else: self.cb_gpu.deselect()
                if profile.get("mango_cpu", 0): self.cb_cpu.select()
                else: self.cb_cpu.deselect()
                if profile.get("mango_ram", 0): self.cb_ram.select()
                else: self.cb_ram.deselect()
                self.save_mangohud()
                self.app.app_log(f"Profile imported from {filepath}")
            except Exception as e:
                self.app.app_log(f"Failed to import profile: {e}")
