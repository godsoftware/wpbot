from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys
import re
from datetime import datetime

@dataclass
class Business:
    name: str = None
    type: str = None
    rating: int = None
    reviews: int = None
    address: str = None
    phone: str = None
    website: str = None
    wp_status: str = None  # Şu anda boş geçeceğiz.



@dataclass
class BusinessList:
    business_list: list[Business] = field(default_factory=list)
    save_at = 'output'

    def clean_text(self, text):
        return re.sub(r'[^\x00-\x7FğüıöçşĞÜŞİÖÇ0-9a-zA-Z ()-]', '', text).strip() if text else ""

    def dataframe(self):
        cleaned_data = [
            {
                'Name': self.clean_text(business.name),
                'Type': self.clean_text(business.type),
                'Rating': self.clean_text(business.rating),
                'Reviews': self.clean_text(business.reviews),
                'Address': self.clean_text(business.address),
                'Phone': self.clean_text(business.phone),
                'Website': self.clean_text(business.website),
                'WP Status': self.clean_text(business.wp_status),
            }
            for business in self.business_list
        ]
        df = pd.DataFrame(cleaned_data)
        return df[['Name', 'Type', 'Rating', 'Reviews', 'Address', 'Phone', 'Website', 'WP Status']]

    def save_to_excel(self, filename):
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)

        file_path = os.path.join(self.save_at, f"{filename}.xlsx")
        new_df = self.dataframe()

        # Tarih sütunu ekle
        today = datetime.now().strftime("%Y-%m-%d")
        new_df["Eklenme Tarihi"] = today

        try:
            if os.path.exists(file_path):
                existing_df = pd.read_excel(file_path)

                # Beklenen başlıklar (tarihi de dahil ediyoruz)
                expected_columns = ['Name', 'Type', 'Rating', 'Reviews', 'Address', 'Phone', 'Website', 'WP Status', 'Eklenme Tarihi']
                for col in expected_columns:
                    if col not in existing_df.columns:
                        print(f"UYARI: '{col}' sütunu mevcut değil, eski dosya yapısı bozuk olabilir. Yeniden oluşturulacak.")
                        combined_df = new_df
                        break
                else:
                    # Yinelenen kayıtları kontrol et (Name + Phone)
                    existing_keys = set(zip(existing_df["Name"], existing_df["Phone"]))
                    unique_rows = [
                        row for i, row in new_df.iterrows()
                        if (row["Name"], row["Phone"]) not in existing_keys
                    ]

                    if unique_rows:
                        new_unique_df = pd.DataFrame(unique_rows)
                        combined_df = pd.concat([existing_df, new_unique_df], ignore_index=True)
                        print(f"➕ {len(new_unique_df)} yeni kayıt eklendi.")
                    else:
                        print("ℹ️ Hiç yeni kayıt bulunamadı.")
                        combined_df = existing_df
            else:
                combined_df = new_df
                print(f"📄 Yeni dosya oluşturuluyor: {file_path}")

            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                combined_df.to_excel(writer, index=False)

            print(f"✔ Veriler başarıyla kaydedildi: {file_path}")

        except Exception as e:
            print(f" Hata oluştu: {e}")



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--total", type=int)
    args = parser.parse_args()

    input_file_name = 'input.txt'
    input_file_path = os.path.join(os.getcwd(), input_file_name)

    if os.path.exists(input_file_path):
        with open(input_file_path, 'r', encoding='utf-8') as file:
            search_list = [line.strip() for line in file.readlines()]
    else:
        print('Hata: input.txt dosyasına ilçe isimlerini ekleyin.')
        sys.exit()

    total = args.total if args.total else 1_000_000

    combined_business_list = BusinessList()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://www.google.com/maps", timeout=60000)
        page.wait_for_timeout(5000)

        for search_for_index, search_for in enumerate(search_list):
            print(f"-----\n{search_for_index} - {search_for}".strip())

            page.locator('//input[@id="searchboxinput"]').fill(search_for)
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

            try:
                page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]', timeout=15000)
                page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')
            except:
                print(f"{search_for} için sonuç bulunamadı veya yüklenmedi.")
                continue

            previously_counted = 0
            scroll_pause_time = 5
            max_attempts = 5
            attempts = 0

            while True:
                page.mouse.wheel(0, 5000)
                page.wait_for_timeout(scroll_pause_time * 1000)

                current_count = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
                print(f"Aktif Sonuç Sayısı: {current_count}")

                if current_count == previously_counted:
                    attempts += 1
                else:
                    attempts = 0

                if attempts >= max_attempts or current_count >= total:
                    break

                previously_counted = current_count

            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total]
            listings = [listing.locator("xpath=..") for listing in listings]

            print(f"Toplam Mağaza Sayısı: {len(listings)}")

            previous_name = None

            for index, store in enumerate(listings):
                try:
                    store.scroll_into_view_if_needed()
                    store.click(timeout=10000)
                    page.wait_for_timeout(2000)

                    # Mağaza adı al ve öncekiyle karşılaştır
                    name_locator = page.locator('//h1[contains(@class, "DUwDvf")]')
                    name = name_locator.first.inner_text() if name_locator.count() > 0 else ""

                    if name == previous_name or name == "":
                        print(f"{index + 1}. mağaza atlandı (aynı içerik veya boş ad)")
                        continue

                    previous_name = name  # Sonraki kontrol için güncelle

                    # TYPE (kategori)
                    try:
                        type_locator = page.locator('button.DkEaL')
                        type_ = type_locator.first.inner_text() if type_locator.count() > 0 else ""
                    except:
                        type_ = ""

                    # Rating (puan)
                    try:
                        rating_locator = page.locator('div.F7nice span[aria-hidden="true"]')
                        rating = rating_locator.first.inner_text() if rating_locator.count() > 0 else ""
                    except:
                        rating = ""

                    # Reviews (yorum sayısı)
                    try:
                        reviews = ""
                        spans = page.locator('div.F7nice span')
                        for i in range(spans.count()):
                            text = spans.nth(i).inner_text()
                            if "(" in text and ")" in text:
                                reviews = ''.join(filter(str.isdigit, text))
                                break
                    except:
                        reviews = ""

                    # Address
                    try:
                        address_locator = page.locator('//button[@data-item-id="address"]')
                        address = address_locator.first.inner_text() if address_locator.count() > 0 else ""
                    except:
                        address = ""

                    # Phone
                    try:
                        phone_locator = page.locator('//button[contains(@data-item-id, "phone:tel:")]')
                        phone = phone_locator.first.inner_text() if phone_locator.count() > 0 else ""
                    except:
                        phone = ""

                    # Website
                    try:
                        website_locator = page.locator('//a[contains(@data-item-id, "authority")]')
                        website = website_locator.first.inner_text() if website_locator.count() > 0 else ""
                    except:
                        website = ""

                    # WhatsApp bilgisi şimdilik boş
                    wp_status = ""

                    # Business nesnesi oluştur ve listeye ekle
                    business = Business(
                        name=name,
                        type=type_,
                        rating=rating,
                        reviews=reviews,
                        address=address,
                        phone=phone,
                        website=website,
                        wp_status=wp_status
                    )
                    combined_business_list.business_list.append(business)

                    print(f"{index + 1}: {name} | {type_} | {rating} | {reviews} | {address} | {phone} | {website}")

                except Exception as e:
                    print(f"{index + 1}. mağazada hata oluştu: {e}")

        combined_business_list.save_to_excel('google_maps_combined_data')

        browser.close()

if __name__ == "__main__":
    main()
