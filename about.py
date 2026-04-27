import customtkinter as ctk
import webbrowser
from theme import DIMENSIONS
from PIL import Image
import os
import sys

# Функция для поиска ресурсов внутри сборки
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)
    if not os.path.exists(path):
        path = os.path.join(base_path, "_internal", relative_path)
    return path

# Локальный словарь переводов
ABOUT_LANGUAGES = {
    "en": {
        "abt_title": "About Application",
        "tt_abt": "Information about the developer and open-source licenses.",
        "abt_text": "Manjaro Gaming Control v1.0.0\nCreated by: Serhii K.\n\nThis software is 100% free and open-source.\nDesigned specifically to bring the best gaming experience\nto Manjaro Linux users.",
        "lbl_donate": "Support the Developer:",
        "lbl_coffee_msg": "If my work helped you out, a coffee is the best way to fuel my late-night coding sessions!",
        "btn_bmac": "Buy Me a Coffee",
        "card_title_about": "About the App",
        "card_title_donate": "Support the Project"
    },
    "ru": {
        "abt_title": "О программе",
        "tt_abt": "Информация об авторе программы и лицензиях.",
        "abt_text": "Manjaro Gaming Control v1.0.0\nАвтор программы: Serhii K.\n\nПрограмма распространяется абсолютно бесплатно.\nСоздана специально для того, чтобы дать пользователям Manjaro Linux\nмаксимальный комфорт и производительность в играх.",
        "lbl_donate": "Поддержать разработчика:",
        "lbl_coffee_msg": "Если моя работа вам помогла, чашка кофе — лучший способ зарядить меня энергией для ночной разработки!",
        "btn_bmac": "Купить мне кофе",
        "card_title_about": "О приложении",
        "card_title_donate": "Поддержать проект"
    }
}

class AboutPage:
    def __init__(self, app_instance, parent_frame):
        self.app = app_instance
        self.frame = parent_frame

        self.donate_img = None
        self.build_ui()

    def build_ui(self):
        # 2 колонки
        self.frame.grid_columnconfigure((0, 1), weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        self.lbl_abt_title = self.app.create_title(self.frame, "abt_title", "tt_abt")

        # --- ЛЕВАЯ КАРТОЧКА ---
        about_card = ctk.CTkFrame(self.frame, corner_radius=DIMENSIONS["corner_radius"])
        about_card.grid(row=1, column=0, padx=(DIMENSIONS["pad_window"], 10), pady=10, sticky="nsew")
        self.app.card_frames.append(about_card)

        self.lbl_card_title_about = ctk.CTkLabel(about_card, text="", font=self.app.subtitle_font)
        self.lbl_card_title_about.pack(padx=25, pady=(20, 10), anchor="w")
        self.app.accent_labels.append(self.lbl_card_title_about)

        self.lbl_abt_text = ctk.CTkLabel(about_card, text="", font=self.app.main_font, justify="left", wraplength=400)
        self.lbl_abt_text.pack(padx=25, pady=(0, 20), anchor="w")
        self.app.accent_labels.append(self.lbl_abt_text)

        # --- ПРАВАЯ КАРТОЧКА (ДОНАТ) ---
        donate_card = ctk.CTkFrame(self.frame, corner_radius=DIMENSIONS["corner_radius"])
        donate_card.grid(row=1, column=1, padx=(10, DIMENSIONS["pad_window"]), pady=10, sticky="nsew")
        self.app.card_frames.append(donate_card)
        donate_card.grid_columnconfigure(0, weight=1)

        # Логика загрузки фото с поддержкой _internal
        try:
            img_path = resource_path("donate_img.jpg")
            if os.path.exists(img_path):
                pil_img = Image.open(img_path)
                orig_w, orig_h = pil_img.size

                target_width = 350
                ratio = target_width / orig_w
                target_height = int(orig_h * ratio)

                self.donate_img = ctk.CTkImage(light_image=pil_img,
                                              dark_image=pil_img,
                                              size=(target_width, target_height))

                self.lbl_img = ctk.CTkLabel(donate_card, image=self.donate_img, text="")
                self.lbl_img.grid(row=0, column=0, pady=(20, 15), sticky="n")
            else:
                print(f"DEBUG: File donate_img.jpg not found at {img_path}")
        except Exception as e:
            print(f"Error loading donate image: {e}")

        self.lbl_card_title_donate = ctk.CTkLabel(donate_card, text="", font=self.app.subtitle_font)
        self.lbl_card_title_donate.grid(row=1, column=0, padx=25, pady=(0, 10))
        self.app.accent_labels.append(self.lbl_card_title_donate)

        self.lbl_coffee_msg = ctk.CTkLabel(donate_card, text="", font=self.app.main_font, wraplength=350)
        self.lbl_coffee_msg.grid(row=2, column=0, padx=25, pady=(0, 25))

        self.btn_bmac = ctk.CTkButton(donate_card, text="", width=280,
                                 fg_color="#FF813F", hover_color="#E57338", text_color="#FFFFFF",
                                 command=lambda: webbrowser.open("https://buymeacoffee.com/serhiidev"),
                                 **self.app.get_btn_style())
        self.btn_bmac.grid(row=3, column=0, padx=25, pady=(0, 30))

    def update_texts(self):
        self.lbl_abt_title.configure(text=self.app.t("abt_title"))
        self.lbl_abt_text.configure(text=self.app.t("abt_text"))
        self.lbl_coffee_msg.configure(text=self.app.t("lbl_coffee_msg"))
        self.btn_bmac.configure(text=self.app.t("btn_bmac"))
        self.lbl_card_title_about.configure(text=self.app.t("card_title_about"))
        self.lbl_card_title_donate.configure(text=self.app.t("card_title_donate"))
