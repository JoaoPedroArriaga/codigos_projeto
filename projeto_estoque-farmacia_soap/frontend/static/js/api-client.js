/**
 * Cliente da API - Camada de abstração sobre SOAP
 * Mantém a mesma interface usada pelo app.js (compatível com o dashboard)
 */

class APIClient {
    constructor(baseURL = '') {
        this.soap = new SOAPClient(baseURL);
    }

    async verificar_conexao() {
        return await this.soap.verificarConexao();
    }

    // ==================== MEDICAMENTOS ====================

    async listar_medicamentos() {
        const dados = await this.soap.enviar('listarMedicamentos');
        const itens = dados?.iten || dados?.itens || [];
        return Array.isArray(itens) ? itens : [itens];
    }

    async obter_medicamento(codigo) {
        return await this.soap.enviar('obterMedicamento', { codigo: parseInt(codigo, 10) });
    }

    // ==================== ESTOQUE ====================

    async obter_estoque(codigo_medicamento) {
        const dados = await this.soap.enviar('obterEstoque', {
            codigo_medicamento: parseInt(codigo_medicamento, 10)
        });
        return {
            codigo_medicamento: dados.codigo_medicamento,
            quantidade_total: dados.quantidade_total,
            nome_medicamento: dados.nome_medicamento,
            lotes: this._normalizarLotes(dados.lote || dados.lotes || dados.iten)
        };
    }

    async consultar_disponibilidade(codigo_medicamento, quantidade, cpf_paciente) {
        const dados = await this.soap.enviar('consultarDisponibilidade', {
            codigo_medicamento: parseInt(codigo_medicamento, 10),
            quantidade: parseInt(quantidade, 10),
            cpf_paciente: String(cpf_paciente).replace(/\D/g, '')
        });

        const resposta = dados?.resposta || dados?.respostas;
        const primeira = Array.isArray(resposta) ? resposta[0] : resposta;

        return {
            codigo_medicamento: primeira?.codigo_medicamento,
            disponivel: primeira?.disponivel === 1 || primeira?.disponivel === '1',
            observacao: primeira?.observacao || ''
        };
    }

    async listar_lotes(codigo_medicamento) {
        const lotes = await this._listarLotesInterno(codigo_medicamento);
        return { lotes };
    }

    // ==================== RESERVAS ====================

    async criar_reserva(codigo_medicamento, quantidade, cpf_paciente) {
        const dados = await this.soap.enviar('criarReserva', {
            codigo_medicamento: parseInt(codigo_medicamento, 10),
            quantidade: parseInt(quantidade, 10),
            cpf_paciente: String(cpf_paciente).replace(/\D/g, '')
        });

        return {
            success: true,
            id_reserva: dados.id_reserva,
            lote_selecionado: dados.numero_lote,
            data_validade: dados.data_validade,
            preco: dados.preco,
            mensagem: `Reserva criada com sucesso! Lote ${dados.numero_lote} (FEFO)`
        };
    }

    async listar_reservas() {
        const dados = await this.soap.enviar('listarReservas');
        const itens = dados?.iten || dados?.itens || [];
        const lista = Array.isArray(itens) ? itens : (itens ? [itens] : []);

        return {
            total: lista.length,
            reservas: lista.map(r => ({
                id_reserva: r.id_reserva,
                codigo_medicamento: r.codigo_medicamento,
                quantidade: r.quantidade,
                lote: r.numero_lote,
                numero_lote: r.numero_lote,
                cpf_paciente: r.cpf_paciente,
                data_reserva: r.data_criacao || r.data_reserva,
                status: r.status
            }))
        };
    }

    async obter_reserva(id_reserva) {
        return await this.soap.enviar('obterReserva', { id_reserva: String(id_reserva) });
    }

    async cancelar_reserva(id_reserva) {
        const dados = await this.soap.enviar('cancelarReserva', { id_reserva: String(id_reserva) });
        return {
            success: dados.success === true || dados.success === 'true',
            mensagem: dados.mensagem || 'Reserva cancelada'
        };
    }

    async listar_lotes_disponiveis_fefo(codigo_medicamento) {
        const lotes = await this._listarLotesInterno(codigo_medicamento);
        const hoje = new Date();
        const disponiveis = lotes.filter(l => {
            const qtd = parseFloat(l.quantidade_atual);
            const validade = new Date(l.data_validade);
            return qtd > 0 && validade >= hoje;
        });

        return {
            codigo_medicamento: parseInt(codigo_medicamento, 10),
            total_lotes: disponiveis.length,
            lotes: disponiveis
        };
    }

    // ==================== BAIXAS ====================

    async dar_baixa(codigo_medicamento, quantidade, lote, motivo = '') {
        const dados = await this.soap.enviar('registrarBaixa', {
            codigo_medicamento: parseInt(codigo_medicamento, 10),
            quantidade: parseInt(quantidade, 10),
            numero_lote: String(lote).trim(),
            cpf_paciente: '00000000000',
            motivo: String(motivo).trim() || 'Baixa via dashboard SOAP'
        });

        return {
            success: true,
            mensagem: `Baixa de ${quantidade} unidades realizada com sucesso`,
            quantidade_restante: dados.quantidade_restante
        };
    }

    // ==================== HELPERS ====================

    _normalizarLotes(lotesRaw) {
        if (!lotesRaw) return [];
        const lista = Array.isArray(lotesRaw) ? lotesRaw : [lotesRaw];
        return lista.map(l => ({
            numero_lote: l.numero_lote,
            codigo_medicamento: l.codigo_medicamento,
            quantidade_atual: l.quantidade_atual,
            quantidade_inicial: l.quantidade_inicial,
            data_validade: l.data_validade,
            preco_venda: l.preco_venda
        }));
    }

    async _listarLotesInterno(codigo_medicamento) {
        const dados = await this.soap.enviar('listarLotes', {
            codigo_medicamento: parseInt(codigo_medicamento, 10)
        });
        return this._normalizarLotes(dados?.iten || dados?.lotes || dados?.lote);
    }
}

const api = new APIClient();
