import subprocess
import argparse

def run_script(script_name, limit):
    """Verilen Python dosyasını çalıştırır."""
    try:
        subprocess.run(["python", script_name, "-t", str(limit)], check=True)
        print(f"{script_name} başarıyla çalıştırıldı.")
    except subprocess.CalledProcessError as e:
        print(f"{script_name} çalıştırılırken hata oluştu: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Python Bot')
    parser.add_argument('-t', '--total', type=int, required=True, help='Her konum için maksimum mağaza sayısı limiti')
    args = parser.parse_args()

    # Önce veri çekme kodu çalışacak
    run_script("map_scraper_main.py", args.total)

    # Sonrasında temizleme kodu çalışacak
    run_script("data_cleaner.py", args.total)
