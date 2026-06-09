"""
Endpoints da API REST usando FastAPI.
Rotas para medicamentos - READ operations only.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from src.schemas import MedicamentoResponseSchema
from src.repositorios import RepositorioMedicamento
from src.config.database import db

router = APIRouter(prefix="/api/medicamentos", tags=["Medicamentos"])


def get_repo_medicamento():
    """Dependency Injection para repositório"""
    return RepositorioMedicamento(db)


@router.get("", response_model=List[MedicamentoResponseSchema])
async def listar_medicamentos(repo: RepositorioMedicamento = Depends(get_repo_medicamento)):
    """
    Lista todos os medicamentos cadastrados
    
    Returns:
        Lista de medicamentos com código e nome
    """
    try:
        medicamentos = repo.listar_todos()
        return medicamentos if medicamentos else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar medicamentos: {str(e)}")


@router.get("/{codigo}", response_model=MedicamentoResponseSchema)
async def obter_medicamento(codigo: int, repo: RepositorioMedicamento = Depends(get_repo_medicamento)):
    """
    Obtém um medicamento específico por código
    
    Args:
        codigo: Código único do medicamento
        
    Returns:
        Dados do medicamento
    """
    try:
        medicamento = repo.buscar_por_codigo(codigo)
        if not medicamento:
            raise HTTPException(status_code=404, detail=f"Medicamento {codigo} não encontrado")
        return medicamento
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar medicamento: {str(e)}")
