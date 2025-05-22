import customtkinter as ctk
import tkinter.messagebox as mbox
import pandas as pd
import subprocess
import threading
import os

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class BotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI WhatsApp Bot")
        self.geometry("900x650")
        self.resizable(False, False)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.input_tab = self.tabview.add("Girdi ve Başlat")
        self.response_tab = self.tabview.add(" AI Cevapları")

        self.build_input_tab()
        self.build_response_tab()

    # ==== Sekme 1: Bot Başlatma ====
    def build_input_tab(self):
        ctk.CTkLabel(self.input_tab, text="Kaç adet veri çekilsin?").pack(pady=(10, 0))
        self.entry_count = ctk.CTkEntry(self.input_tab, width=100)
        self.entry_count.insert(0, "10")
        self.entry_count.pack()

        ctk.CTkLabel(self.input_tab, text="input.txt düzenle:").pack(pady=(20, 5))
        self.input_textbox = ctk.CTkTextbox(self.input_tab, width=800, height=200)
        self.input_textbox.pack(padx=10)
        self.load_input_txt()

        ctk.CTkButton(self.input_tab, text=" input.txt Kaydet", command=self.save_input_txt).pack(pady=5)
        ctk.CTkButton(self.input_tab, text=" Botu Başlat", command=self.run_bot_thread).pack(pady=10)

        self.output_box = ctk.CTkTextbox(self.input_tab, width=800, height=200)
        self.output_box.pack(padx=10, pady=10)

    def load_input_txt(self):
        if os.path.exists("input.txt"):
            with open("input.txt", "r", encoding="utf-8") as f:
                self.input_textbox.delete("0.0", "end")
                self.input_textbox.insert("0.0", f.read())

    def save_input_txt(self):
        content = self.input_textbox.get("0.0", "end").strip()
        try:
            with open("input.txt", "w", encoding="utf-8") as f:
                f.write(content)
            mbox.showinfo("Başarılı", "input.txt kaydedildi.")
        except Exception as e:
            mbox.showerror("Hata", str(e))

    def run_bot_thread(self):
        t = threading.Thread(target=self.run_bot_steps)
        t.start()

    def log(self, text):
        self.output_box.insert("end", text + "\n")
        self.output_box.see("end")

    def run_bot_steps(self):
        try:
            count = int(self.entry_count.get())
        except ValueError:
            mbox.showerror("Hata", "Lütfen geçerli bir sayı girin.")
            return

        steps = [
            ("Web Scraper", ["python", "map_scraper_main.py", "-t", str(count)]),
            ("Data Cleaner", ["python", "data_cleaner.py"]),
            ("Mesaj Gönder", ["python", "sending_message.py"]),
            ("Mesaj Al", ["python", "recieve_message.py"]),
            ("AI Kontrol", ["python", "checking_aı_apı.py"])
        ]

        for desc, cmd in steps:
            self.log(f"[{desc}] çalıştırılıyor...")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
                self.log(result.stdout.strip() or "[stdout boş]")
                if result.stderr:
                    self.log(f"[!] Hata: {result.stderr.strip()}")
            except Exception as e:
                self.log(f"[!] Komut hatası: {e}")

        self.log("[✓] Tüm adımlar tamamlandı.")
        self.show_responses()

    # ==== Sekme 2: Cevapları Göster ====
    def build_response_tab(self):
        self.response_frame = ctk.CTkScrollableFrame(self.response_tab, width=850, height=500)
        self.response_frame.pack(pady=20)

        self.refresh_btn = ctk.CTkButton(self.response_tab, text="🔄 Yenile", command=self.show_responses)
        self.refresh_btn.pack()

    def show_responses(self):
        for widget in self.response_frame.winfo_children():
            widget.destroy()

        path = "gemini_mesaj_cevaplari.xlsx"
        if not os.path.exists(path):
            ctk.CTkLabel(self.response_frame, text="Dosya bulunamadı.").pack()
            return

        try:
            df = pd.read_excel(path, engine="openpyxl")
            if "Numara" not in df.columns or "Mesaj" not in df.columns:
                ctk.CTkLabel(self.response_frame, text="Excel formatı hatalı.").pack()
                return

            grouped = df.groupby("Numara")
            for numara, group in grouped:
                ctk.CTkLabel(self.response_frame, text=f"📱 {numara}", font=("Arial", 16, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
                for _, row in group.iterrows():
                    kart = ctk.CTkFrame(self.response_frame, fg_color="#f1f3f5", corner_radius=10)
                    kart.pack(padx=20, pady=5, fill="x")
                    ctk.CTkLabel(kart, text=row["Mesaj"], wraplength=800, justify="left").pack(padx=10, pady=10)
        except Exception as e:
            ctk.CTkLabel(self.response_frame, text=f"Hata: {e}").pack()


if __name__ == "__main__":
    app = BotApp()
    app.mainloop()
