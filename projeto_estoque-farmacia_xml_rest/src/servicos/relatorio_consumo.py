"""
Geração do relatório de consumo (consumo.xsd) para o G1 puxar via SOAP ou REST.
"""
from datetime import date, datetime, timedelta
from typing import Tuple

from lxml import etree

from src.config.database import db
from src.utils.hash_utils import serializar_xml, adicionar_assinatura
from src.utils.xml_normalizer import XMLNormalizer, XMLBuilder


class RelatorioConsumoService:
    """Monta XML de consumo assinado a partir de itens_consumo."""

    def resolver_periodo(
        self,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> Tuple[date, date]:
        if data_fim is None:
            data_fim = datetime.now().date() - timedelta(days=1)
        if data_inicio is None:
            data_inicio = data_fim
        return data_inicio, data_fim

    def listar_itens(self, data_inicio: date, data_fim: date) -> list[dict]:
        rows = db.execute(
            """SELECT id_prescricao, cpf_paciente, codigo_medicamento,
                      quantidade, unidade, preco_total, data_uso
               FROM itens_consumo
               WHERE consolidado_em BETWEEN %s AND %s
               ORDER BY id_item""",
            (data_inicio, data_fim),
            fetch_all=True,
        )
        return rows or []

    def gerar_xml(self, data_inicio: date | None = None, data_fim: date | None = None) -> Tuple[str, int, date, date]:
        inicio, fim = self.resolver_periodo(data_inicio, data_fim)
        rows = self.listar_itens(inicio, fim)

        itens_normalizados = [
            {
                'id_prescricao': r['id_prescricao'],
                'cpf_paciente': r['cpf_paciente'],
                'codigo_medicamento': r['codigo_medicamento'],
                'quantidade': float(r['quantidade']),
                'unidade': r.get('unidade') or 'CAIXA',
                'preco_total': float(r['preco_total']),
                'data_uso': r['data_uso'],
            }
            for r in rows
        ]

        itens_xml = XMLNormalizer.normalizar_para_consumo(itens_normalizados)
        root = XMLBuilder.construir_consumo(itens_xml)
        adicionar_assinatura(root, 'GRUPO_3')

        return serializar_xml(root), len(rows), inicio, fim

    def marcar_como_enviado(self, data_inicio: date, data_fim: date) -> None:
        db.execute(
            """UPDATE itens_consumo
               SET enviado_para_g1 = TRUE, enviado_em = CURRENT_TIMESTAMP
               WHERE consolidado_em BETWEEN %s AND %s AND enviado_para_g1 = FALSE""",
            (data_inicio, data_fim),
        )
