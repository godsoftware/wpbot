import pandas as pd
import time
from urllib.parse import quote
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.keys import Keys

# Dosya yolları
cevaplar_path = r"C:\PycharmProjects\whatsappbot\wpbot\gemini_mesaj_cevaplari.xlsx"
orijinal_path = r"C:\PycharmProjects\whatsappbot\wpbot\whatsapp_mesajlar.xlsx"

# Excel dosyalarını oku
cevaplar_df = pd.read_excel(cevaplar_path)
orijinal_df = pd.read_excel(orijinal_path)

# 🛡️ 'Durum' sütunu yoksa oluştur
if 'Durum' not in cevaplar_df.columns:
    cevaplar_df['Durum'] = ''

# 🔍 Gönderilmeyen mesajları filtrele
bekleyenler = cevaplar_df[cevaplar_df['Durum'] != 'Gönderildi'].copy()


# Edge profili ayarları
options = Options()
options.add_argument("user-data-dir=C:\\Users\\ozkal.DESKTOP-8UHA164\\EdgeBotProfile")
options.add_argument("profile-directory=Profile 1")
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# WebDriver başlat
driver = webdriver.Edge(options=options)
driver.get("https://web.whatsapp.com")
print("Tarayıcı açıldı. QR çıkmıyorsa profil doğru bağlandı.")
time.sleep(10)

wait_time = 15  # her kişi için bekleme süresi

for index, row in bekleyenler.iterrows():
    numara_raw = row["Numara"]
    mesaj = row["Gemini_Cevap"]
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Numara temizlenir
    digits = ''.join(filter(str.isdigit, numara_raw))
    if digits.startswith("0"):
        digits = digits[1:]
    number = f"{digits}"  # Türkiye için ülke kodu

    # Mesaj URL encode edilir
    encoded_message = quote(mesaj)

    # WhatsApp bağlantısı hazırlanır
    url = f"https://web.whatsapp.com/send?phone={number}&text={encoded_message}"
    print(f"\n➡ {index+1}. {numara_raw}")
    print(f" Açılıyor: {url}")
    driver.get(url)

    print(f" {wait_time} saniye bekleniyor ve ENTER gönderilecek...")
    time.sleep(wait_time)

    try:
        message_box = driver.switch_to.active_element
        message_box.send_keys(Keys.ENTER)
    except Exception as e:
        print("⚠️ ENTER tuşu gönderilirken hata oluştu:", e)

    time.sleep(3)

    # 1. Cevaplar dosyasında "Gönderildi" olarak işaretle
    cevaplar_df.at[index, 'Durum'] = 'Gönderildi'

    # 2. Numaranın altına yeni satır olarak AI cevabı ekle
    ilgili_kisim = orijinal_df[orijinal_df['Numara'] == numara_raw]
    if not ilgili_kisim.empty:
        son_index = ilgili_kisim.index[-1] + 1
    else:
        son_index = len(orijinal_df)

    yeni_satir = {
        'Sohbet No': '',
        'Numara': numara_raw,
        'Tarih': now,
        'Gönderen': 'AI CUSTOMER',
        'Mesaj': mesaj,
        'Son Kontrol': ''
    }

    ust = orijinal_df.iloc[:son_index]
    alt = orijinal_df.iloc[son_index:]
    orijinal_df = pd.concat([ust, pd.DataFrame([yeni_satir]), alt], ignore_index=True)

# 🔄 Dosyaları aynı isimle üzerine kaydet
cevaplar_df.to_excel(cevaplar_path, index=False)
orijinal_df.to_excel(orijinal_path, index=False)

driver.quit()
print("\n🎉 Tüm mesajlar gönderildi ve dosyalar güncellendi.")
