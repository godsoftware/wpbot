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
        return re.sub(r'[^\x00-\x7FğüşıöçĞÜŞİÖÇ0-9a-zA-Z ()-]', '', text).strip()

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
        return df[['mağaza_adi', 'telefon']]  # Ensure correct column order

    def save_to_excel(self, filename):
        """Save DataFrame to Excel file with specific headers"""
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        with pd.ExcelWriter(f"{self.save_at}/{filename}.xlsx", engine='xlsxwriter') as writer:
            self.dataframe().to_excel(writer, index=False, header=['MAĞAZA ADI', 'TELEFON'])

def main():
    ########
    # Input
    ########
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-t", "--total", type=int)
    args = parser.parse_args()

    if args.search:
        search_list = [args.search]
    else:
        search_list = []
        input_file_name = 'input.txt'
        input_file_path = os.path.join(os.getcwd(), input_file_name)

        if os.path.exists(input_file_path):
            with open(input_file_path, 'r') as file:
                search_list = [line.strip() for line in file.readlines()]

        if len(search_list) == 0:
            print('Hata: -s argümanını girin veya input.txt dosyasına arama terimleri ekleyin.')
            sys.exit()

    total = args.total if args.total else 1_000_000

    ###########
    # Scraping
    ###########
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

            page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

            previously_counted = 0
            scroll_pause_time = 5
            max_attempts = 30
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
            business_list = BusinessList()

            for index, store in enumerate(listings):
                try:
                    store.scroll_into_view_if_needed()
                    store.click(timeout=10000)
                    page.wait_for_timeout(5000)

                    # Clean business name
                    try:
                        page.wait_for_selector('//h1[contains(@class, "DUwDvf")]', timeout=15000)
                        mağaza_adi = page.locator('//h1[contains(@class, "DUwDvf")]').inner_text()
                    except:
                        mağaza_adi = ""

                    # Clean phone number
                    try:
                        page.wait_for_selector('//button[contains(@data-item-id, "phone:tel:")]', timeout=15000)
                        telefon = page.locator('//button[contains(@data-item-id, "phone:tel:")]').inner_text()
                    except:
                        telefon = ""

                    business = Business(mağaza_adi=mağaza_adi, telefon=telefon)
                    business_list.business_list.append(business)

                    print(f"{index + 1}: {mağaza_adi} | {telefon}")

                except Exception as e:
                    print(f'Hata oluştu: {e}')

            filename = f"google_maps_data_{search_for}".replace(' ', '_')
            business_list.save_to_excel(filename)

        browser.close()

if __name__ == "__main__":
    main()
