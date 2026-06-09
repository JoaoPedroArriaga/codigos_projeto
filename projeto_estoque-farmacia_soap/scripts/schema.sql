-- =============================================
-- SISTEMA DE ESTOQUE E FARMÁCIA - GRUPO 3
-- BANCO DE DADOS POSTGRESQL
-- SCHEMA: projeto
-- VERSÃO SIMPLIFICADA (APENAS COLUNAS USADAS)
-- =============================================

-- Criar schema
CREATE SCHEMA IF NOT EXISTS projeto;

-- =============================================
-- 1. TABELAS DE CADASTRO
-- =============================================

-- Medicamentos
CREATE TABLE IF NOT EXISTS projeto.medicamentos (
    codigo NUMERIC(20) PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    concentracao VARCHAR(30),
    unidade VARCHAR(20) DEFAULT 'CAIXA',
    preco_venda NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lotes (estoque físico)
CREATE TABLE IF NOT EXISTS projeto.lotes (
    id_lote SERIAL PRIMARY KEY,
    codigo_medicamento NUMERIC(20) NOT NULL REFERENCES projeto.medicamentos(codigo) ON DELETE RESTRICT,
    numero_lote VARCHAR(30) NOT NULL,
    data_validade DATE NOT NULL,
    quantidade_inicial NUMERIC(6,3) NOT NULL,
    quantidade_atual NUMERIC(6,3) NOT NULL,
    preco_venda NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(codigo_medicamento, numero_lote)
);

-- =============================================
-- 2. TABELAS DE LOG (Histórico de processamento)
-- =============================================

-- Log das consultas recebidas do G2 (Laudos)
CREATE TABLE IF NOT EXISTS projeto.logs_consultas (
    id_log SERIAL PRIMARY KEY,
    arquivo_nome VARCHAR(100) NOT NULL,
    id_prescricao NUMERIC(30) NOT NULL,
    cpf_paciente NUMERIC(11) NOT NULL,
    codigo_medicamento NUMERIC(20) NOT NULL,
    quantidade NUMERIC(6,3) NOT NULL,
    disponivel BOOLEAN,
    observacao VARCHAR(200),
    data_recebimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log das reservas recebidas do G2 (Laudos)
CREATE TABLE IF NOT EXISTS projeto.logs_reservas (
    id_log SERIAL PRIMARY KEY,
    arquivo_nome VARCHAR(100) NOT NULL,
    id_prescricao NUMERIC(30) NOT NULL,
    cpf_paciente NUMERIC(11) NOT NULL,
    codigo_medicamento NUMERIC(20) NOT NULL,
    quantidade NUMERIC(6,3) NOT NULL,
    lote VARCHAR(30),
    id_lote INTEGER REFERENCES projeto.lotes(id_lote),
    status VARCHAR(20) DEFAULT 'PROCESSADO' CHECK (status IN ('PROCESSADO', 'ERRO')),
    observacao VARCHAR(200),
    data_recebimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log das baixas recebidas do G2 (Laudos)
CREATE TABLE IF NOT EXISTS projeto.logs_baixas (
    id_log SERIAL PRIMARY KEY,
    arquivo_nome VARCHAR(100) NOT NULL,
    id_prescricao NUMERIC(30) NOT NULL,
    cpf_paciente NUMERIC(11) NOT NULL,
    codigo_medicamento NUMERIC(20) NOT NULL,
    quantidade NUMERIC(6,3) NOT NULL,
    lote VARCHAR(30),
    data_uso NUMERIC(6),
    id_lote INTEGER REFERENCES projeto.lotes(id_lote),
    status VARCHAR(20) DEFAULT 'PROCESSADO' CHECK (status IN ('PROCESSADO', 'ERRO')),
    observacao VARCHAR(200),
    data_recebimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log dos consumos enviados para o G1 (Financeiro)
CREATE TABLE IF NOT EXISTS projeto.logs_consumos (
    id_log SERIAL PRIMARY KEY,
    arquivo_nome VARCHAR(100) NOT NULL,
    data_consumo DATE NOT NULL,
    total_itens INTEGER,
    total_valor NUMERIC(12,2),
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log de arquivos externos (status_financeiro, finalizacao)
CREATE TABLE IF NOT EXISTS projeto.logs_arquivos_externos (
    id_log SERIAL PRIMARY KEY,
    arquivo_nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(30) NOT NULL, -- 'STATUS_FINANCEIRO', 'FINALIZACAO'
    data_recebimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'RECEBIDO',
    observacao VARCHAR(500),
    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 3. TABELAS DE RESERVAS ATIVAS
-- =============================================

-- Reservas ativas (controle de reservas em andamento)
CREATE TABLE IF NOT EXISTS projeto.reservas_ativas (
    id_reserva SERIAL PRIMARY KEY,
    id_prescricao NUMERIC(30) NOT NULL,
    cpf_paciente NUMERIC(11) NOT NULL,
    codigo_medicamento NUMERIC(20) NOT NULL,
    quantidade NUMERIC(6,3) NOT NULL,
    lote VARCHAR(30) NOT NULL,
    id_lote INTEGER NOT NULL REFERENCES projeto.lotes(id_lote),
    status VARCHAR(20) DEFAULT 'RESERVADO' CHECK (status IN ('RESERVADO', 'UTILIZADO', 'CANCELADO')),
    data_reserva TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_utilizacao TIMESTAMP
);

-- =============================================
-- 4. TABELAS DE MOVIMENTAÇÃO E CONSUMO
-- =============================================

-- Movimentações de estoque (histórico completo)
CREATE TABLE IF NOT EXISTS projeto.movimentacoes (
    id_mov SERIAL PRIMARY KEY,
    id_lote INTEGER NOT NULL REFERENCES projeto.lotes(id_lote),
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('ENTRADA', 'RESERVA', 'BAIXA', 'AJUSTE')),
    quantidade NUMERIC(6,3) NOT NULL,
    quantidade_anterior NUMERIC(6,3) NOT NULL,
    quantidade_nova NUMERIC(6,3) NOT NULL,
    referencia_id INTEGER,
    referencia_tabela VARCHAR(30),
    data_mov TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario VARCHAR(50) DEFAULT 'SISTEMA'
);

-- Itens de consumo (consolidados para enviar ao G1)
CREATE TABLE IF NOT EXISTS projeto.itens_consumo (
    id_item SERIAL PRIMARY KEY,
    id_prescricao NUMERIC(30) NOT NULL,
    cpf_paciente NUMERIC(11) NOT NULL,
    codigo_medicamento NUMERIC(20) NOT NULL,
    quantidade NUMERIC(6,3) NOT NULL,
    preco_total NUMERIC(10,2) NOT NULL,
    data_uso NUMERIC(6) NOT NULL,
    lote VARCHAR(30) NOT NULL,
    unidade VARCHAR(20),
    id_lote INTEGER REFERENCES projeto.lotes(id_lote),
    id_baixa_log INTEGER REFERENCES projeto.logs_baixas(id_log),
    consolidado_em DATE DEFAULT CURRENT_DATE,
    enviado_para_g1 BOOLEAN DEFAULT FALSE,
    enviado_em TIMESTAMP
);

-- =============================================
-- 5. ÍNDICES PARA PERFORMANCE
-- =============================================

-- Índices lotes
CREATE INDEX IF NOT EXISTS idx_lotes_validade ON projeto.lotes(data_validade);
CREATE INDEX IF NOT EXISTS idx_lotes_medicamento ON projeto.lotes(codigo_medicamento);
CREATE INDEX IF NOT EXISTS idx_lotes_quantidade ON projeto.lotes(quantidade_atual);

-- Índices logs
CREATE INDEX IF NOT EXISTS idx_logs_consultas_data ON projeto.logs_consultas(data_recebimento);
CREATE INDEX IF NOT EXISTS idx_logs_reservas_data ON projeto.logs_reservas(data_recebimento);
CREATE INDEX IF NOT EXISTS idx_logs_baixas_data ON projeto.logs_baixas(data_recebimento);

-- Índices reservas ativas
CREATE INDEX IF NOT EXISTS idx_reservas_ativas_status ON projeto.reservas_ativas(status);
CREATE INDEX IF NOT EXISTS idx_reservas_ativas_prescricao ON projeto.reservas_ativas(id_prescricao);

-- Índices movimentações e consumo
CREATE INDEX IF NOT EXISTS idx_movimentacoes_data ON projeto.movimentacoes(data_mov);
CREATE INDEX IF NOT EXISTS idx_movimentacoes_lote ON projeto.movimentacoes(id_lote);
CREATE INDEX IF NOT EXISTS idx_itens_consumo_data ON projeto.itens_consumo(consolidado_em);
CREATE INDEX IF NOT EXISTS idx_itens_consumo_enviado ON projeto.itens_consumo(enviado_para_g1);

-- =============================================
-- 6. CONCESSÃO DE PERMISSÕES
-- =============================================

GRANT USAGE ON SCHEMA projeto TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA projeto TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA projeto TO postgres;