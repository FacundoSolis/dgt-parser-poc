"""
DGT Vehicle Report Parser - FIXED VERSION
"""

import pdfplumber
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class VehicleData:
    """Structured vehicle data from DGT report"""
    matricula: str = ""
    bastidor: str = ""
    marca: str = ""
    modelo: str = ""
    tipo_vehiculo: str = ""
    servicio: str = ""
    masa_maxima: int = 0
    tara: int = 0
    
    titular_actual: str = ""
    cotitulares: List[str] = field(default_factory=list)
    
    es_renting: bool = False
    arrendatario_actual: str = ""
    
    historial_titulares: List[Dict] = field(default_factory=list)
    historial_arrendatarios: List[Dict] = field(default_factory=list)
    historial_itvs: List[Dict] = field(default_factory=list)
    historial_bajas: List[Dict] = field(default_factory=list)
    
    pdf_filename: str = ""


class DGTParser:
    """Parser for DGT vehicle reports"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        
    def parse(self) -> VehicleData:
        """Main parsing method"""
        print(f"\n{'='*60}")
        print(f"📄 Procesando: {self.pdf_path}")
        print(f"{'='*60}")
        
        self._extract_text()
        
        data = VehicleData(pdf_filename=self.pdf_path)
        
        self._parse_identificacion(data)
        self._parse_titular(data)
        self._parse_renting(data)
        self._parse_arrendatario(data)
        self._parse_historial_titulares(data)
        self._parse_historial_itvs(data)
        self._parse_historial_bajas(data)
        
        self._print_summary(data)
        
        return data
    
    def _extract_text(self):
        """Extract all text from PDF - concatenate all pages"""
        with pdfplumber.open(self.pdf_path) as pdf:
            # ✅ NUEVO: Concatenar TODO el texto primero
            all_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                all_text.append(page_text)

            self.text = "\n".join(all_text)

        print(f"✓ Texto extraído: {len(self.text)} caracteres")
    
    def _parse_identificacion(self, data: VehicleData):
        """Parse vehicle identification"""
        print("\n🔍 IDENTIFICACIÓN...")
        
        # Matrícula
        match = re.search(r'Matrícula:\s*([A-Z0-9]{4,7}\s?[A-Z]{3})', self.text, re.I)
        if match:
            data.matricula = match.group(1).strip()
            print(f"  ✓ Matrícula: {data.matricula}")
        
        # Bastidor
        match = re.search(r'Bastidor:\s*([A-Z0-9]{17})', self.text, re.I)
        if match:
            data.bastidor = match.group(1)
            print(f"  ✓ Bastidor: {data.bastidor}")
        
        # Marca
        match = re.search(r'Marca:\s*([A-Z\s\-]+?)(?=\s+F\.|$)', self.text, re.I)
        if match:
            data.marca = match.group(1).strip()
            print(f"  ✓ Marca: {data.marca}")
        
        # Modelo
        match = re.search(r'Modelo:\s*([A-Z0-9\s\-]+?)(?=\s+Renting:|$)', self.text, re.I)
        if match:
            data.modelo = match.group(1).strip()
            print(f"  ✓ Modelo: {data.modelo}")
        
        # Servicio
        match = re.search(r'Servicio:\s*([A-ZÁ-ÚÑ\s\-]+?)(?=\s+Tipo)', self.text, re.I)
        if match:
            data.servicio = match.group(1).strip()
            print(f"  ✓ Servicio: {data.servicio}")
        
        # Tipo de vehículo
        match = re.search(r'Tipo de vehículo:\s*([A-ZÁ-ÚÑ\s\-\(\)]+?)(?=\n|ARRENDATARIO|CARGAS)', self.text, re.I)
        if match:
            data.tipo_vehiculo = match.group(1).strip()
            print(f"  ✓ Tipo: {data.tipo_vehiculo}")
        
        # Masa máxima
        match = re.search(r'Masa máxima:\s*(\d{4,6})', self.text, re.I)
        if match:
            data.masa_maxima = int(match.group(1))
            print(f"  ✓ Masa: {data.masa_maxima} kg")
        
        # Tara
        match = re.search(r'Tara[:\s\(kg\)]*:\s*(\d{4,6})', self.text, re.I)
        if match:
            data.tara = int(match.group(1))
            print(f"  ✓ Tara: {data.tara} kg")
    
    def _parse_titular(self, data: VehicleData):
        """Parse current owner"""
        print("\n🔍 TITULAR...")
        
        match = re.search(r'Filiación:\s*([A-ZÁ-ÚÑ0-9\s\.\,\-]+?)(?=\n|Cotitulares:)', self.text, re.I)
        if match:
            data.titular_actual = match.group(1).strip()
            print(f"  ✓ Titular: {data.titular_actual}")
    
    def _parse_renting(self, data: VehicleData):
        """Parse renting info"""
        print("\n🔍 RENTING...")
        
        # Match both "Si" and "Sí"
        match = re.search(r'Renting:\s*(Sí|Si|No)', self.text, re.I)
        if match:
            renting_value = match.group(1).upper()
            data.es_renting = renting_value in ['SÍ', 'SI']
            print(f"  ✓ Renting: {'Sí' if data.es_renting else 'No'}")
    
    def _parse_arrendatario(self, data: VehicleData):
        """Parse ARRENDATARIO section"""
        print("\n🔍 ARRENDATARIO...")
        
        # Find ARRENDATARIO section
        match = re.search(r'ARRENDATARIO\s+(.+?)(?=CARGAS|DATOS SEGURO|HISTORIAL)', self.text, re.I | re.DOTALL)
        if not match:
            print("  ⚠ Sección no encontrada")
            return
        
        section = match.group(1)
        
        # Parse table rows: Fecha Inicio | Fecha fin | Filiacion
        # Example: 09/08/2022 25/10/2026 PAMPLONA T I TRANSPORTE INMEDIATO SL
        pattern = r'(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+([A-ZÁ-ÚÑ0-9\s\.\,\-]+?)(?=\n|$)'
        
        for match in re.finditer(pattern, section):
            fecha_inicio = self._parse_date(match.group(1))
            fecha_fin = self._parse_date(match.group(2))
            filiacion = match.group(3).strip()
            
            arrendatario = {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'filiacion': filiacion
            }
            
            data.historial_arrendatarios.append(arrendatario)
            
            # Set current arrendatario (if active - fecha_fin is future)
            if fecha_fin and fecha_fin > datetime.now():
                data.arrendatario_actual = filiacion
        
        print(f"  ✓ {len(data.historial_arrendatarios)} registros")
        if data.arrendatario_actual:
            print(f"  ✓ Actual: {data.arrendatario_actual}")
    
    def _parse_historial_titulares(self, data: VehicleData):
        """Parse ownership history"""
        print("\n🔍 HISTORIAL TITULARES...")
        
        match = re.search(r'HISTORIAL DE TITULARES\s+(.+?)(?=HISTORIAL|DATOS|$)', 
                         self.text, re.I | re.DOTALL)
        if not match:
            print("  ⚠ Sección no encontrada")
            return
        
        section = match.group(1)
        
        # Pattern: DD/MM/YYYY (optional end date) Type
        pattern = r'(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4}|---)\s+([A-Za-zá-ú]+)'
        
        for match in re.finditer(pattern, section):
            data.historial_titulares.append({
                'fecha_inicio': self._parse_date(match.group(1)),
                'fecha_fin': self._parse_date(match.group(2)) if match.group(2) != '---' else None,
                'tipo': match.group(3)
            })
        
        print(f"  ✓ {len(data.historial_titulares)} registros")
    
    def _parse_historial_itvs(self, data: VehicleData):
        """Parse ITV history"""
        print("\n🔍 HISTORIAL ITVs...")
        
        # Find section
        match = re.search(r'HISTORIAL DE INSPECCIONES TÉCNICAS\s+(.+?)(?=El presente documento|HISTORIAL DE LECTURAS|$)', 
                         self.text, re.I | re.DOTALL)
        if not match:
            print("  ⚠ Sección no encontrada")
            return
        
        section = match.group(1)
        
        # Split into lines
        lines = section.split('\n')
        
        current_itv = None
        
        for line in lines:
            line = line.strip()
            
            # Skip headers and empty lines
            if not line or 'Fecha ITV' in line or 'Estación' in line:
                continue
            
            # Try to match ITV line: Date | Date | Station | Result | Kilometers
            # More flexible pattern to handle various formats
            date_pattern = r'^(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\S+)\s+(FAVORABLE(?:\s+CON)?|DESFAVORABLE|NEGATIVA)'
            match = re.match(date_pattern, line, re.I)
            
            if match:
                # Save previous ITV if exists
                if current_itv:
                    data.historial_itvs.append(current_itv)
                
                # Start new ITV
                fecha_itv = self._parse_date(match.group(1))
                fecha_cad = self._parse_date(match.group(2))
                estacion = match.group(3)
                resultado = match.group(4).upper().replace(' ', '_')
                
                # Extract kilometers (after resultado)
                remaining = line[match.end():].strip()
                km_match = re.search(r'(\d{1,3}(?:\.\d{3})*|\d+)', remaining)
                kilometros = self._parse_km(km_match.group(1)) if km_match else 0
                
                current_itv = {
                    'fecha_itv': fecha_itv,
                    'fecha_caducidad': fecha_cad,
                    'estacion': estacion,
                    'resultado': resultado,
                    'kilometros': kilometros,
                    'defectos': [],
                    'gravedad': ''
                }
            elif current_itv and re.match(r'^\d{2}\.\d{2}\s+(LEVE|GRAVE)', line, re.I):
                # This is a defect line for current ITV
                current_itv['defectos'].append(line.strip())
        
        # Don't forget last ITV
        if current_itv:
            data.historial_itvs.append(current_itv)
        
        # Convert defects list to string
        for itv in data.historial_itvs:
            itv['defectos'] = '; '.join(itv['defectos']) if itv['defectos'] else ''
        
        print(f"  ✓ {len(data.historial_itvs)} inspecciones")
    
    def _parse_historial_bajas(self, data: VehicleData):
        """Parse deregistration history"""
        print("\n🔍 HISTORIAL BAJAS...")
        
        match = re.search(r'HISTORIAL DE BAJAS\s+(.+?)(?=HISTORIAL|INFORMACIÓN|$)', 
                         self.text, re.I | re.DOTALL)
        if not match:
            print("  ⚠ Sección no encontrada")
            return
        
        section = match.group(1)
        
        # Pattern: DD/MM/YYYY DD/MM/YYYY TYPE REASON
        pattern = r'(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+([A-Z]+)\s+(.+?)(?=\n|$)'
        
        for match in re.finditer(pattern, section):
            data.historial_bajas.append({
                'fecha_inicio': self._parse_date(match.group(1)),
                'fecha_fin': self._parse_date(match.group(2)),
                'tipo': match.group(3),
                'motivo': match.group(4).strip()
            })
        
        print(f"  ✓ {len(data.historial_bajas)} registros")
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse DD/MM/YYYY date"""
        if not date_str or date_str in ['---', '']:
            return None
        try:
            return datetime.strptime(date_str.strip(), '%d/%m/%Y')
        except:
            return None
    
    def _parse_km(self, km_str: str) -> int:
        """Parse kilometer value"""
        if not km_str or km_str == '---':
            return 0
        try:
            return int(km_str.replace('.', '').replace(' ', ''))
        except:
            return 0
    
    def _print_summary(self, data: VehicleData):
        """Print summary"""
        print(f"\n{'='*60}")
        print(f"✅ RESUMEN")
        print(f"{'='*60}")
        print(f"Matrícula: {data.matricula}")
        print(f"Titular: {data.titular_actual}")
        print(f"Renting: {'Sí' if data.es_renting else 'No'}")
        if data.arrendatario_actual:
            print(f"Arrendatario: {data.arrendatario_actual}")
        print(f"Arrendatarios históricos: {len(data.historial_arrendatarios)}")
        print(f"Titulares históricos: {len(data.historial_titulares)}")
        print(f"ITVs: {len(data.historial_itvs)}")
        print(f"Bajas: {len(data.historial_bajas)}")
        print(f"{'='*60}\n")