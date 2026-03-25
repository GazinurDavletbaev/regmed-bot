import os
import re
import sys
import argparse
from pathlib import Path
import pdfplumber

def extract_text_from_page(pdf_path, page_num=0):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                return page.extract_text()
    except Exception as e:
        print(f"⚠️ Ошибка при чтении страницы {page_num+1} в {pdf_path}: {e}")
    return None

def find_gost_line_and_context(text):
    if not text:
        return None, None, None
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'ГОСТ' in line:
            context = lines[i+1:i+8]
            return i, line, context
    return None, None, None

def extract_gost_number_from_context(gost_line, context):
    iso_part = None
    for line in context:
        iso_match = re.search(r'\([ИСОA-Z]+\s*([\d\.:-]+)\)', line, re.IGNORECASE)
        if iso_match:
            iso_part = iso_match.group(1)
            break
    
    # ETSI EN 301 489-24 — 2022
    for i, line in enumerate(context[:5]):
        if 'ETSI EN' in line:
            match = re.search(r'ETSI\s+EN\s+(\d+)\s+(\d+)-(\d+)[–—-]', line, re.IGNORECASE)
            if match:
                num = f"{match.group(1)} {match.group(2)}-{match.group(3)}"
                for next_line in context[i+1:i+4]:
                    year_match = re.search(r'(\d{4})', next_line)
                    if year_match:
                        return num, year_match.group(1), iso_part
                return num, None, iso_part
    
    # 60811 2 1 — 2006
    for line in context[:5]:
        match = re.search(r'(\d+)\s+(\d+)\s+(\d+)', line)
        if match:
            num = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            for next_line in context:
                year_match = re.search(r'(\d{4})', next_line)
                if year_match:
                    return num, year_match.group(1), iso_part
            return num, None, iso_part
    
    # OIML R 111-2 — 2014
    for i, line in enumerate(context[:5]):
        if 'OIML' in line:
            match = re.search(r'OIML\s*R?\s*(\d+)\s*-(\d+)[–—-]', line, re.IGNORECASE)
            if match:
                num = f"R {match.group(1)}-{match.group(2)}"
                for next_line in context[i+1:i+4]:
                    year_match = re.search(r'(\d{4})', next_line)
                    if year_match:
                        return num, year_match.group(1), iso_part
                return num, None, iso_part
    
    # ISO Guide 30 — 2019
    for i, line in enumerate([gost_line] + context[:5]):
        if 'ISO Guide' in line:
            num = re.search(r'ISO Guide\s*(\d+)', line, re.IGNORECASE)
            if num:
                for n in [gost_line] + context[i+1:i+4]:
                    y = re.search(r'(\d{4})', n)
                    if y:
                        return f"ISO Guide {num.group(1)}", y.group(1), iso_part
                return f"ISO Guide {num.group(1)}", None, iso_part
    
    # Обычный номер с точками и годом
    combined = gost_line + ' ' + ' '.join(context[:8])
    combined = re.sub(r'\s+', ' ', combined)
    match = re.search(r'(\d+(?:\.\d+)+)[–—-](\d{2,4})', combined)
    if match:
        return match.group(1), match.group(2), iso_part
    
    # Обычный номер без точек
    match = re.search(r'(\d{3,6})[–—-](\d{2,4})', combined)
    if match:
        return match.group(1), match.group(2), iso_part
    
    # Буквенно-цифровой номер
    match = re.search(r'([A-ZА-Я][A-ZА-Я\s/]+?\d+)\s*[-–—]\s*(\d{4})', combined, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2), iso_part
    
    # Номер и год в разных строках
    lines = [gost_line] + context[:5]
    for i, line in enumerate(lines):
        num = re.search(r'(\d+(?:\.\d+)+)', line) or re.search(r'(\d{3,6})', line)
        if num:
            for n in lines[i+1:i+4]:
                y = re.search(r'(\d{4})', n)
                if y:
                    return num.group(1), y.group(1), iso_part
            return num.group(1), None, iso_part
    
    return None, None, iso_part

def determine_prefix(gost_line, context):
    s = (gost_line + ' ' + ' '.join(context[:3])).upper()
    s = re.sub(r'ГОСТР', 'ГОСТ Р', s)
    
    if 'ETSI' in s:
        return "ГОСТ ETSI"
    if 'OIML' in s:
        return "ГОСТ OIML"
    if 'ИСО/АСТМ' in s:
        return "ГОСТ Р ИСО/АСТМ"
    if 'ИСО/МЭК МФС' in s:
        return "ГОСТ Р ИСО/МЭК МФС"
    if 'ИСО/МЭК' in s:
        return "ГОСТ Р ИСО/МЭК"
    if 'ИСО/HL7' in s or 'ISO/HL7' in s:
        return "ГОСТ Р ИСО/HL7"
    if 'ИСО/ТО' in s:
        return "ГОСТ Р ИСО/ТО"
    if 'ИСО/ТС' in s:
        return "ГОСТ Р ИСО/ТС"
    if 'ИСО/ТУ' in s:
        return "ГОСТ Р ИСО/ТУ"
    if 'EN' in s and 'ГОСТ Р' not in s and 'ИСО' not in s:
        return "ГОСТ EN"
    if 'ISO Guide' in s:
        return "ГОСТ ISO Guide"
    if 'ИСО' in s and 'ГОСТ Р' in s:
        return "ГОСТ Р ИСО"
    if 'ИСО' in s:
        return "ГОСТ ИСО"
    if 'МЭК' in s:
        return "ГОСТ МЭК"
    if 'ГОСТ Р' in s:
        return "ГОСТ Р"
    return "ГОСТ"

def safe_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'ГОСТ(?:[\s_]+ГОСТ)+', 'ГОСТ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def get_unique_filename(folder, base_name):
    path = folder / base_name
    if not path.exists():
        return path
    stem = path.stem
    ext = path.suffix
    c = 1
    while True:
        new = folder / f"{stem} ({c}){ext}"
        if not new.exists():
            return new
        c += 1

def process_pdf(pdf_path):
    print(f"\n📄 {pdf_path.name}")
    
    for page in range(3):
        text = extract_text_from_page(pdf_path, page)
        if text:
            line_num, gost_line, context = find_gost_line_and_context(text)
            if gost_line:
                num, year, iso = extract_gost_number_from_context(gost_line, context)
                if num and year:
                    prefix = determine_prefix(gost_line, context)
                    name = f"{prefix} {num}-{year}"
                    if iso:
                        name += f" (ИСО {iso.replace(':', '-')})"
                    new_name = safe_filename(name) + ".pdf"
                    new_path = get_unique_filename(pdf_path.parent, new_name)
                    pdf_path.rename(new_path)
                    print(f"   ✅ {new_path.name}")
                    return True
    print(f"   ❌ Не распознан")
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root_dir')
    args = parser.parse_args()
    
    root = Path(args.root_dir)
    if not root.exists():
        print(f"Папка {root} не существует")
        return
    
    files = list(root.glob("*.pdf"))
    print(f"Найдено PDF: {len(files)}")
    
    ok = 0
    for f in files:
        if process_pdf(f):
            ok += 1
    
    print(f"\n✅ Успешно: {ok}/{len(files)}")

if __name__ == "__main__":
    main()