/**
 * App Principal - Lógica do frontend
 * Segue padrões: SOLID, DRY, KISS
 */

// ========================================
// UTILIDADES
// ========================================

const Util = {
    /**
     * Mostra mensagem de resultado
     */
    mostrarResultado(elementoId, tipo, titulo, mensagem, detalhes = null) {
        const elemento = document.getElementById(elementoId);
        elemento.className = `resultado show ${tipo}`;
        elemento.innerHTML = `
            <h3>${titulo}</h3>
            <p>${mensagem}</p>
            ${detalhes ? `<pre style="margin-top: 10px; overflow-x: auto;">${JSON.stringify(detalhes, null, 2)}</pre>` : ''}
        `;
        elemento.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    },

    /**
     * Formata data ISO para formato legível
     */
    formatarData(dataISO) {
        const data = new Date(dataISO);
        return data.toLocaleDateString('pt-BR', { year: 'numeric', month: '2-digit', day: '2-digit' });
    },

    /**
     * Formata moeda brasileira
     */
    formatarMoeda(valor) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    },

    /**
     * Limpa todos os formulários
     */
    limparFormularios() {
        document.querySelectorAll('form').forEach(form => form.reset());
    },

    /**
     * Esconde elemento de resultado
     */
    limparResultado(elementoId) {
        const elemento = document.getElementById(elementoId);
        elemento.className = 'resultado';
    }
};

// ========================================
// GERENCIADOR DE ABAS
// ========================================

const GerenciadorAbas = {
    init() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => this.mudarAba(btn.dataset.tab));
        });
    },

    mudarAba(nomeAba) {
        // Esconder todas as abas
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });

        // Remover class active de botões
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Mostrar aba selecionada
        document.getElementById(nomeAba).classList.add('active');
        document.querySelector(`[data-tab="${nomeAba}"]`).classList.add('active');

        // Limpar resultados ao trocar de aba
        Util.limparFormularios();
    }
};

// ========================================
// STATUS DA API
// ========================================

const StatusAPI = {
    async verificar() {
        const elemento = document.getElementById('api-status');
        
        try {
            const conectado = await api.verificar_conexao();
            
            if (conectado) {
                elemento.textContent = '✅ Conectado';
                elemento.className = 'status-connected';
            } else {
                throw new Error('Offline');
            }
        } catch (erro) {
            elemento.textContent = '❌ Desconectado';
            elemento.className = 'status-disconnected';
            console.error('Erro ao verificar API:', erro);
        }
    }
};

// ========================================
// MEDICAMENTOS
// ========================================

const Medicamentos = {
    async carregar() {
        try {
            const medicamentos = await api.listar_medicamentos();
            this.renderizar(medicamentos);
        } catch (erro) {
            Util.mostrarResultado('lista-medicamentos', 'error', 'Erro', 'Não foi possível carregar os medicamentos');
        }
    },

    renderizar(medicamentos) {
        const container = document.getElementById('lista-medicamentos');
        
        if (!medicamentos || medicamentos.length === 0) {
            container.innerHTML = '<p class="loading">Nenhum medicamento encontrado</p>';
            return;
        }

        container.innerHTML = medicamentos.map(med => `
            <div class="grid-item">
                <h3>💊 ${med.nome || 'N/A'}</h3>
                <p><strong>Código:</strong> ${med.codigo}</p>
                <p><strong>ID:</strong> ${med.id || 'N/A'}</p>
                <button class="btn btn-secondary" onclick="Medicamentos.consultarDetalhes(${med.codigo})">Ver Estoque</button>
            </div>
        `).join('');
    },

    async consultarDetalhes(codigo) {
        try {
            const estoque = await api.obter_estoque(codigo);
            const lotes = estoque.lotes.map(l => `
                <tr>
                    <td>${l.numero_lote}</td>
                    <td>${l.quantidade_atual}</td>
                    <td>${Util.formatarData(l.data_validade)}</td>
                    <td>${Util.formatarMoeda(l.preco_venda)}</td>
                </tr>
            `).join('');

            Util.mostrarResultado('lista-medicamentos', 'info', 'Estoque do Medicamento', '', {
                total: estoque.quantidade_total,
                detalhes: estoque
            });
        } catch (erro) {
            Util.mostrarResultado('lista-medicamentos', 'error', 'Erro', `Não foi possível carregar o estoque: ${erro.message}`);
        }
    }
};

