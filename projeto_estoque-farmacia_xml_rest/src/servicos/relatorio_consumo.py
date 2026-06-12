"""
Geração do relatório de consumo em JSON para o G1 puxar via REST.
"""
from datetime import date, datetime, timedelta
from typing import Any

from src.config.database import db


class RelatorioConsumoService:
    """Monta relatório de consumo a partir de itens_consumo."""

    def resolver_periodo(
        self,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> tuple[date, date]:
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

    def _formatar_cpf(self, valor) -> str:
        if valor is None:
            return ""
        cpf = str(valor).split(".")[0]
        return cpf.zfill(11) if cpf.isdigit() else cpf

    def _formatar_item(self, row: dict) -> dict[str, Any]:
        data_uso = row["data_uso"]
        if hasattr(data_uso, "isoformat"):
            data_uso = data_uso.isoformat()
        else:
            data_uso = str(data_uso)

        return {
            "prescricao": str(row["id_prescricao"]),
            "cpf": self._formatar_cpf(row["cpf_paciente"]),
            "codigo_medicamento": int(row["codigo_medicamento"]),
            "quantidade": float(row["quantidade"]),
            "unidade": row.get("unidade") or "CAIXA",
            "preco_total": float(row["preco_total"]),
            "data_uso": data_uso,
        }

    def gerar_json(
        self,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> tuple[dict[str, Any], date, date]:
        inicio, fim = self.resolver_periodo(data_inicio, data_fim)
        rows = self.listar_itens(inicio, fim)
        itens = [self._formatar_item(r) for r in rows]

        return {
            "data_inicio": inicio.isoformat(),
            "data_fim": fim.isoformat(),
            "total_itens": len(itens),
            "itens": itens,
        }, inicio, fim

    def marcar_como_enviado(self, data_inicio: date, data_fim: date) -> None:
        db.execute(
            """UPDATE itens_consumo
               SET enviado_para_g1 = TRUE, enviado_em = CURRENT_TIMESTAMP
               WHERE consolidado_em BETWEEN %s AND %s AND enviado_para_g1 = FALSE""",
            (data_inicio, data_fim),
        )
