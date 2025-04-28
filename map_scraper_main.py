from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys
import re

@dataclass
class Business:
    """Stores business data"""
    mağaza_adi: str = None
    telefon: str = None

@dataclass
class BusinessList:
    """Holds the list of Business objects and saves to Excel"""
    business_list: list[Business] = field(default_factory=list)
    save_at = 'output'

    def clean_text(self, text):
        """Remove special characters and unnecessary whitespace"""
        return re.sub(r'[^\x00-\x7FğüıöçşĞÜŞİÖÇ0-9a-zA-Z ()-]', '', text).strip()

    def dataframe(self):
        """Convert business_list to pandas DataFrame with correct column order"""
        cleaned_data = [
            {
                'mağaza_adi': self.clean_text(business.mağaza_adi),
                'telefon': self.clean_text(business.telefon)
            }
            for business in self.business_list
        ]
        df = pd.DataFrame(cleaned_data)
        return df[['mağaza_adi', 'telefon']]

    def save_to_excel(self, filename):
        """Append to existing Excel file or create it if it doesn't exist"""
        # 1. Klasörü oluştur
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)

        file_path = os.path.join(self.save_at, f"{filename}.xlsx")
        new_df = self.dataframe()

        try:
            # 2. Dosya varsa oku ve verileri birleştir
            if os.path.exists(file_path):
                existing_df = pd.read_excel(file_path)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                combined_df = new_df

            # 3. Dosyayı yaz
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                combined_df.to_excel(writer, index=False, header=['MAĞAZA ADI', 'TELEFON'])

            print(f"✔ Veriler başarıyla kaydedildi: {file_path}")

        except Exception as e:
            print(f"Hata oluştu: {e}")


def main():
    ########
    # Input
    ########
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

    ###########
    # Scraping
    ###########
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

            for index, store in enumerate(listings):
                try:
                    store.scroll_into_view_if_needed()
                    store.click(timeout=10000)
                    page.wait_for_timeout(5000)

                    try:
                        page.wait_for_selector('//h1[contains(@class, "DUwDvf")]', timeout=15000)
                        mağaza_adi = page.locator('//h1[contains(@class, "DUwDvf")]').inner_text()
                    except:
                        mağaza_adi = ""

                    try:
                        page.wait_for_selector('//button[contains(@data-item-id, "phone:tel:")]', timeout=15000)
                        telefon = page.locator('//button[contains(@data-item-id, "phone:tel:")]').inner_text()
                    except:
                        telefon = ""

                    business = Business(mağaza_adi=mağaza_adi, telefon=telefon)
                    combined_business_list.business_list.append(business)

                    print(f"{index + 1}: {mağaza_adi} | {telefon}")

                except Exception as e:
                    print(f'Hata oluştu: {e}')

        combined_business_list.save_to_excel('google_maps_combined_data')

        browser.close()

if __name__ == "__main__":
    main()
