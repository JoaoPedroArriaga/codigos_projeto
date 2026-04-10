import os
import sys
import time
import subprocess
from pathlib import Path

BASE = Path(r"C:\Users\Joaop\Documents\Faculdade\Interoperabilidade\Projeto")
CSV_DIR = BASE / "projeto-estoque-farmacia"
XML_DIR = BASE / "projeto_estoque-farmacia_xml"

def contar_arquivos_por_pasta(projeto_dir, extensao):
    resultados = {}
    pastas = [
        ("data/saida/respostas", "saida_respostas"),
        ("data/saida/consumos", "saida_consumos"),
        ("data/processados/consultas", "processados_consultas"),
        ("data/processados/reservas", "processados_reservas"),
        ("data/processados/baixas", "processados_baixas"),
    ]
    
    for pasta, nome in pastas:
        caminho = projeto_dir / pasta
        if caminho.exists():
            arquivos = list(caminho.glob(f"*{extensao}"))
            tamanho = sum(a.stat().st_size for a in arquivos)
            resultados[nome] = (len(arquivos), tamanho)
        else:
            resultados[nome] = (0, 0)
    
    return resultados

def executar_teste(script_path, projeto_dir):
    original_dir = os.getcwd()
    os.chdir(projeto_dir)
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    start = time.perf_counter()
    try:
        result = subprocess.run(
            [sys.executable, str(script_path.relative_to(projeto_dir))],
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
            encoding='utf-8',
            errors='replace'
        )
        end = time.perf_counter()
        
        if result.returncode != 0:
            print(f"   Erro: {result.stderr[:200] if result.stderr else 'Desconhecido'}")
            return None, False
        
        # Extrair tempos da saida
        tempos = {}
        for line in result.stdout.split('\n'):
            line = line.strip()
            if 'Geracao de arquivos:' in line:
                try:
                    val = line.split(':')[1].strip().replace('s', '')
                    tempos['geracao'] = float(val)
                except:
                    pass
            elif 'Processamento:' in line and 'Processamento' not in tempos:
                try:
                    val = line.split(':')[1].strip().replace('s', '')
                    tempos['processamento'] = float(val)
                except:
                    pass
            elif 'Geracao de consumo:' in line:
                try:
                    val = line.split(':')[1].strip().replace('s', '')
                    tempos['consumo'] = float(val)
                except:
                    pass
            elif 'TOTAL:' in line:
                try:
                    val = line.split(':')[1].strip().replace('s', '')
                    tempos['total'] = float(val)
                except:
                    pass
        
        return tempos, True
    except Exception as e:
        print(f"   Excecao: {e}")
        return None, False
    finally:
        os.chdir(original_dir)