// ========================================
// CONSULTAS
// ========================================

const Consultas = {
    init() {
        document.getElementById('form-consulta').addEventListener('submit', (e) => this.enviar(e));
    },

    async enviar(evento) {
        evento.preventDefault();

        const dados = {
            codigo_medicamento: parseInt(document.getElementById('consulta-codigo').value),
            quantidade: parseInt(document.getElementById('consulta-quantidade').value),
            cpf_paciente: document.getElementById('consulta-cpf').value
        };

        try {
            const resultado = await api.consultar_disponibilidade(
                dados.codigo_medicamento,
                dados.quantidade,
                dados.cpf_paciente
            );

            if (resultado.disponivel) {
                Util.mostrarResultado('resultado-consulta', 'success',
                    '✅ Medicamento Disponível',
                    `${resultado.mensagem}\nLote: ${resultado.lote}\nPreço: ${Util.formatarMoeda(resultado.preco)}`,
                    resultado
                );
            } else {
                Util.mostrarResultado('resultado-consulta', 'info',
                    '⚠️ Medicamento Indisponível',
                    resultado.mensagem,
                    resultado
                );
            }
        } catch (erro) {
            Util.mostrarResultado('resultado-consulta', 'error',
                '❌ Erro na Consulta',
                erro.message
            );
        }
    }
};

// ========================================
// RESERVAS
// ========================================

const Reservas = {
    init() {
        document.getElementById('form-reserva').addEventListener('submit', (e) => this.enviar(e));
    },

    async enviar(evento) {
        evento.preventDefault();

        const dados = {
            codigo_medicamento: parseInt(document.getElementById('reserva-codigo').value),
            quantidade: parseInt(document.getElementById('reserva-quantidade').value),
            lote: document.getElementById('reserva-lote').value,
            cpf_paciente: document.getElementById('reserva-cpf').value
        };

        try {
            const resultado = await api.criar_reserva(
                dados.codigo_medicamento,
                dados.quantidade,
                dados.lote,
                dados.cpf_paciente
            );

            if (resultado.success) {
                Util.mostrarResultado('resultado-reserva', 'success',
                    '✅ Reserva Criada com Sucesso',
                    `ID da Reserva: ${resultado.id_reserva}\n${resultado.mensagem}`,
                    resultado
                );
                document.getElementById('form-reserva').reset();
                await carregarReservasAtivas();
            } else {
                Util.mostrarResultado('resultado-reserva', 'error',
                    '❌ Erro ao Criar Reserva',
                    resultado.mensagem
                );
            }
        } catch (erro) {
            Util.mostrarResultado('resultado-reserva', 'error',
                '❌ Erro na Requisição',
                erro.message
            );
        }
    }
};

