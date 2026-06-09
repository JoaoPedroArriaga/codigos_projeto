"""
Endpoints da API REST usando FastAPI.
Rotas para consultas de estoque e disponibilidade.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from src.schemas import EstoqueResponseSchema, ConsultaRequestSchema, ConsultaResponseSchema
from src.repositorios import RepositorioLote, RepositorioMedicamento
from src.casos_de_uso import CasoDeUsoEstoque, CasoDeUsoConsulta
from src.config.database import db

router = APIRouter(prefix="/api/estoque", tags=["Estoque"])


def get_repo_lote():
    return RepositorioLote(db)


def get_repo_medicamento():
    return RepositorioMedicamento(db)


def get_caso_de_uso_estoque(repo_lote=Depends(get_repo_lote), repo_med=Depends(get_repo_medicamento)):
    return CasoDeUsoEstoque(repo_lote, repo_med)


def get_caso_de_uso_consulta(repo_lote=Depends(get_repo_lote), repo_med=Depends(get_repo_medicamento)):
    return CasoDeUsoConsulta(repo_lote, repo_med)


@router.get("/{codigo_medicamento}", response_model=EstoqueResponseSchema)
async def obter_estoque(
    codigo_medicamento: int,
    caso_de_uso: CasoDeUsoEstoque = Depends(get_caso_de_uso_estoque)
):
    """
    Obtém informações de estoque de um medicamento
    
    Args:
        codigo_medicamento: Código do medicamento
        
    Returns:
        Detalhes do estoque e lotes disponíveis
    """
    try:
        estoque = caso_de_uso.obter_estoque_total(codigo_medicamento)
        if estoque['quantidade_total'] == 0:
            raise HTTPException(status_code=404, detail=f"Nenhum estoque para medicamento {codigo_medicamento}")
        return {
            'codigo_medicamento': codigo_medicamento,
            'nome_medicamento': 'N/A',  # Será preenchido com join se necessário
            'quantidade_total': estoque['quantidade_total'],
            'lotes': estoque['lotes']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estoque: {str(e)}")


@router.post("/consultar", response_model=ConsultaResponseSchema)
async def consultar_disponibilidade(
    dados: ConsultaRequestSchema,
    caso_de_uso: CasoDeUsoConsulta = Depends(get_caso_de_uso_consulta)
):
    """
    Consulta disponibilidade de um medicamento
    
    Args:
        dados: Código do medicamento, quantidade e CPF do paciente
        
    Returns:
        Disponibilidade, lote sugerido e preço
    """
    try:
        resultado = caso_de_uso.processar_consulta(
            dados.codigo_medicamento,
            dados.quantidade,
            dados.cpf_paciente
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na consulta: {str(e)}")


@router.get("/lotes/{codigo_medicamento}")
async def listar_lotes(
    codigo_medicamento: int,
    repo_lote: RepositorioLote = Depends(get_repo_lote)
):
    """
    Lista todos os lotes de um medicamento
    
    Args:
        codigo_medicamento: Código do medicamento
        
    Returns:
        Lista de lotes com informações de quantidade e validade
    """
    try:
        lotes = repo_lote.listar_por_medicamento(codigo_medicamento)
        if not lotes:
            raise HTTPException(status_code=404, detail=f"Nenhum lote encontrado para medicamento {codigo_medicamento}")
        return {
            'codigo_medicamento': codigo_medicamento,
            'total_lotes': len(lotes),
            'lotes': lotes
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar lotes: {str(e)}")
