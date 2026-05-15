/**
 * Cliente da API - Abstração para chamadas à API REST
 * Segue o padrão DRY e KISS
 */

class APIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.timeout = 10000; // 10 segundos
    }

    /**
     * Faz uma requisição HTTP com tratamento de erro
     */
    async fazer_requisicao(caminho, metodo = 'GET', dados = null) {
        const url = `${this.baseURL}${caminho}`;
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        try {
            const opcoes = {
                method: metodo,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                signal: controller.signal
            };

            if (dados && (metodo === 'POST' || metodo === 'PUT')) {
                opcoes.body = JSON.stringify(dados);
            }

            const resposta = await fetch(url, opcoes);
            clearTimeout(timeoutId);

            if (!resposta.ok) {
                let erroMsg = `HTTP ${resposta.status}`;
                try {
                    const erro = await resposta.json();
                    erroMsg = erro.detail || erro.mensagem || erroMsg;
                } catch(e) {}
                throw new Error(erroMsg);
            }

            return await resposta.json();
        } catch (erro) {
            clearTimeout(timeoutId);
            if (erro.name === 'AbortError') {
                throw new Error('Timeout na requisição - servidor não respondeu');
            }
            console.error(`Erro na requisição ${metodo} ${url}:`, erro);
            throw erro;
        }
    }

    /**
     * Verifica conexão com a API
     */
    async verificar_conexao() {
        try {
            const resposta = await this.fazer_requisicao('/health');
            return resposta.status === 'healthy';
        } catch {
            return false;
        }
    }

    // ==================== MEDICAMENTOS ====================

    async listar_medicamentos() {
        return await this.fazer_requisicao('/api/medicamentos');
    }

    async obter_medicamento(codigo) {
        return await this.fazer_requisicao(`/api/medicamentos/${codigo}`);
    }

    // ==================== ESTOQUE ====================

    async obter_estoque(codigo_medicamento) {
        return await this.fazer_requisicao(`/api/estoque/${codigo_medicamento}`);
    }

    async consultar_disponibilidade(codigo_medicamento, quantidade, cpf_paciente) {
        const dados = {
            codigo_medicamento: parseInt(codigo_medicamento),
            quantidade: parseInt(quantidade),
            cpf_paciente: String(cpf_paciente).replace(/\D/g, '')
        };
        return await this.fazer_requisicao('/api/estoque/consultar', 'POST', dados);
    }

    async listar_lotes(codigo_medicamento) {
        return await this.fazer_requisicao(`/api/estoque/lotes/${codigo_medicamento}`);
    }

    // ==================== RESERVAS (FEFO - SEM LOTE MANUAL) ====================

    async criar_reserva(codigo_medicamento, quantidade, cpf_paciente) {
        /**
         * Cria uma reserva usando FEFO (First Expiry First Out)
         * O lote é automaticamente selecionado pelo sistema
         */
        const dados = {
            codigo_medicamento: parseInt(codigo_medicamento),
            quantidade: parseInt(quantidade),
            cpf_paciente: String(cpf_paciente).replace(/\D/g, '')
            // SEM o campo lote - o sistema decide qual lote usar via FEFO
        };
        return await this.fazer_requisicao('/api/reservas', 'POST', dados);
    }

    async listar_reservas() {
        return await this.fazer_requisicao('/api/reservas');
    }

    async obter_reserva(id_reserva) {
        return await this.fazer_requisicao(`/api/reservas/${id_reserva}`);
    }

    async cancelar_reserva(id_reserva) {
        return await this.fazer_requisicao(`/api/reservas/${id_reserva}`, 'DELETE');
    }

    async listar_lotes_disponiveis_fefo(codigo_medicamento) {
        return await this.fazer_requisicao(`/api/reservas/lotes-disponiveis/${codigo_medicamento}`);
    }

    // ==================== BAIXAS ====================

    async dar_baixa(codigo_medicamento, quantidade, lote, motivo = '') {
        const dados = {
            codigo_medicamento: parseInt(codigo_medicamento),
            quantidade: parseInt(quantidade),
            lote: String(lote).trim(),
            motivo: String(motivo).trim()
        };
        return await this.fazer_requisicao('/api/baixas', 'POST', dados);
    }
}

// Instância global
const api = new APIClient();