async function carregarReservasAtivas() {
    try {
        const resposta = await api.listar_reservas();
        const container = document.getElementById('lista-reservas');

        if (!resposta.reservas || resposta.reservas.length === 0) {
            container.innerHTML = '<p class="loading">Nenhuma reserva ativa</p>';
            return;
        }

        const tabela = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Medicamento</th>
                        <th>Quantidade</th>
                        <th>Lote</th>
                        <th>Paciente</th>
                        <th>Status</th>
                        <th>Ação</th>
                    </tr>
                </thead>
                <tbody>
                    ${resposta.reservas.map(res => `
                        <tr>
                            <td>${res.id_reserva}</td>
                            <td>${res.codigo_medicamento}</td>
                            <td>${res.quantidade}</td>
                            <td>${res.numero_lote}</td>
                            <td>${res.cpf_paciente}</td>
                            <td><span class="badge badge-success">${res.status}</span></td>
                            <td>
                                <button class="btn btn-danger" onclick="Reservas.cancelar(${res.id_reserva})">Cancelar</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        container.innerHTML = tabela;
    } catch (erro) {
        document.getElementById('lista-reservas').innerHTML = 
            `<p class="error">Erro ao carregar reservas: ${erro.message}</p>`;
    }
}

const Reservas_Extended = {
    async cancelar(id) {
        if (!confirm('Tem certeza que deseja cancelar esta reserva?')) return;

        try {
            const resultado = await api.cancelar_reserva(id);
            if (resultado.success) {
                alert('Reserva cancelada com sucesso!');
                await carregarReservasAtivas();
            } else {
                alert(`Erro: ${resultado.mensagem}`);
            }
        } catch (erro) {
            alert(`Erro ao cancelar: ${erro.message}`);
        }
    }
};

// Estender Reservas
Reservas.cancelar = Reservas_Extended.cancelar;

// ========================================
// BAIXAS
// ========================================

const Baixas = {
    init() {
        document.getElementById('form-baixa').addEventListener('submit', (e) => this.enviar(e));
    },

    async enviar(evento) {
        evento.preventDefault();

        const dados = {
            codigo_medicamento: parseInt(document.getElementById('baixa-codigo').value),
            quantidade: parseInt(document.getElementById('baixa-quantidade').value),
            lote: document.getElementById('baixa-lote').value,
            motivo: document.getElementById('baixa-motivo').value
        };

        try {
            const resultado = await api.dar_baixa(
                dados.codigo_medicamento,
                dados.quantidade,
                dados.lote,
                dados.motivo
            );

            if (resultado.success) {
                Util.mostrarResultado('resultado-baixa', 'success',
                    '✅ Baixa Registrada com Sucesso',
                    `${resultado.mensagem}\nQuantidade Restante: ${resultado.quantidade_restante}`,
                    resultado
                );
                document.getElementById('form-baixa').reset();
            } else {
                Util.mostrarResultado('resultado-baixa', 'error',
                    '❌ Erro ao Registrar Baixa',
                    resultado.mensagem
                );
            }
        } catch (erro) {
            Util.mostrarResultado('resultado-baixa', 'error',
                '❌ Erro na Requisição',
                erro.message
            );
        }
    }
};

// ========================================
// ESTOQUE
// ========================================

async function carregarEstoque() {
    const codigo = document.getElementById('estoque-codigo').value;

    if (!codigo) {
        alert('Por favor, digite um código de medicamento');
        return;
    }

    try {
        const estoque = await api.obter_estoque(parseInt(codigo));
        
        const lotes = estoque.lotes.map(l => `
            <tr>
                <td>${l.numero_lote}</td>
                <td>${l.quantidade_atual}</td>
                <td>${l.quantidade_inicial}</td>
                <td>${Util.formatarData(l.data_validade)}</td>
                <td>${Util.formatarMoeda(l.preco_venda)}</td>
            </tr>
        `).join('');

        const resultado = document.getElementById('resultado-estoque');
        resultado.className = 'resultado show info';
        resultado.innerHTML = `
            <h3>📊 Estoque do Medicamento ${codigo}</h3>
            <p><strong>Quantidade Total:</strong> ${estoque.quantidade_total} unidades</p>
            <table>
                <thead>
                    <tr>
                        <th>Lote</th>
                        <th>Quantidade Atual</th>
                        <th>Quantidade Inicial</th>
                        <th>Validade</th>
                        <th>Preço</th>
                    </tr>
                </thead>
                <tbody>
                    ${lotes}
                </tbody>
            </table>
        `;
    } catch (erro) {
        Util.mostrarResultado('resultado-estoque', 'error',
            'Erro ao Carregar Estoque',
            erro.message
        );
    }
}

// ========================================
// INICIALIZAÇÃO
// ========================================

document.addEventListener('DOMContentLoaded', async () => {
    // Verificar conexão com a API
    await StatusAPI.verificar();
    setInterval(() => StatusAPI.verificar(), 30000); // A cada 30 segundos

    // Inicializar componentes
    GerenciadorAbas.init();
    Consultas.init();
    Reservas.init();
    Baixas.init();

    // Carregar dados iniciais
    await Medicamentos.carregar();
    await carregarReservasAtivas();

    // Auto-refresh de reservas a cada 60 segundos
    setInterval(() => carregarReservasAtivas(), 60000);
});
