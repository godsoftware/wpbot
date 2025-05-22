import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import subprocess
import threading
from tkinter import ttk
import pandas as pd

class BotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Bot Kontrol Paneli")
        self.root.geometry("800x750")

        # Veri sayısı girişi
        tk.Label(root, text="Kaç adet veri çekilsin?").pack(pady=5)
        self.entry = tk.Entry(root, width=10)
        self.entry.pack()

        # input.txt düzenleme kutusu
        tk.Label(root, text="input.txt düzenle:").pack(pady=5)
        self.input_text = scrolledtext.ScrolledText(root, width=95, height=10)
        self.input_text.pack(padx=10, pady=5)
        self.load_input_file()

        # Kaydet Butonu
        self.save_button = tk.Button(root, text="input.txt Kaydet", command=self.save_input_file)
        self.save_button.pack(pady=5)

        # Başlat Butonu
        self.start_button = tk.Button(root, text="START", command=self.run_bot)
        self.start_button.pack(pady=10)

        # Durum Alanı
        self.status_area = scrolledtext.ScrolledText(root, width=95, height=20)
        self.status_area.pack(padx=10, pady=10)

    def load_input_file(self):
        try:
            with open("input.txt", "r", encoding="utf-8") as f:
                content = f.read()
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert(tk.END, content)
        except FileNotFoundError:
            self.input_text.insert(tk.END, "")

    def save_input_file(self):
        content = self.input_text.get("1.0", tk.END)
        try:
            with open("input.txt", "w", encoding="utf-8") as f:
                f.write(content.strip())
            messagebox.showinfo("Başarılı", "input.txt kaydedildi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya kaydedilemedi: {e}")

    def show_responses(self):
        self.response_area.delete("1.0", tk.END)
        try:
            df = pd.read_excel("gemini_mesaj_cevaplari.xlsx", engine="openpyxl")
            if 'Numara' in df.columns and 'Mesaj' in df.columns:
                for index, row in df.iterrows():
                    self.response_area.insert(tk.END, f"📱 {row['Numara']}\n")
                    self.response_area.insert(tk.END, f"📝 {row['Mesaj']}\n")
                    self.response_area.insert(tk.END, "-"*60 + "\n")
            else:
                self.response_area.insert(tk.END, "Dosyada 'Numara' ve 'Mesaj' sütunları yok.")
        except FileNotFoundError:
            self.response_area.insert(tk.END, "gemini_mesaj_cevaplari.xlsx dosyası bulunamadı.")
        except Exception as e:
            self.response_area.insert(tk.END, f"Hata: {e}")

    def log(self, message):
        self.status_area.insert(tk.END, message + "\n")
        self.status_area.see(tk.END)
        self.root.update()

    def run_bot(self):
        try:
            self.count = int(self.entry.get())
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli bir sayı girin!")
            return
        thread = threading.Thread(target=self._run_bot_steps)
        thread.start()

    def _run_bot_steps(self):
        steps = [
            (f"[1] Web Scraper Başlatılıyor - {self.count} veri",
             ["python", "map_scraper_main.py", "-t", str(self.count)]),
            ("[2] Veri Temizleme Başlatılıyor", ["python", "data_cleaner.py"]),
            ("[3] Mesaj Gönderiliyor", ["python", "sending_message.py"]),
            ("[4] Yanıt Alınıyor", ["python", "recieve_message.py"]),
            ("[5] AI Kontrolü Yapılıyor", ["python", "checking_aı_apı.py"]),
        ]

        for desc, cmd in steps:
            self.log(desc)
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
                self.log(result.stdout if result.stdout else "[stdout boş]")
                if result.stderr:
                    self.log("[!] Hata: " + result.stderr)
            except Exception as e:
                self.log(f"[!] Komut çalıştırılamadı: {e}")

        self.log("[✓] Tüm işlemler tamamlandı.")

# Uygulama başlatılıyor
if __name__ == "__main__":
    root = tk.Tk()
    app = BotApp(root)
    root.mainloop()
