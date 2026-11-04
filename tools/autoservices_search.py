import requests
import json
import re
from bs4 import BeautifulSoup

def parse_olx_ad(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Основной источник — JSON-LD (Product/JobPosting), он есть на всех типах объявлений
        for block in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', response.text, re.S):
            try:
                data = json.loads(block)
            except ValueError:
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                description = item.get('description')
                if description:
                    return description

        # Фолбэк: текст в блоке ad_description, слово "Описание" — заголовок h3 внутри него
        soup = BeautifulSoup(response.text, 'html.parser')
        container = soup.find('div', attrs={'data-testid': 'ad_description'}) or soup.find('div', attrs={'data-cy': 'ad_description'})
        if container:
            text = container.get_text(' ', strip=True)
            text = text.removeprefix('Описание').strip()
            if text:
                return text
        return "Описание отсутствует"
    except Exception as e:
        print(f"Ошибка при получении описания объявления: {e}")
        return "Ошибка при получении описания"

def parse_olx():
    url = "https://www.olx.uz/list/q-%D0%B0%D0%B2%D1%82%D0%BE%D1%81%D0%B5%D1%80%D0%B2%D0%B8%D1%81/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        ads = soup.find_all('div', {'data-cy': 'l-card'})
        olx_results = []
        for ad in ads:
            try:
                title_elem = ad.find('h4') or ad.find('h6') or ad.find('div', class_='title')
                title = title_elem.get_text(strip=True) if title_elem else "Без названия"

                link_elem = ad.find('a')
                link = "https://www.olx.uz" + link_elem['href'] if link_elem and link_elem.get('href', '').startswith('/') else (link_elem['href'] if link_elem else 'Нет ссылки')

                # Получаем описание объявления
                description = "Описание отсутствует"
                if link != 'Нет ссылки':
                    description = parse_olx_ad(link)

                olx_results.append({
                    "title": title,
                    "url": link,
                    "description": description
                })
            except Exception as e:
                print(f"Ошибка при обработке объявления OLX: {e}")
                continue
        return olx_results
    except Exception as e:
        print(f"Ошибка при запросе к OLX: {e}")
        return []

def save_results(results, filename="olx_autoservices_data.json"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Результаты сохранены в {filename}")
    except Exception as e:
        print(f"Ошибка при сохранении результатов: {e}")

def main():
    olx_results = parse_olx()
    save_results(olx_results)

if __name__ == "__main__":
    main()
