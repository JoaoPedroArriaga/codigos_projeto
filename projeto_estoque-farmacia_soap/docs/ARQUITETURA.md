# 🏗️ Arquitetura e Padrões de Código

## 📐 Princípios Arquiteturais

Este projeto segue os princípios SOLID, DRY, KISS e Clean Code.

### SOLID

#### 1. Single Responsibility Principle (SRP)
Cada classe tem uma única responsabilidade.

```python
# ✅ BOM - Classe com responsabilidade única
class RepositorioMedicamento:
    """Responsável apenas por acesso a dados de medicamentos"""
    def listar_todos(self):
        pass

class CasoDeUsoConsulta:
    """Responsável apenas pela lógica de consulta"""
    def processar_consulta(self, ...):
        pass

# ❌ RUIM - Classe com múltiplas responsabilidades
class GerenciadorCompleto:
    def listar_medicamentos(self):  # Responsabilidade 1
        pass
    def processar_consulta(self):   # Responsabilidade 2
        pass
    def salvar_banco(self):         # Responsabilidade 3
        pass
```

#### 2. Open/Closed Principle (OCP)
Aberto para extensão, fechado para modificação.

```python
# ✅ BOM - Fácil estender sem modificar
class RepositorioBase(ABC):
    @abstractmethod
    def listar_todos(self):
        pass

class RepositorioMedicamento(RepositorioBase):
    def listar_todos(self):
        # Implementação específica
        pass

# Fácil adicionar novo repositório sem modificar código existente
class RepositorioOutroTipo(RepositorioBase):
    def listar_todos(self):
        pass

# ❌ RUIM - Código quebra ao adicionar novo tipo
def listar_dados(tipo):
    if tipo == "medicamento":
        # código
    elif tipo == "reserva":
        # código
    elif tipo == "novo":  # MODIFICAR FUNÇÃO = RUIM
        # código
```

#### 3. Liskov Substitution Principle (LSP)
Subclasses devem ser substituíveis.

```python
# ✅ BOM - Toda subclasse pode substituir a classe-base
class API(ABC):
    @abstractmethod
    async def obter_dados(self):
        pass

class FastAPIImpl(API):
    async def obter_dados(self):
        # Implementação
        pass

class FlaskImpl(API):  # Pode ser usada no lugar de FastAPIImpl
    async def obter_dados(self):
        pass

# Usar: api = FastAPIImpl() # ou FlaskImpl() - FUNCIONA IGUAL
```

#### 4. Interface Segregation Principle (ISP)
Interfaces específicas, não genéricas demais.

```python
# ✅ BOM - Interfaces específicas
class Leitura(ABC):
    @abstractmethod
    def ler(self):
        pass

class Escrita(ABC):
    @abstractmethod
    def escrever(self):
        pass

class RepositorioCompleto(Leitura, Escrita):
    def ler(self):
        pass
    def escrever(self):
        pass

# Classes que só leem
class RepositorioSoLeitura(Leitura):
    def ler(self):
        pass

# ❌ RUIM - Interface genérica demais
class RepositorioGenerico(ABC):
    @abstractmethod
    def ler(self):
        pass
    @abstractmethod
    def escrever(self):
        pass
    @abstractmethod
    def deletar(self):
        pass
    # ... 20 mais métodos que não são usados por todos
```

#### 5. Dependency Inversion Principle (DIP)
Depender de abstrações, não de implementações concretas.

```python
# ✅ BOM - Depende de abstração
class CasoDeUsoConsulta:
    def __init__(self, repositorio: RepositorioBase):
        self.repositorio = repositorio  # Abstração!

# Fácil trocar implementação
consulta = CasoDeUsoConsulta(RepositorioMedicamento())
# ou
consulta = CasoDeUsoConsulta(RepositorioMedicamentoCache())

# ❌ RUIM - Depende de implementação concreta
class CasoDeUsoConsulta:
    def __init__(self):
        self.repositorio = RepositorioMedicamento()  # Concreto!
        # Não é possível trocar para RepositorioMedicamentoCache
```

### DRY (Don't Repeat Yourself)

