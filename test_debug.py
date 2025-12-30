import pdfplumber

pdf_path = "data/pdfs/2860LZG.pdf"

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total páginas: {len(pdf.pages)}\n")
    
    # Página 1
    print("="*70)
    print("PÁGINA 1 - Primeros 2500 caracteres:")
    print("="*70)
    text1 = pdf.pages[0].extract_text()
    print(text1[:2500])
    
    # Página 2 (si existe)
    if len(pdf.pages) > 1:
        print("\n" + "="*70)
        print("PÁGINA 2 - Primeros 2500 caracteres:")
        print("="*70)
        text2 = pdf.pages[1].extract_text()
        print(text2[:2500])