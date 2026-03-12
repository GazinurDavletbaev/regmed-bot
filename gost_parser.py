import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import time

BASE_URL = "https://files.stroyinf.ru"
DOWNLOAD_DIR = "gost_pdfs"  # Папка для сохранения PDF

# Создаем папку для скачивания, если её нет
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_doc_links_from_list_page(list_url):
    """Собирает все ссылки на страницы документов с одной страницы каталога."""
    print(f"Обрабатываю страницу каталога: {list_url}")
    try:
        response = requests.get(list_url, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        doc_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/Index/'):
                full_url = urljoin(BASE_URL, href)
                doc_links.append(full_url)
        print(f"Найдено ссылок на документы: {len(doc_links)}")
        return doc_links
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке страницы {list_url}: {e}")
        return []

def get_doc_number_from_url(doc_url):
    """Извлекает номер документа из URL страницы."""
    # URL вида https://files.stroyinf.ru/Index/63/63467.htm
    # Нам нужно число перед .htm
    base = doc_url.split('/')[-1]  # берем последнюю часть URL
    doc_number = base.replace('.htm', '')
    return doc_number

def get_pdf_url(doc_number):
    """Формирует предполагаемый URL PDF по номеру документа."""
    # Папка формируется из первых цифр номера (например, 63467 -> 634)
    # Берем первые 3 цифры
    folder = doc_number[:3]
    return f"{BASE_URL}/Data/{folder}/{doc_number}.pdf"

def download_pdf(pdf_url, doc_number):
    """Скачивает PDF по указанному URL."""
    local_filename = os.path.join(DOWNLOAD_DIR, f"{doc_number}.pdf")
    
    # Проверяем, не скачан ли уже файл
    if os.path.exists(local_filename):
        print(f"Файл {doc_number}.pdf уже существует, пропускаю.")
        return True
    
    print(f"Пробую скачать: {pdf_url}")
    try:
        # Важно: stream=True для больших файлов
        response = requests.get(pdf_url, verify=False, stream=True)
        if response.status_code == 200:
            with open(local_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Успешно скачан: {doc_number}.pdf")
            return True
        else:
            print(f"❌ Ошибка {response.status_code} для {pdf_url}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при скачивании {pdf_url}: {e}")
        return False

if __name__ == "__main__":
    # Тестируем на известной странице каталога
    test_list_url = "https://files.stroyinf.ru/list/1-166.htm"
    doc_links = get_doc_links_from_list_page(test_list_url)
    
    if doc_links:
        print("\nПробуем скачать первые 5 документов:")
        # Берем первые 5 для теста
        for i, link in enumerate(doc_links[:5]):
            doc_number = get_doc_number_from_url(link)
            pdf_url = get_pdf_url(doc_number)
            print(f"\n{i+1}. Документ {doc_number}")
            download_pdf(pdf_url, doc_number)
            time.sleep(1)  # Пауза, чтобы не нагружать сервер
    else:
        print("Нет ссылок для обработки.")