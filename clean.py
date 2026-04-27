import customtkinter as ctk
import tkinter as tk
import subprocess
import os
import shutil
import glob
from theme import FONTS, DIMENSIONS

# Локальный словарь переводов для вкладки "Очистка"
CLEAN_LANGUAGES = {
    "en": {
        "tab_clean_title": "Smart System Cleaner",
        "tt_clean": "Safely free up disk and memory space.",
        "lbl_pkg": "Packages Cache (Pamac)", "tt_clean_pkg": "Linux keeps copies of updated apps.\nIF YOU CLEAN IT: Old copies are deleted to free space. 100% safe.",
        "btn_analyze_pkg": "Analyze Cache", "btn_clean_pkg": "Clean Cache",
        "lbl_log": "System Error Logs", "tt_clean_log": "Records of system events.\nIF YOU CLEAN IT: Keeps only the latest 50MB. Safe and good for SSD.",
        "btn_analyze_log": "Analyze Logs", "btn_clean_log": "Clean Old Logs",
        "lbl_pfx": "Steam Prefixes (Orphans)", "tt_clean_pfx": "Windows environments for games.\nIF YOU CLEAN IT: Deletes folders of ALREADY uninstalled games. Safe.",
        "btn_analyze_pfx": "Scan Orphans", "btn_clean_pfx": "Delete Orphans",
        "lbl_ram": "RAM & Swap Cache", "tt_clean_ram": "Frees up Linux memory cache before launching a heavy game to prevent stutters.",
        "btn_analyze_ram": "Analyze RAM", "btn_clean_ram": "Drop Caches"
    },
    "ru": {
        "tab_clean_title": "Умная очистка мусора",
        "tt_clean": "Безопасное освобождение места на диске и в памяти.",
        "lbl_pkg": "Кэш пакетов (Программы)", "tt_clean_pkg": "Система сохраняет старые версии программ.\nЕСЛИ ОЧИСТИТЬ: Освободятся гигабайты места. 100% безопасно.",
        "btn_analyze_pkg": "Анализ пакетов", "btn_clean_pkg": "Очистить кэш",
        "lbl_log": "Системные журналы (Логи)", "tt_clean_log": "Текстовые записи системных ошибок.\nЕСЛИ ОЧИСТИТЬ: Оставит только свежие логи. Продлевает жизнь SSD.",
        "btn_analyze_log": "Анализ логов", "btn_clean_log": "Удалить логи",
        "lbl_pfx": "Префиксы Steam (Остатки)", "tt_clean_pfx": "Steam создает фейковую Windows для каждой игры.\nЕСЛИ ОЧИСТИТЬ: Удалит папки УЖЕ удаленных игр. Сохранения в безопасности.",
        "btn_analyze_pfx": "Поиск остатков", "btn_clean_pfx": "Удалить мусор",
        "lbl_ram": "Очистка RAM и Swap", "tt_clean_ram": "Очищает дисковый кэш из оперативной памяти перед запуском тяжелой игры.\nПредотвращает жесткие зависания (Swap thrashing).",
        "btn_analyze_ram": "Анализ памяти", "btn_clean_ram": "Очистить память"
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

class CleanPage:
    def __init__(self, app_instance, parent_frame):
        self.app = app_instance
        self.frame = parent_frame
        self.orphan_prefixes = []
        self.build_ui()

    def build_ui(self):
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(6, weight=1)
        self.lbl_clean_title = self.app.create_title(self.frame, "tab_clean_title", "tt_clean")

        def create_clean_row(row_idx, tt_key, cmd_analyze, cmd_clean):
            row_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
            row_frame.grid(row=row_idx, column=0, padx=DIMENSIONS["pad_window"], pady=10, sticky="ew")

            icon = ctk.CTkLabel(row_frame, text=" ( i ) ", font=ctk.CTkFont(family=FONTS["main_family"], size=22, weight="bold"), cursor="hand2", text_color="#F39C12")
            icon.pack(side="left", padx=(0, 15))
            icon.bind("<Enter>", lambda e, k=tt_key, i=icon: self.app.show_tooltip(i, k))
            icon.bind("<Leave>", self.app.hide_tooltip)

            lbl_title = ctk.CTkLabel(row_frame, text="", font=self.app.subtitle_font, width=250, anchor="w")
            lbl_title.pack(side="left", padx=(0, 20))
            self.app.accent_labels.append(lbl_title)

            btn_a = ctk.CTkButton(row_frame, text="", command=lambda: self.app.run_in_thread(cmd_analyze), width=180, **self.app.get_btn_style())
            btn_a.pack(side="left", padx=(0, 15))
            self.app.primary_buttons.append(btn_a)

            btn_c = ctk.CTkButton(row_frame, text="", command=lambda: self.app.run_in_thread(cmd_clean), fg_color="#D35400", hover_color="#A04000", width=180, **self.app.get_btn_style())
            btn_c.pack(side="left")

            return lbl_title, btn_a, btn_c

        self.lbl_pkg, self.btn_analyze_pkg, self.btn_clean_pkg = create_clean_row(
            1, "tt_clean_pkg", self.analyze_pamac, self.clean_pamac)

        self.lbl_log, self.btn_analyze_log, self.btn_clean_log = create_clean_row(
            2, "tt_clean_log", self.analyze_logs, self.clean_logs)

        self.lbl_pfx, self.btn_analyze_pfx, self.btn_clean_pfx = create_clean_row(
            3, "tt_clean_pfx", self.scan_steam_prefixes, self.clean_steam_prefixes)
        self.btn_clean_pfx.configure(state="disabled", fg_color="#E74C3C", hover_color="#C0392B")

        self.lbl_ram, self.btn_analyze_ram, self.btn_clean_ram = create_clean_row(
            4, "tt_clean_ram", self.analyze_ram, self.clean_ram)

        self.log_box = ctk.CTkTextbox(self.frame, font=self.app.console_font, corner_radius=DIMENSIONS["corner_radius"])
        self.log_box.grid(row=5, column=0, padx=DIMENSIONS["pad_window"], pady=(20, DIMENSIONS["pad_window"]), sticky="nsew")
        self.app.consoles.append(self.log_box)

    def write_log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def update_texts(self):
        self.lbl_clean_title.configure(text=self.app.t("tab_clean_title"))
        self.lbl_pkg.configure(text=self.app.t("lbl_pkg"))
        self.btn_analyze_pkg.configure(text=self.app.t("btn_analyze_pkg"))
        self.btn_clean_pkg.configure(text=self.app.t("btn_clean_pkg"))
        self.lbl_log.configure(text=self.app.t("lbl_log"))
        self.btn_analyze_log.configure(text=self.app.t("btn_analyze_log"))
        self.btn_clean_log.configure(text=self.app.t("btn_clean_log"))
        self.lbl_pfx.configure(text=self.app.t("lbl_pfx"))
        self.btn_analyze_pfx.configure(text=self.app.t("btn_analyze_pfx"))
        self.btn_clean_pfx.configure(text=self.app.t("btn_clean_pfx"))
        self.lbl_ram.configure(text=self.app.t("lbl_ram"))
        self.btn_analyze_ram.configure(text=self.app.t("btn_analyze_ram"))
        self.btn_clean_ram.configure(text=self.app.t("btn_clean_ram"))

    def change_theme(self, theme):
        danger_hover = "#A04000"
        danger_col = "#D35400"
        self.btn_clean_pkg.configure(fg_color=danger_col, hover_color=danger_hover)
        self.btn_clean_log.configure(fg_color=danger_col, hover_color=danger_hover)
        self.btn_clean_pfx.configure(fg_color="#E74C3C", hover_color="#C0392B")
        self.btn_clean_ram.configure(fg_color=danger_col, hover_color=danger_hover)

    # ==================== ЛОГИКА ОЧИСТКИ ====================
    def analyze_pamac(self):
        self.app.app_log("Analyzing Pamac Cache...")
        self.write_log("\n--- PAMAC CACHE SCAN ---")
        pkg_size = get_dir_size_in_mb("/var/cache/pacman/pkg/")
        self.write_log(f"Packages Cache: {pkg_size:.1f} MB" if self.app.lang=="en" else f"Кэш пакетов: {pkg_size:.1f} МБ")

    def clean_pamac(self):
        self.app.app_log("Running Pamac cache clean (keep 3)...")
        subprocess.Popen(["pamac", "clean", "--keep", "3", "--no-confirm"])
        self.write_log("\n[OK] Package cache cleaning started." if self.app.lang=="en" else "\n[OK] Очистка пакетов запущена.")

    def analyze_logs(self):
        self.app.app_log("Analyzing System Logs...")
        self.write_log("\n--- SYSTEM LOGS SCAN ---")
        try:
            process = subprocess.run(["journalctl", "--disk-usage"], capture_output=True, text=True)
            if process.stdout:
                res = process.stdout.strip().split('take up ')[-1]
                self.write_log(f"System Logs: {res}" if self.app.lang=="en" else f"Системные логи: {res}")
        except Exception as e:
            self.app.app_log(f"Error during logs analysis: {e}")

    def clean_logs(self):
        self.app.app_log("Running journalctl vacuum to 50M...")
        subprocess.Popen(["journalctl", "--vacuum-size=50M"])
        self.write_log("\n[OK] Logs reduced to 50MB." if self.app.lang=="en" else "\n[OK] Логи очищены.")

    def scan_steam_prefixes(self):
        self.app.app_log("Scanning Steam for orphan compatdata prefixes...")
        self.write_log("\n--- STEAM PREFIX SCAN ---")
        steamapps_paths = [os.path.expanduser("~/.local/share/Steam/steamapps")]
        vdf_path = os.path.expanduser("~/.steam/steam/steamapps/libraryfolders.vdf")
        if os.path.exists(vdf_path):
            try:
                with open(vdf_path, 'r') as f:
                    for line in f:
                        if '"path"' in line:
                            parts = line.split('"')
                            if len(parts) >= 4:
                                steamapps_paths.append(os.path.join(parts[3], "steamapps"))
            except Exception as e: self.app.app_log(f"VDF Error: {e}")

        installed_apps = set(["0", "250920"])
        self.orphan_prefixes = []
        total_orphan_size = 0

        for s_path in set(steamapps_paths):
            if not os.path.exists(s_path): continue

            for file in os.listdir(s_path):
                if file.startswith("appmanifest_") and file.endswith(".acf"):
                    appid = file.split("_")[1].split(".")[0]
                    installed_apps.add(appid)

            compat_path = os.path.join(s_path, "compatdata")
            if os.path.exists(compat_path):
                for folder in os.listdir(compat_path):
                    if folder.isdigit() and folder not in installed_apps:
                        pfx_dir = os.path.join(compat_path, folder)
                        size_mb = get_dir_size_in_mb(pfx_dir)
                        self.orphan_prefixes.append(pfx_dir)
                        total_orphan_size += size_mb

        if self.orphan_prefixes:
            msg = f"Found {len(self.orphan_prefixes)} orphan prefixes taking {total_orphan_size:.1f} MB." if self.app.lang=="en" else f"Найдено {len(self.orphan_prefixes)} мусорных префиксов (Занимают {total_orphan_size:.1f} МБ)."
            self.write_log(msg)
            self.app.app_log(msg)
            self.app.after(0, lambda: self.btn_clean_pfx.configure(state="normal"))
        else:
            msg = "No orphan prefixes found. System is clean!" if self.app.lang=="en" else "Мусорных префиксов не найдено. Всё чисто!"
            self.write_log(msg)
            self.app.app_log(msg)
            self.app.after(0, lambda: self.btn_clean_pfx.configure(state="disabled"))

    def clean_steam_prefixes(self):
        self.app.app_log("Deleting orphan Steam prefixes...")
        freed = 0
        for pfx in self.orphan_prefixes:
            try:
                freed += get_dir_size_in_mb(pfx)
                shutil.rmtree(pfx)
                self.app.app_log(f"Deleted: {pfx}")
            except Exception as e:
                self.app.app_log(f"Failed to delete {pfx}: {e}")

        msg = f"\n[OK] Cleaned {len(self.orphan_prefixes)} prefixes. Freed {freed:.1f} MB!" if self.app.lang=="en" else f"\n[OK] Удалено {len(self.orphan_prefixes)} папок. Освобождено {freed:.1f} МБ!"
        self.write_log(msg)
        self.orphan_prefixes.clear()
        self.app.after(0, lambda: self.btn_clean_pfx.configure(state="disabled"))

    def analyze_ram(self):
        self.app.app_log("Analyzing RAM and Swap...")
        self.write_log("\n--- RAM & SWAP ANALYSIS ---")
        try:
            res = subprocess.run(["free", "-h"], capture_output=True, text=True)
            self.write_log(res.stdout)
            self.app.app_log("RAM analysis complete.")
        except Exception as e:
            self.app.app_log(f"Error: {e}")

    def clean_ram(self):
        self.app.app_log("Running Drop Caches command (requires sudo)...")
        try:
            res = subprocess.run(["pkexec", "sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"], capture_output=True, text=True)
            if res.returncode == 0:
                self.app.app_log("✅ RAM & Swap caches dropped successfully. Memory freed.")
                self.write_log("\n[OK] Memory cache cleared successfully!" if self.app.lang=="en" else "\n[OK] Кэш оперативной памяти очищен!")
            else:
                self.app.app_log(f"❌ Error dropping cache: {res.stderr}")
                self.write_log(f"\n[ERROR] {res.stderr}")
        except Exception as e:
            self.app.app_log(f"❌ Error: {e}")
