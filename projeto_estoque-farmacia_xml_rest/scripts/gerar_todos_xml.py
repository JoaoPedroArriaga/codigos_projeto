#!/usr/bin/env python
"""
Script para gerar todos os arquivos XML de uma vez (fluxo completo)
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.gerar_consulta_xml import gerar_consulta_xml
from scripts.gerar_reserva_xml import gerar_reserva_xml
from scripts.gerar_baixa_xml import gerar_baixa_xml

def gerar_fluxo_completo(codigo=789123, quantidade=2, lote='LOTE002'):
    """Gera consulta, reserva e baixa em sequência"""
    print("=" * 60)
    print("📦 GERANDO FLUXO COMPLETO XML")
    print("=" * 60)
    
    id_base = datetime.now().strftime('%H%M%S')
    
    # Gerar consulta
    print("\n[1/3] Gerando CONSULTA XML...")
    consulta = gerar_consulta_xml(
        codigo_medicamento=codigo,
        quantidade=quantidade,
        id_prescricao=id_base
    )
    
    # Gerar reserva
    print("\n[2/3] Gerando RESERVA XML...")
    reserva = gerar_reserva_xml(
        codigo_medicamento=codigo,
        quantidade=quantidade,
        id_prescricao=id_base
    )
    
    # Gerar baixa
    print("\n[3/3] Gerando BAIXA XML...")
    baixa = gerar_baixa_xml(
        codigo_medicamento=codigo,
        quantidade=quantidade,
        lote=lote,
        id_prescricao=id_base
    )
    
    print("\n" + "=" * 60)
    print("✅ TODOS OS XMLs GERADOS!")
    print("=" * 60)
    
    return consulta, reserva, baixa

if __name__ == "__main__":
    gerar_fluxo_completo()