```python
# ❌ RUIM - Código repetido
@router.post("/medicamentos")
async def criar_medicamento(dados):
    if not dados.codigo:
        raise HTTPException(status_code=400, detail="Código obrigatório")
    if not dados.nome:
        raise HTTPException(status_code=400, detail="Nome obrigatório")
    return {"success": True}

@router.post("/reservas")
async def criar_reserva(dados):
    if not dados.codigo:
        raise HTTPException(status_code=400, detail="Código obrigatório")
    if not dados.nome:
        raise HTTPException(status_code=400, detail="Nome obrigatório")
    return {"success": True}

# ✅ BOM - Código reutilizável
def validar_campos_obrigatorios(dados, campos):
    """Valida campos obrigatórios uma vez"""
    for campo in campos:
        if not getattr(dados, campo, None):
            raise HTTPException(
                status_code=400,
                detail=f"{campo} obrigatório"
            )

@router.post("/medicamentos")
async def criar_medicamento(dados):
    validar_campos_obrigatorios(dados, ["codigo", "nome"])
    return {"success": True}

@router.post("/reservas")
async def criar_reserva(dados):
    validar_campos_obrigatorios(dados, ["codigo", "nome"])
    return {"success": True}
```

### KISS (Keep It Simple, Stupid)

```python
# ❌ RUIM - Complexo demais
class ValidadorComplexo:
    def validar(self, cpf):
        padrao = r"^[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}$"
        if not re.match(padrao, cpf):
            algoritmo = [5,4,3,2,9,8,7,6,5,4,3,2]
            # ... 50 linhas de cálculo
            return resultado_complexo
        return False

# ✅ BOM - Simples e claro
class ValidadorCPF:
    def validar(self, cpf: str) -> bool:
        """Valida CPF simples - apenas check de formato"""
        return bool(re.match(r"^\d{11}$", cpf.replace(".", "").replace("-", "")))

# A validação complexa fica em outro serviço específico se necessário
class ValidadorCPFCompleto:
    def validar(self, cpf: str) -> bool:
        """Validação com dígitos verificadores (mais complexo, mas em arquivo separado)"""
        pass
```

### Clean Code

#### Nomes Claros

```python
# ❌ RUIM
def p(c, q):
    return db.execute(f"SELECT * FROM l WHERE cm = {c} AND qa >= {q}")

# ✅ BOM
def buscar_lote_disponivel(codigo_medicamento: int, quantidade: int):
    """Busca lote disponível respeitando FEFO"""
    return db.execute(
        """SELECT * FROM lotes 
           WHERE codigo_medicamento = %s AND quantidade_atual >= %s
           ORDER BY data_validade ASC LIMIT 1""",
        (codigo_medicamento, quantidade),
        fetch_one=True
    )
```

#### Funções Pequenas

```python
# ❌ RUIM - Função grande demais
def processar_tudo():
    # 200 linhas de código misturado
    pass

# ✅ BOM - Funções pequenas e focadas
def processar_consultas():
    """Processa consultas pendentes"""
    arquivos = listar_arquivos_entrada('consulta')
    for arquivo in arquivos:
        ConsultaProcessor.processar(arquivo)

def processar_reservas():
    """Processa reservas pendentes"""
    arquivos = listar_arquivos_entrada('reserva')
    for arquivo in arquivos:
        ReservaProcessor.processar(arquivo)

def processar_tudo():
    """Orquestra todo o processamento"""
    processar_consultas()
    processar_reservas()
    processar_baixas()
```

#### Type Hints

```python
# ❌ RUIM - Sem tipos
def criar_reserva(codigo, quantidade, lote, cpf):
    pass

# ✅ BOM - Com tipos claros
def criar_reserva(
    codigo: int,
    quantidade: int,
    lote: str,
    cpf: str
) -> Dict[str, Any]:
    """
    Cria uma nova reserva
    
    Args:
        codigo: Código do medicamento
        quantidade: Quantidade desejada
        lote: Número do lote
        cpf: CPF do paciente (11 dígitos)
    
    Returns:
        Dicionário com sucesso e ID da reserva
    """
    pass
```

#### Documentação

