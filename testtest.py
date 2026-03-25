import pdfplumber

pdf_path = "C:\\Users\\user\\regmed_bot\\gost_pdfs\\ГОСТ Р 231.pdf"  # вставьте полный путь

with pdfplumber.open(pdf_path) as pdf:
    if len(pdf.pages) > 0:
        text = pdf.pages[0].extract_text()
        print("Первые 500 символов текста:\n")
        print(text[:500])
    else:
        print("Нет страниц")