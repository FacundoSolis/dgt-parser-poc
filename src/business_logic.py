"""
Business Logic - DGT Vehicle Processing Rules
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from .pdf_parser import VehicleData


class BusinessLogic:
    """Applies DGT business rules to vehicle data"""
    
    def __init__(self, cliente_nif: Optional[str] = None):
        self.cliente_nif = cliente_nif
    
    def process_vehicle(self, data: VehicleData) -> Dict[str, Any]:
        """Process vehicle through all business rules"""
        
        result = {
            'matricula': data.matricula,
            'fecha_penulti': None,
            'lectura_k_penulti': 0,
            'fecha_ult': None,
            'lectura_k_ult': 0,
            'dias_entre': 0,
            'km_itvs': 0,
            'km_1_ano': 0,
            'km_int': 0,
            'km_nac': 0,
            'comentarios': []
        }
        
        # RULE 1 & 2: Check Titularity/Renting
        if not self._check_titularity(data, result):
            if not self._check_renting(data, result):
                result['comentarios'].append("El vehículo no es susceptible de generar CAEs")
                return result
        
        # RULE 3: Check BAJAS
        self._check_bajas(data, result)
        
        # RULE 4: Calculate ITV metrics
        self._calculate_itv_metrics(data, result)
        
        return result
    
    def _check_titularity(self, data: VehicleData, result: Dict) -> bool:
        """Check if current titular matches client"""
        if not self.cliente_nif:
            return True
        
        titular_upper = data.titular_actual.upper()
        cliente_upper = self.cliente_nif.upper()
        
        return cliente_upper in titular_upper
    
    def _check_renting(self, data: VehicleData, result: Dict) -> bool:
        """Check renting/arrendamiento"""
        if not self.cliente_nif:
            return data.es_renting
        
        cliente_upper = self.cliente_nif.upper()
        
        if data.es_renting:
            if data.arrendatario_actual:
                arrendatario_upper = data.arrendatario_actual.upper()
                if cliente_upper in arrendatario_upper:
                    return True
            
            for arrendatario in data.historial_arrendatarios:
                filiacion = arrendatario.get('filiacion', '').upper()
                if cliente_upper not in filiacion:
                    continue
                
                fecha_inicio = arrendatario.get('fecha_inicio')
                fecha_fin = arrendatario.get('fecha_fin')
                
                if fecha_inicio and fecha_fin:
                    meses = (fecha_fin - fecha_inicio).days / 30.44
                    if meses > 14:
                        return True
            
            return False
        
        return False
    
    def _check_bajas(self, data: VehicleData, result: Dict):
        """Check if vehicle has BAJAS after 01/01/2023"""
        cutoff_date = datetime(2023, 1, 1)
        
        for baja in data.historial_bajas:
            fecha_inicio = baja.get('fecha_inicio')
            fecha_fin = baja.get('fecha_fin')
            
            if fecha_inicio and fecha_inicio >= cutoff_date:
                fecha_inicio_str = fecha_inicio.strftime('%d/%m/%Y')
                fecha_fin_str = fecha_fin.strftime('%d/%m/%Y') if fecha_fin else 'Actual'
                
                result['comentarios'].append(
                    f"Vehículo de baja del {fecha_inicio_str} hasta el {fecha_fin_str}"
                )
    
    def _calculate_itv_metrics(self, data: VehicleData, result: Dict):
        """
        Calculate ITV metrics with improved filtering
        
        Priority:
        1. FAVORABLE result only
        2. Has kilometraje > 0 (prefer ITVs with odometer readings)
        3. Non-decreasing kilometers
        """
        if not data.historial_itvs:
            result['comentarios'].append("Sin historial de ITVs")
            return
        
        # Sort ITVs by date (most recent first)
        itvs_sorted = sorted(
            data.historial_itvs,
            key=lambda x: x['fecha_itv'] if x['fecha_itv'] else datetime.min,
            reverse=True
        )
        
        # Filter valid ITVs
        valid_itvs = []
        
        for itv in itvs_sorted:
            resultado = itv.get('resultado', '').upper()
            kilometros = itv.get('kilometros', 0)
            
            # a) Ignore DESFAVORABLE or NEGATIVA
            if 'DESFAVORABLE' in resultado or 'NEGATIVA' in resultado:
                continue
            
            valid_itvs.append(itv)
        
        # Separate ITVs with km > 0 from those with km = 0
        itvs_with_km = [itv for itv in valid_itvs if itv.get('kilometros', 0) > 0]
        itvs_without_km = [itv for itv in valid_itvs if itv.get('kilometros', 0) == 0]
        
        # Prefer ITVs with kilometers
        if len(itvs_with_km) >= 2:
            # We have at least 2 ITVs with km readings - use those
            working_itvs = itvs_with_km
        elif len(itvs_with_km) == 1:
            # Only one ITV with km - can't calculate CAEs
            result['comentarios'].append("El vehículo no es susceptible de generar CAEs")
            return
        else:
            # No ITVs with km readings
            if valid_itvs:
                result['comentarios'].append("ITVs válidas sin lecturas de kilometraje")
                result['fecha_ult'] = valid_itvs[0]['fecha_itv']
            else:
                result['comentarios'].append("Sin ITVs válidas (todas DESFAVORABLE/NEGATIVA)")
            return
        
        # Now filter for non-decreasing kilometers
        filtered_itvs = []
        last_km = float('inf')  # Start with infinity (most recent should have highest km)
        
        for itv in working_itvs:
            km = itv.get('kilometros', 0)
            if km <= last_km:
                filtered_itvs.append(itv)
                last_km = km
        
        if len(filtered_itvs) < 2:
            if filtered_itvs:
                itv = filtered_itvs[0]
                result['fecha_ult'] = itv['fecha_itv']
                result['lectura_k_ult'] = itv['kilometros']
                result['comentarios'].append("Solo una ITV válida con kilometraje consistente")
            return
        
        # Select última (most recent) and penúltima (second most recent)
        ultima = filtered_itvs[0]
        penultima = filtered_itvs[1]
        # Safety check: ensure they're different
        if ultima['fecha_itv'] == penultima['fecha_itv'] and ultima['kilometros'] == penultima['kilometros']:
            result['comentarios'].append("El vehículo no es susceptible de generar CAEs")
            return
        
        result['fecha_ult'] = ultima['fecha_itv']
        result['lectura_k_ult'] = ultima['kilometros']
        result['fecha_penulti'] = penultima['fecha_itv']
        result['lectura_k_penulti'] = penultima['kilometros']
        
        # Calculate días entre
        if result['fecha_ult'] and result['fecha_penulti']:
            dias = (result['fecha_ult'] - result['fecha_penulti']).days
            result['dias_entre'] = dias
            
            # Calculate km ITVs
            if result['lectura_k_ult'] > 0 and result['lectura_k_penulti'] > 0:
                result['km_itvs'] = result['lectura_k_ult'] - result['lectura_k_penulti']
                
                # Calculate km 1 año
                if dias > 0:
                    result['km_1_ano'] = int((result['km_itvs'] * 365) / dias)
                else:
                    result['comentarios'].append("Días entre ≤ 0, km 1 año = N/A")
        
        # km int and km nac - not in PDF
        result['km_int'] = 0
        result['km_nac'] = 0
    
    def format_output_row(self, result: Dict) -> List[str]:
        """Format result as output row"""
        def fmt_date(d):
            return d.strftime('%d/%m/%Y') if d else '-'
        
        def fmt_int(n):
            return str(n) if n > 0 else '0'
        
        comentarios_str = '; '.join(result['comentarios']) if result['comentarios'] else ''
        
        return [
            result['matricula'],
            fmt_date(result['fecha_penulti']),
            fmt_int(result['lectura_k_penulti']),
            fmt_date(result['fecha_ult']),
            fmt_int(result['lectura_k_ult']),
            fmt_int(result['dias_entre']),
            fmt_int(result['km_itvs']),
            fmt_int(result['km_1_ano']),
            fmt_int(result['km_int']),
            fmt_int(result['km_nac']),
            comentarios_str
        ]