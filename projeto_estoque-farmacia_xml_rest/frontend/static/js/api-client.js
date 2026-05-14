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
        
        try {
            const opcoes = {
                method: metodo,
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (dados) {
                opcoes.body = JSON.stringify(dados);
            }

            const resposta = await Promise.race([
                fetch(url, opcoes),
                new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('Timeout na requisição')), this.timeout)
                )
            ]);

            if (!resposta.ok) {
                const erro = await resposta.json().catch(() => ({}));
                throw new Error(erro.detail || `HTTP ${resposta.status}`);
            }

            return await resposta.json();
        } catch (erro) {
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
            codigo_medicamento,
            quantidade,
            cpf_paciente
        };
        return await this.fazer_requisicao('/api/estoque/consultar', 'POST', dados);
    }

    async listar_lotes(codigo_medicamento) {
        return await this.fazer_requisicao(`/api/estoque/lotes/${codigo_medicamento}`);
    }

    // ==================== RESERVAS ====================

    async criar_reserva(codigo_medicamento, quantidade, lote, cpf_paciente) {
        const dados = {
            codigo_medicamento,
            quantidade,
            lote,
            cpf_paciente
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

    // ==================== BAIXAS ====================

    async dar_baixa(codigo_medicamento, quantidade, lote, motivo = '') {
        const dados = {
            codigo_medicamento,
            quantidade,
            lote,
            motivo
        };
        return await this.fazer_requisicao('/api/baixas', 'POST', dados);
    }
}

// Instância global
const api = new APIClient();
