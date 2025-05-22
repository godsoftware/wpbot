import pandas as pd
import ollama

# Excel dosyasını oku
df = pd.read_excel(r"C:\PycharmProjects\whatsappbot\wpbot\whatsapp_mesajlar.xlsx")

# Telefon numarasına göre mesajları grupla
gruplar = df.groupby("Numara")

# Ollama istemcisini başlat (Llama3.2 için)
client = ollama.Client(host='http://localhost:11434')

# Sonuçları saklayacağın liste
sonuclar = []

for numara, mesajlar in gruplar:
    prompt = "Aşağıdaki mesajları müşteri temsilcisi olarak yanıtlayın.\n\n"

    # Tüm mesajları tam olarak ekleyelim ve yazdıralım
    print(f"\n{'='*60}\n📞 Numara: {numara}\n{'='*60}")

    for idx, row in mesajlar.iterrows():
        tarih = row['Tarih']
        mesaj = row['Mesaj']
        print(f"Müşteri ({tarih}): {mesaj}")  # Tam çıktı olarak ekrana yaz
        prompt += f"Müşteri ({tarih}): {mesaj}\n"

    prompt += "\nMüşteri Temsilcisi:"

    # Ollama üzerinden cevap al
    response = client.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        options={'temperature': 0.5}
    )

    cevap = response['message']['content']

    # Modelin cevabını ekrana yazdır
    print(f"\n🤖 Müşteri Temsilcisi Yanıtı:\n{cevap}\n{'-'*60}")

    # İstersen sonuçları listede sakla (sonradan dosyaya yazdırmak için)
    sonuclar.append({
        'Numara': numara,
        'Mesajlar': mesajlar['Mesaj'].tolist(),
        'Model_Cevabi': cevap
    })

# Sonuçları yeni bir Excel dosyasına kaydet (opsiyonel)
sonuc_df = pd.DataFrame(sonuclar)
sonuc_df.to_excel("mesaj_model_cevaplari.xlsx", index=False)