```python
# ✅ BOM - Documentação clara
class CasoDeUsoReserva:
    """Lógica de negócio para reservas de medicamentos.
    
    Responsável por:
    - Validar medicamento e lote
    - Verificar disponibilidade
    - Criar reserva no banco
    
    Segue FEFO (First Expiry First Out)
    """
    
    def criar_reserva(
        self,
        codigo_medicamento: int,
        quantidade: int,
        numero_lote: str,
        cpf_paciente: str
    ) -> Dict[str, Any]:
        """
        Cria uma reserva após validações completas.
        
        Validações:
        1. Medicamento existe
        2. Lote existe e não expirou
        3. Estoque suficiente
        
        Args:
            codigo_medicamento: ID do medicamento
            quantidade: Quantidade a reservar
            numero_lote: Número do lote específico
            cpf_paciente: CPF com 11 dígitos
        
        Returns:
            {
                'success': bool,
                'id_reserva': str,
                'mensagem': str,
                'timestamp': str
            }
        
        Raises:
            HTTPException: Se validações falharem
        
        Example:
            >>> reserva = caso.criar_reserva(789123, 5, "LOTE123", "12345678901")
            >>> print(reserva['id_reserva'])
            "abc123"
        """
        pass
```

## 🔄 Padrões de Projeto

### Repository Pattern

```
┌──────────────────┐
│  Use Cases       │
└────────┬─────────┘
         │ (Depende de)
┌────────▼─────────┐
│  Repository      │
│  (Abstrato)      │
└────────┬─────────┘
         │
    ┌────┴────┐
    │ diferentes implementações
    │
┌───▼────────────────────┐
│  RepositorioSQL        │
│  RepositorioCache      │
│  RepositorioAPI        │
└────────────────────────┘
```

### Use Case Pattern

```
┌──────────────────┐
│  Controller      │  (HTTP Request)
│  (API Endpoint)  │
└────────┬─────────┘
         │
┌────────▼──────────────────┐
│  Use Case / Caso de Uso    │  (Lógica de Negócio)
│  (ex: CasoDeUsoReserva)    │
└────────┬──────────────────┘
         │
         ├─────┬───────────┐
         │     │           │
    ┌────▼─┐ ┌─▼───┐  ┌───▼──┐
    │Repo1 │ │Repo2│  │Repo3 │  (Acesso a Dados)
    └──────┘ └─────┘  └──────┘
```

## 📊 Exemplos Completos

### Adicionar Novo Endpoint

1. **Schema (validação)** - `src/schemas.py`:

```python
class NovoSchema(BaseModel):
    campo1: str = Field(..., min_length=1)
    campo2: int = Field(..., gt=0)

class NovoResponseSchema(BaseModel):
    success: bool
    mensagem: str
```

2. **Repositório** - `src/repositorios.py`:

```python
class RepositorioNovo(RepositorioBase):
    def criar(self, dados):
        pass
```

3. **Caso de Uso** - `src/casos_de_uso.py`:

```python
class CasoDeUsoNovo:
    def processar(self, dados):
        # Lógica de negócio
        pass
```

4. **Rota** - `src/api/rotas_novo.py`:

```python
@router.post("")
async def criar(dados: NovoSchema):
    resultado = caso_de_uso.processar(dados)
    return resultado
```

5. **Registrar** - `src/api/app.py`:

```python
from src.api.rotas_novo import router as router_novo
app.include_router(router_novo)
```

## ✅ Checklist para Código de Qualidade

- [ ] Segue SOLID
- [ ] Não repete código (DRY)
- [ ] É simples de entender (KISS)
- [ ] Tem type hints
- [ ] Tem docstring
- [ ] Tem tratamento de erro
- [ ] Nomes são descritivos
- [ ] Funções são pequenas
- [ ] Testes passam
- [ ] Sem code smells
- [ ] Performance aceitável
- [ ] Segue convenções do projeto

## 🚀 Performance

### Database Queries

```python
# ❌ N+1 Problem
medicamentos = db.listar_todos()
for med in medicamentos:
    estoque = db.buscar_estoque(med.id)  # Query em loop!

# ✅ Usar JOIN
estoque = db.execute("""
    SELECT m.*, COUNT(l.id_lote) as total_lotes
    FROM medicamentos m
    LEFT JOIN lotes l ON m.codigo = l.codigo_medicamento
    GROUP BY m.id
""")
```

### Caching

```python
# ✅ Cache simples
from functools import lru_cache

@lru_cache(maxsize=128)
def obter_medicamento(codigo):
    return db.buscar_por_codigo(codigo)
```

### Índices

```sql
-- Sempre indexar chaves estrangeiras e campos frequentemente consultados
CREATE INDEX idx_lotes_medicamento ON lotes(codigo_medicamento);
CREATE INDEX idx_reservas_status ON reservas_ativas(status);
```

## 📚 Referências

- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Clean Code - Robert C. Martin](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
- [Design Patterns](https://refactoring.guru/design-patterns)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/deployment/concepts/#concepts)
