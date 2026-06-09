"""
Endpoints da API REST usando FastAPI.
Rotas para baixas de estoque.
"""
from fastapi import APIRouter, HTTPException, Depends
from src.schemas import BaixaRequestSchema, BaixaResponseSchema
from src.repositorios import RepositorioLote, RepositorioMedicamento
from src.casos_de_uso import CasoDeUsoBaixa
from src.config.database import db

router = APIRouter(prefix="/api/baixas", tags=["Baixas"])


def get_repo_lote():
    return RepositorioLote(db)


def get_repo_medicamento():
    return RepositorioMedicamento(db)


def get_caso_de_uso_baixa(
    repo_lote=Depends(get_repo_lote),
    repo_med=Depends(get_repo_medicamento)
):
    return CasoDeUsoBaixa(repo_lote, repo_med)


@router.post("", response_model=BaixaResponseSchema)
async def dar_baixa(
    dados: BaixaRequestSchema,
    caso_de_uso: CasoDeUsoBaixa = Depends(get_caso_de_uso_baixa)
):
    """
    Registra uma baixa de estoque (reduz quantidade do lote)
    
    Args:
        dados: Código do medicamento, quantidade, lote e motivo (opcional)
        
    Returns:
        Confirmação da baixa com quantidade restante
    """
    try:
        # Iniciar transação explícita
        db.begin()
        
        try:
            resultado = caso_de_uso.dar_baixa(
                dados.codigo_medicamento,
                dados.quantidade,
                dados.lote,
                dados.motivo or ""
            )
            
            if not resultado['success']:
                db.rollback()
                raise HTTPException(status_code=400, detail=resultado['mensagem'])
            
            # Confirmar transação apenas se tudo deu certo
            db.commit()
            return resultado
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Erro ao processar baixa: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar baixa: {str(e)}")
