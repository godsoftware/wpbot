import pandas as pd
import requests
import json

# Excel dosyanı oku
df = pd.read_excel("whatsapp_mesajlar.xlsx")

#gruplandır
gruplar = df.groupby("Numara")


GEMINI_API_KEY = 'AIzaSyC24GhG3lt71z0K7RJpzYD82ftl11ROskU'

# Gemini API URL
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# Tüm sonuçları saklamak için liste
tum_sonuclar = []

# Her numara için mesajları hazırla ve Gemini'ye gönder
for numara, mesajlar in gruplar:
    prompt = "Aşağıdaki müşteri mesajlarını, profesyonel bir müşteri hizmetleri temsilcisi olarak Türkçe cevapla:\n\n"

    # Mesajların tamamını prompta ekle ve ekrana yazdır
    print(f"\n{'=' * 60}\n Numara: {numara}\n{'=' * 60}")
    for idx, row in mesajlar.iterrows():
        tarih = row['Tarih']
        mesaj = row['Mesaj']
        prompt += f"Müşteri ({tarih}): {mesaj}\n"
        print(f"Müşteri ({tarih}): {mesaj}")

    prompt += "\nMüşteri Temsilcisi:"

    # Gemini API'ye gönderilecek veri
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    # Gemini API çağrısı yap
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # API'den dönen yanıtı kontrol et
    if response.status_code == 200:
        cevap = response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        cevap = f"Hata: {response.status_code}, Detay: {response.text}"

    # Gemini cevabını ekrana yazdır
    print(f"\n Müşteri Temsilcisi Yanıtı:\n{cevap}\n{'-' * 60}")

    # Sonuçları kaydet
    tum_sonuclar.append({
        'Numara': numara,
        'Mesajlar': mesajlar['Mesaj'].tolist(),
        'Gemini_Cevap': cevap
    })

# Sonuçları Excel'e kaydet
sonuclar_df = pd.DataFrame(tum_sonuclar)
sonuclar_df.to_excel("gemini_mesaj_cevaplari.xlsx", index=False)
