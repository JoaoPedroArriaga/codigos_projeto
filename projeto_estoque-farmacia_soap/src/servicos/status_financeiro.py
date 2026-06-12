"""
Sincronização de status financeiro recebido do G1 (status_financeiro.xsd).
"""
from datetime import datetime
from typing import Any, Dict

from lxml import etree

from src.utils.hash_utils import calcular_hmac, serializar_xml


class StatusFinanceiroService:
    """Processa XML de status do G1 e mantém cache em memória."""

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}

    def sincronizar(self, arquivo_xml: str, grupo_origem: str) -> tuple[int, str]:
        root = etree.fromstring(arquivo_xml.encode('utf-8'))

        assinatura_elem = root.find('assinatura')
        if assinatura_elem is None:
            raise Exception("ASSINATURA_FALTANDO: XML deve conter elemento <assinatura>")

        hash_recebido = assinatura_elem.findtext('hash')
        if not hash_recebido:
            raise Exception("ASSINATURA_INVALIDA: Elemento <hash> vazio")

        root.remove(assinatura_elem)
        hash_calculado = calcular_hmac(serializar_xml(root))
        if hash_recebido != hash_calculado:
            raise Exception("ASSINATURA_INVALIDA: Hash não confere com conteúdo")

        root.append(assinatura_elem)
        total = 0

        for pac_elem in root.findall('paciente'):
            cpf_elem = pac_elem.find('cpf')
            status_elem = pac_elem.find('status')
            if cpf_elem is None or status_elem is None:
                raise Exception("XML_INVALIDO: Faltam campos cpf ou status")

            permite = pac_elem.find('permite_atendimento')
            observacao = pac_elem.find('observacao')
            cpf = cpf_elem.text.replace('.', '').replace('-', '')

            self.cache[cpf] = {
                'cpf': cpf,
                'status': status_elem.text,
                'permite_atendimento': int(permite.text or 0) if permite is not None else 0,
                'observacao': observacao.text if observacao is not None else None,
                'sincronizado_em': datetime.now().isoformat(),
                'grupo_origem': grupo_origem,
            }
            total += 1

        return total, f"Sincronizados {total} pacientes de {grupo_origem}"

    def consultar(self, cpf: str) -> Dict[str, Any]:
        cpf_limpo = cpf.replace('.', '').replace('-', '')
        if len(cpf_limpo) != 11:
            raise Exception("CPF_INVALIDO: CPF deve ter 11 dígitos")
        if cpf_limpo not in self.cache:
            raise Exception(f"PACIENTE_NAO_ENCONTRADO: CPF {cpf} não tem status cadastrado")
        return self.cache[cpf_limpo]
