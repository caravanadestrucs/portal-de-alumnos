"""
Extrae texto de PDFs de plan de estudios
"""
import os
import sys
from pdfminer.high_level import extract_text

pdf_dir = r"C:\Users\Dario\Desktop\restaurante\public\planpdf"
output_dir = r"C:\Users\Dario\Desktop\portal de alumnos\backend\planpdf"

# Crear directorio output
os.makedirs(output_dir, exist_ok=True)

pdfs = [
    'sistemas.pdf',
    'contaduria.pdf',
    'derecho.pdf',
    'pedagogia.pdf',
    'psicologia.pdf',
    'ciencias-del-deporte.pdf'
]

for pdf_name in pdfs:
    pdf_path = os.path.join(pdf_dir, pdf_name)
    txt_name = pdf_name.replace('.pdf', '.txt')
    txt_path = os.path.join(output_dir, txt_name)
    
    print(f"Extrayendo {pdf_name}...")
    try:
        text = extract_text(pdf_path)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"  OK: {txt_name}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nListo! Archivos txt creados en:")
print(output_dir)