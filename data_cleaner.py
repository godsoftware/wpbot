import pandas as pd
from datetime import datetime
import os

# Excel dosyasını yükleyin
def load_existing_data(filepath):
    if os.path.exists(filepath):
        return pd.read_excel(filepath)
    else:
        return pd.DataFrame(columns=['MAĞAZA ADI', 'TELEFON', 'EKLENME TARİHİ'])

# Büyük mağaza adları (Ulusal Markalar)
big_brands = [
    "Arçelik", "Beko", "Vestel", "Bosch", "Siemens", "Profilo",
    "Samsung", "LG", "Grundig", "Regal", "Altus", "Sunny", "Simfer",
    "Fantom", "Uğur", "Teka", "Silverline", "Miele", "Philips",
    "Rowenta", "Arnica", "Korkmaz", "Karaca",
     "Bauhaus","Hepsiburada", "Trendyol", "CarrefourSA", "Metro Market", "A101",
    "BİM", "ŞOK"
]

# Hariç tutulacak ikinci el kelimeler
exclude_keywords = ["spot", "2.el", "ikinci el", "spotçu", "eski eşya"]

def filter_data(df):
    df = df.dropna(subset=['MAĞAZA ADI', 'TELEFON'])
    df = df[~df['MAĞAZA ADI'].str.contains('|'.join(big_brands), case=False, na=False)]
    df = df[~df['MAĞAZA ADI'].str.contains('|'.join(exclude_keywords), case=False, na=False)]
    df = df.drop_duplicates()
    return df

def update_existing_data(existing_df, new_df):
    # Sadece daha önce olmayanları ekle
    combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['MAĞAZA ADI', 'TELEFON'], keep='first')
    return combined_df

# Dosya yolları
input_file = r'C:\PycharmProjects\whatsappbot\output\cleaned_data.xlsx'
output_file = r'C:\PycharmProjects\whatsappbot\output\cleaned_data.xlsx'

# Verileri yükle
existing_data = load_existing_data(output_file)
new_data = pd.read_excel(input_file)

# Veriyi filtrele
filtered_data = filter_data(new_data)

# EKLENME TARİHİ sütunu ekle
filtered_data['EKLENME TARİHİ'] = datetime.now().strftime('%Y-%m-%d')

# Mevcut veriyle birleştir
final_data = update_existing_data(existing_data, filtered_data)

# Sonuçları kaydet
final_data.to_excel(output_file, index=False)

print(f"✔ Veri başarıyla temizlendi, yeni veriler eklendi ve '{output_file}' olarak kaydedildi.")
