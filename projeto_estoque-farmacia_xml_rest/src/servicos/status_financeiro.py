"""
Sincronização de status financeiro recebido do G1 via REST/JSON.
"""
from datetime import datetime
from typing import Any

import re


class StatusFinanceiroService:
    """Processa status financeiro do G1 e mantém cache em memória."""

    def __init__(self):
        self.cache: dict[str, dict[str, Any]] = {}

    def sincronizar(self, pacientes: list[dict[str, Any]], grupo_origem: str) -> tuple[int, str]:
        if not pacientes:
            raise ValueError("LISTA_VAZIA: Envie ao menos um paciente")

        total = 0
        for paciente in pacientes:
            cpf = re.sub(r"[^0-9]", "", str(paciente.get("cpf", "")))
            status = paciente.get("status")
            if len(cpf) != 11:
                raise ValueError(f"CPF_INVALIDO: CPF deve ter 11 dígitos ({cpf})")
            if not status:
                raise ValueError(f"DADOS_INVALIDOS: status obrigatório para CPF {cpf}")

            self.cache[cpf] = {
                "cpf": cpf,
                "status": status,
                "permite_atendimento": int(paciente.get("permite_atendimento", 0)),
                "observacao": paciente.get("observacao"),
                "sincronizado_em": datetime.now().isoformat(),
                "grupo_origem": grupo_origem,
            }
            total += 1

        return total, f"Sincronizados {total} pacientes de {grupo_origem}"

    def consultar(self, cpf: str) -> dict[str, Any]:
        cpf_limpo = re.sub(r"[^0-9]", "", cpf)
        if len(cpf_limpo) != 11:
            raise ValueError("CPF_INVALIDO: CPF deve ter 11 dígitos")
        if cpf_limpo not in self.cache:
            raise ValueError(f"PACIENTE_NAO_ENCONTRADO: CPF {cpf} não tem status cadastrado")
        return self.cache[cpf_limpo]
