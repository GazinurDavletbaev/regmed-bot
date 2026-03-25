import os
import re
import json
import requests
from pathlib import Path
import pdfplumber

# Конфигурация
DEEPSEEK_API_KEY = "sk-8532345d813c4b01aac9955dc2303548"  # замени на свой
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
GOST_PDFS = Path("C:/Users/user/gost_pdfs")
METADATA_FILE = GOST_PDFS / "metadata.json"

def extract_text_from_page(pdf_path, page_num=0):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num < len(pdf.pages):
                return pdf.pages[page_num].extract_text()
    except Exception as e:
        print(f"⚠️ Ошибка при чтении страницы {page_num+1} в {pdf_path}: {e}")
    return None

def ask_deepseek_for_metadata(text):
    prompt = f"""Ты — ассистент, который извлекает метаданные из текста первой страницы ГОСТа.
Верни только JSON без пояснений. Если какое-то поле не найдено, оставь пустую строку.

Извлеки:
- gost_number (полный номер, например "ГОСТ 31336-2006")
- title (полное название стандарта)
- year (год принятия, только число)
- status (действует / заменён, если понятно из текста)
- iso_reference (ISO-ссылка, например "ИСО 2151:2004")

Текст страницы:
{text}
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты — помощник для извлечения метаданных из ГОСТов. Отвечай только JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            content = content[start:end]
        return json.loads(content)
    except Exception as e:
        print(f"❌ Ошибка при запросе к DeepSeek: {e}")
        return None

def get_unique_filename(folder, base_name):
    path = folder / base_name
    if not path.exists():
        return path
    stem = path.stem
    ext = path.suffix
    counter = 1
    while True:
        new_name = f"{stem} ({counter}){ext}"
        new_path = folder / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def load_existing_metadata():
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_metadata(metadata_dict):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata_dict, f, ensure_ascii=False, indent=2)

def process_pdf(pdf_path, all_metadata):
    print(f"\n📄 Обрабатываю: {pdf_path.name}")
    
    text = extract_text_from_page(pdf_path, 0)
    if not text:
        text = extract_text_from_page(pdf_path, 1)
        if not text:
            print("❌ Не удалось извлечь текст с первых двух страниц")
            return False
    
    print("📜 Текст первой страницы (первые 500 символов):")
    print(text[:500])
    print("-" * 50)
    
    metadata = ask_deepseek_for_metadata(text)
    if not metadata:
        return False
    
    metadata["original_file"] = pdf_path.name
    
    gost_number = metadata.get("gost_number", "").strip()
    if gost_number:
        all_metadata[gost_number] = metadata
    else:
        all_metadata[pdf_path.name] = metadata
    
    if gost_number:
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', gost_number)
        new_pdf_name = f"{safe_name}.pdf"
        new_pdf_path = get_unique_filename(pdf_path.parent, new_pdf_name)
        pdf_path.rename(new_pdf_path)
        print(f"✅ PDF переименован в {new_pdf_path.name}")
    else:
        print("⚠️ Номер ГОСТа не найден, PDF не переименован")
    
    return True

def main():
    # Берём только первые 3 PDF
    pdf_files = sorted(GOST_PDFS.glob("*.pdf"))[:3]
    print(f"Найдено PDF для обработки: {len(pdf_files)}")
    
    all_metadata = load_existing_metadata()
    
    for pdf in pdf_files:
        process_pdf(pdf, all_metadata)
    
    save_metadata(all_metadata)
    print(f"\n✅ Метаданные сохранены в {METADATA_FILE}")

if __name__ == "__main__":
    main()