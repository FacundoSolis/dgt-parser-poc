from src.pdf_parser import DGTParser

# Vehículos que deberían tener bajas
for matricula in ['9952HPL', '9990JJY']:
    pdf_path = f"data/pdfs/{matricula}.pdf"
    parser = DGTParser(pdf_path)
    data = parser.parse()
    
    print(f"\n{'='*60}")
    print(f"{matricula} - Bajas:")
    print(f"{'='*60}")
    for baja in data.historial_bajas:
        print(f"  Fecha inicio: {baja['fecha_inicio']}")
        print(f"  Fecha fin: {baja['fecha_fin']}")
        print(f"  Tipo: {baja['tipo']}")
        print(f"  Motivo: {baja['motivo']}")
        print()
