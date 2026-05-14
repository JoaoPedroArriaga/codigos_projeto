"""
Endpoints da API REST usando FastAPI.
Rotas para reservas de medicamentos.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from src.schemas import ReservaRequestSchema, ReservaResponseSchema
from src.repositorios import RepositorioReserva, RepositorioLote, RepositorioMedicamento
from src.casos_de_uso import CasoDeUsoReserva
from src.config.database import db

router = APIRouter(prefix="/api/reservas", tags=["Reservas"])


def get_repo_reserva():
    return RepositorioReserva(db)


def get_repo_lote():
    return RepositorioLote(db)


def get_repo_medicamento():
    return RepositorioMedicamento(db)


def get_caso_de_uso_reserva(
    repo_reserva=Depends(get_repo_reserva),
    repo_lote=Depends(get_repo_lote),
    repo_med=Depends(get_repo_medicamento)
):
    return CasoDeUsoReserva(repo_reserva, repo_lote, repo_med)


@router.post("", response_model=ReservaResponseSchema)
async def criar_reserva(
    dados: ReservaRequestSchema,
    caso_de_uso: CasoDeUsoReserva = Depends(get_caso_de_uso_reserva)
):
    """
    Cria uma nova reserva de medicamento
    
    Args:
        dados: Código do medicamento, quantidade, número do lote e CPF do paciente
        
    Returns:
        Confirmação da reserva com ID único
    """
    try:
        resultado = caso_de_uso.criar_reserva(
            dados.codigo_medicamento,
            dados.quantidade,
            dados.lote,
            dados.cpf_paciente
        )
        
        if not resultado['success']:
            raise HTTPException(status_code=400, detail=resultado['mensagem'])
        
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar reserva: {str(e)}")


@router.get("")
async def listar_reservas_ativas(
    repo_reserva: RepositorioReserva = Depends(get_repo_reserva)
):
    """
    Lista todas as reservas ativas
    
    Returns:
        Lista de reservas com status 'ativa'
    """
    try:
        reservas = repo_reserva.listar_ativas()
        return {
            'total': len(reservas),
            'reservas': reservas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar reservas: {str(e)}")


@router.get("/{id_reserva}")
async def obter_reserva(
    id_reserva: int,
    repo_reserva: RepositorioReserva = Depends(get_repo_reserva)
):
    """
    Obtém detalhes de uma reserva específica
    
    Args:
        id_reserva: ID da reserva
        
    Returns:
        Detalhes da reserva
    """
    try:
        reserva = repo_reserva.buscar_por_id(id_reserva)
        if not reserva:
            raise HTTPException(status_code=404, detail=f"Reserva {id_reserva} não encontrada")
        return reserva
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter reserva: {str(e)}")


@router.delete("/{id_reserva}")
async def cancelar_reserva(
    id_reserva: int,
    caso_de_uso: CasoDeUsoReserva = Depends(get_caso_de_uso_reserva)
):
    """
    Cancela uma reserva
    
    Args:
        id_reserva: ID da reserva a cancelar
        
    Returns:
        Confirmação do cancelamento
    """
    try:
        resultado = caso_de_uso.cancelar_reserva(id_reserva)
        
        if not resultado['success']:
            raise HTTPException(status_code=400, detail=resultado['mensagem'])
        
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar reserva: {str(e)}")
