import pandas as pd
import time
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.keys import Keys

# Excel dosyası
excel_path = r"C:\PycharmProjects\whatsappbot\output\cleaned_data.xlsx"
df = pd.read_excel(excel_path)

# Gönderilecek mesaj (URL encode edilir)
message = "Merhaba, mağazanız hakkında bilgi almak istiyorum."
encoded_message = quote(message)

#  Edge profili ayarları
options = Options()
options.add_argument("user-data-dir=C:\\Users\\ozkal.DESKTOP-8UHA164\\EdgeBotProfile")
options.add_argument("profile-directory=Profile 1")
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

#  WebDriver başlat
driver = webdriver.Edge(options=options)

# WhatsApp Web'e git
driver.get("https://web.whatsapp.com")
print("Tarayıcı açıldı. QR çıkmıyorsa profil doğru bağlandı.")
time.sleep(10)

print("\n WhatsApp Web tarayıcıda açık olmalı ve oturum açık olmalıdır.\n")

#  Her kişi için bekleme süresi (sayfa yüklenme + mesaj gönderme)
wait_time = 15

#  Her satır için bağlantıyı sırayla aç
for index, row in df.iterrows():
    raw_number = str(row["TELEFON"])
    name = row.get("MAĞAZA ADI", "Mağaza")

    #  Numara sadece rakam olacak şekilde temizlenir
    digits = ''.join(filter(str.isdigit, raw_number))
    if digits.startswith("0"):
        digits = digits[1:]
    number = f"90{digits}"  # Türkiye için ülke kodu

    #  WhatsApp Web bağlantısı
    url = f"https://web.whatsapp.com/send?phone={number}&text={encoded_message}"

    print(f"\n➡ {index+1}. {name} ({number})")
    print(f" Açılıyor: {url}")
    driver.get(url)

    print(f" {wait_time} saniye bekleniyor ve ENTER gönderilecek...")
    time.sleep(wait_time)

    # ⌨ ENTER tuşuna otomatik bas
    try:
        message_box = driver.switch_to.active_element
        message_box.send_keys(Keys.ENTER)
    except Exception as e:
        print("⚠️ ENTER tuşu gönderilirken hata oluştu:", e)

    #  Mesaj gönderildikten sonra 3 saniye bekle
    time.sleep(3)

print("\n Tüm mesajlar otomatik olarak gönderildi.")
