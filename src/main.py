"""
Main script - Process all DGT PDFs
"""

import os
import csv
from pdf_parser import DGTParser
from business_logic import BusinessLogic


def main():
    # Configuration
    pdf_dir = "data/pdfs"
    output_file = "data/output/resultados.csv"
    
    # No client validation for POC - process all vehicles
    cliente_nif = None
    
    # Create output directory
    os.makedirs("data/output", exist_ok=True)
    
    # Get all PDFs
    pdf_files = sorted([f for f in os.listdir(pdf_dir) if f.endswith('.pdf')])
    
    print(f"\n{'='*70}")
    print(f"DGT PARSER POC - Procesamiento Completo")
    print(f"{'='*70}")
    print(f"PDFs encontrados: {len(pdf_files)}")
    print(f"Modo: Procesar TODOS los vehículos (sin filtro de cliente)")
    print(f"{'='*70}\n")
    
    # Initialize business logic
    logic = BusinessLogic(cliente_nif=cliente_nif)
    
    # Process all PDFs
    results = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        
        # Parse PDF
        parser = DGTParser(pdf_path)
        data = parser.parse()
        
        # Apply business logic
        result = logic.process_vehicle(data)
        results.append(result)
    
    # Generate CSV output
    print("\n" + "="*70)
    print("GENERANDO TABLA DE SALIDA")
    print("="*70 + "\n")
    
    # CSV headers (exact columns required)
    headers = [
        'Matrícula',
        'Fecha penúlti',
        'Lectura k',
        'Fecha últ',
        'Lectura k',
        'Días entre',
        'km ITVs',
        'km 1 año',
        'km int',
        'km nac',
        'Comentarios'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for result in results:
            row = logic.format_output_row(result)
            writer.writerow(row)
    
    print(f"✅ Tabla generada: {output_file}")
    print(f"✅ Total vehículos procesados: {len(results)}")
    
    # Show preview
    print("\n" + "="*70)
    print("PREVIEW - Primeros 5 vehículos:")
    print("="*70)
    
    for i, result in enumerate(results[:5], 1):
        print(f"\n{i}. {result['matricula']}")
        if result['fecha_ult']:
            print(f"   Última ITV: {result['fecha_ult'].strftime('%d/%m/%Y')}")
            print(f"   Kilómetros: {result['lectura_k_ult']:,} km")
            if result['km_1_ano'] > 0:
                print(f"   km/año: {result['km_1_ano']:,}")
        else:
            print(f"   Última ITV: N/A")
        
        if result['comentarios']:
            print(f"   Comentarios: {'; '.join(result['comentarios'])}")
        else:
            print(f"   ✓ OK - Listo para procesamiento")
    
    print("\n" + "="*70)
    print(f"✅ Ver archivo completo: {output_file}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()