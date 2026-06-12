"""
Geração do relatório de consumo em JSON para o G1 puxar via REST.
"""
import json
import os
from datetime import date, datetime, timedelta
from typing import Any

from dotenv import load_dotenv

from src.config.database import db

load_dotenv()


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

    def _gerar_nome_arquivo_json(self) -> str:
        return f"CONSUMO_{datetime.now().strftime('%y%m%d')}.json"

    def gerar_e_salvar_arquivo(
        self,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> tuple[str, str, str, int, date, date]:
        """
        Gera relatório JSON, grava em data/saida/consumos/ e retorna metadados.
        Não marca enviado_para_g1 — isso fica para o pull do G1 via REST.
        """
        relatorio, inicio, fim = self.gerar_json(data_inicio, data_fim)
        total = relatorio["total_itens"]
        if total == 0:
            raise ValueError(
                f"Nenhum item de consumo entre {inicio.isoformat()} e {fim.isoformat()}"
            )

        nome_arquivo = self._gerar_nome_arquivo_json()
        data_dir = os.getenv("DATA_DIR", "data")
        pasta_consumos = os.getenv("PASTA_CONSUMOS", "saida/consumos")
        caminho = os.path.join(data_dir, pasta_consumos, nome_arquivo)

        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)

        conteudo = json.dumps(relatorio, ensure_ascii=False, indent=2)
        return caminho, nome_arquivo, conteudo, total, inicio, fim

    def marcar_como_enviado(self, data_inicio: date, data_fim: date) -> None:
        db.execute(
            """UPDATE itens_consumo
               SET enviado_para_g1 = TRUE, enviado_em = CURRENT_TIMESTAMP
               WHERE consolidado_em BETWEEN %s AND %s AND enviado_para_g1 = FALSE""",
            (data_inicio, data_fim),
        )