def main():
    print("=" * 70)
    print("COMPARADOR PADRONIZADO CSV vs XML")
    print("=" * 70)
    
    script_csv = CSV_DIR / "scripts" / "teste_padronizado_csv.py"
    script_xml = XML_DIR / "scripts" / "teste_padronizado_xml.py"
    
    # Executar CSV
    print("\n[EXECUTANDO] Teste CSV...")
    tempos_csv, ok_csv = executar_teste(script_csv, CSV_DIR)
    if ok_csv and tempos_csv:
        arquivos_csv = contar_arquivos_por_pasta(CSV_DIR, ".csv")
        print("   [OK] Concluido")
    else:
        print("   [FALHA]")
        return
    
    # Executar XML
    print("\n[EXECUTANDO] Teste XML...")
    tempos_xml, ok_xml = executar_teste(script_xml, XML_DIR)
    if ok_xml and tempos_xml:
        arquivos_xml = contar_arquivos_por_pasta(XML_DIR, ".xml")
        print("   [OK] Concluido")
    else:
        print("   [FALHA]")
        return
    
    # RESULTADOS
    print("\n" + "=" * 70)
    print("RESULTADOS DA COMPARACAO")
    print("=" * 70)
    
    # 1. TEMPOS
    print("\n[1] TEMPOS (segundos):")
    print(f"   {'Etapa':<20} {'CSV':>12} {'XML':>12} {'Diferenca':>12}")
    print("   " + "-" * 58)
    
    for etapa in ['geracao', 'processamento', 'consumo', 'total']:
        csv_t = tempos_csv.get(etapa, 0)
        xml_t = tempos_xml.get(etapa, 0)
        if csv_t > 0 or xml_t > 0:
            diff = xml_t - csv_t
            diff_pct = (diff / csv_t * 100) if csv_t > 0 else 0
            print(f"   {etapa:<20} {csv_t:>11.4f}s {xml_t:>11.4f}s {diff_pct:>+11.1f}%")
    
    # 2. TAMANHOS
    print("\n[2] TAMANHOS (bytes):")
    print(f"   {'Tipo':<25} {'CSV':>12} {'XML':>12} {'Diferenca':>12}")
    print("   " + "-" * 63)
    
    total_csv = 0
    total_xml = 0
    
    tipos = ['saida_respostas', 'saida_consumos', 'processados_consultas', 'processados_reservas', 'processados_baixas']
    nomes = ['saida respostas', 'saida consumos', 'processados consultas', 'processados reservas', 'processados baixas']
    
    for tipo, nome in zip(tipos, nomes):
        csv_qtd, csv_bytes = arquivos_csv.get(tipo, (0, 0))
        xml_qtd, xml_bytes = arquivos_xml.get(tipo, (0, 0))
        total_csv += csv_bytes
        total_xml += xml_bytes
        
        if csv_bytes > 0 or xml_bytes > 0:
            diff = xml_bytes - csv_bytes
            diff_pct = (diff / csv_bytes * 100) if csv_bytes > 0 else 0
            print(f"   {nome:<25} {csv_bytes:>11,}b {xml_bytes:>11,}b {diff_pct:>+11.1f}%")
    
    print("   " + "-" * 63)
    diff_total = total_xml - total_csv
    diff_pct_total = (diff_total / total_csv * 100) if total_csv > 0 else 0
    print(f"   {'TOTAL':<25} {total_csv:>11,}b {total_xml:>11,}b {diff_pct_total:>+11.1f}%")
    
    # 3. QUANTIDADE DE ARQUIVOS
    print("\n[3] QUANTIDADE DE ARQUIVOS:")
    print(f"   {'Tipo':<25} {'CSV':>8} {'XML':>8}")
    print("   " + "-" * 43)
    
    total_qtd_csv = 0
    total_qtd_xml = 0
    
    for tipo, nome in zip(tipos, nomes):
        csv_qtd, _ = arquivos_csv.get(tipo, (0, 0))
        xml_qtd, _ = arquivos_xml.get(tipo, (0, 0))
        total_qtd_csv += csv_qtd
        total_qtd_xml += xml_qtd
        
        if csv_qtd > 0 or xml_qtd > 0:
            print(f"   {nome:<25} {csv_qtd:>8} {xml_qtd:>8}")
    
    print("   " + "-" * 43)
    print(f"   {'TOTAL':<25} {total_qtd_csv:>8} {total_qtd_xml:>8}")
    
    # 4. RESUMO
    print("\n" + "=" * 70)
    print("RESUMO DA COMPARACAO")
    print("=" * 70)
    
    if tempos_csv and tempos_xml:
        tempo_csv = tempos_csv.get('total', 0)
        tempo_xml = tempos_xml.get('total', 0)
        diff_tempo = (tempo_xml / tempo_csv - 1) * 100 if tempo_csv > 0 else 0
        
        print(f"\n   Velocidade: XML e {diff_tempo:+.1f}% mais lento")
        print(f"   Tamanho:    XML e {diff_pct_total:+.1f}% maior")
        print(f"   Arquivos:   XML gera {total_qtd_xml - total_qtd_csv:+d} arquivos")
    
    print("\n[OK] Comparacao concluida!")

if __name__ == "__main__":
    main()