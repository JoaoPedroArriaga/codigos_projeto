/**
 * App Principal - Lógica do frontend
 * Segue padrões: SOLID, DRY, KISS
 */

// ========================================
// UTILIDADES
// ========================================

const Util = {
    mostrarToast(mensagem, tipo = 'info') {
        const container = document.getElementById('toast-container') || (() => {
            const div = document.createElement('div');
            div.id = 'toast-container';
            div.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1000;';
            document.body.appendChild(div);
            return div;
        })();
        
        const toast = document.createElement('div');
        toast.className = `toast ${tipo}`;
        toast.textContent = mensagem;
        toast.style.cssText = `
            background: ${tipo === 'success' ? '#28a745' : tipo === 'error' ? '#dc3545' : '#17a2b8'};
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            margin-top: 10px;
            animation: slideIn 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    },

    mostrarResultado(elementoId, tipo, titulo, mensagem, detalhes = null) {
        const elemento = document.getElementById(elementoId);
        if (!elemento) return;
        
        elemento.className = `resultado show ${tipo}`;
        
        let conteudo = `<h3>${titulo}</h3>`;
        if (mensagem) conteudo += `<p>${mensagem}</p>`;
        
        if (detalhes) {
            if (Array.isArray(detalhes)) {
                conteudo += this.renderizarTabela(detalhes);
            } else if (detalhes.lotes) {
                conteudo += `<div class="card-info"><p><strong>Total:</strong> ${detalhes.quantidade_total} unidades</p></div>`;
                conteudo += this.renderizarTabelaLotes(detalhes.lotes);
            } else if (detalhes.disponivel !== undefined) {
                conteudo += `<div class="card-result">
                    <p><strong>Código:</strong> ${detalhes.codigo_medicamento}</p>
                    <p><strong>Disponível:</strong> ${detalhes.disponivel ? '✅ SIM' : '❌ NÃO'}</p>
                    ${detalhes.lote ? `<p><strong>Lote:</strong> ${detalhes.lote}</p>` : ''}
                    ${detalhes.validade ? `<p><strong>Validade:</strong> ${this.formatarData(detalhes.validade)}</p>` : ''}
                    ${detalhes.preco !== undefined ? `<p><strong>Preço:</strong> ${this.formatarMoeda(detalhes.preco)}</p>` : ''}
                    <p><em>${detalhes.mensagem || ''}</em></p>
                </div>`;
            } else if (detalhes.id_reserva) {
                conteudo += `<div class="card-result">
                    <p><strong>ID Reserva:</strong> ${detalhes.id_reserva}</p>
                    <p><strong>Código:</strong> ${detalhes.codigo_medicamento}</p>
                    <p><strong>Quantidade:</strong> ${detalhes.quantidade}</p>
                    <p><strong>Lote Selecionado:</strong> ${detalhes.lote_selecionado || 'N/A'}</p>
                    <p><strong>Data:</strong> ${this.formatarData(detalhes.timestamp)}</p>
                </div>`;
            } else {
                conteudo += this.renderizarCard(detalhes);
            }
        }
        
        elemento.innerHTML = conteudo;
        elemento.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        if (tipo === 'success') {
            setTimeout(() => {
                if (elemento) elemento.className = 'resultado';
            }, 10000);
        }
    },

    renderizarTabela(dados) {
        if (!dados || dados.length === 0) return '<p>Nenhum dado disponível</p>';
        
        const colunas = Object.keys(dados[0]);
        let html = '<div class="tabela-wrapper"><table class="tabela-resultado"><thead><tr>';
        colunas.forEach(col => {
            html += `<th>${this.formatarColunaHeader(col)}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        dados.forEach(linha => {
            html += '<tr>';
            colunas.forEach(col => {
                let valor = linha[col];
                if (col.includes('data') && valor) valor = this.formatarData(valor);
                if ((col.includes('preco') || col.includes('valor')) && typeof valor === 'number') valor = this.formatarMoeda(valor);
                html += `<td>${valor ?? '-'}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        return html;
    },

    renderizarTabelaLotes(lotes) {
        if (!lotes || lotes.length === 0) return '';
        
        let html = '<div class="tabela-wrapper"><table class="tabela-resultado"><thead><tr>';
        html += '<th>Lote</th><th>Quantidade Atual</th><th>Quantidade Inicial</th><th>Validade</th><th>Preço</th>';
        html += '</tr></thead><tbody>';
        
        lotes.forEach(lote => {
            html += '<tr>';
            html += `<td><strong>${lote.numero_lote || lote.lote}</strong></td>`;
            html += `<td>${lote.quantidade_atual}</td>`;
            html += `<td>${lote.quantidade_inicial || '-'}</td>`;
            html += `<td>${this.formatarData(lote.data_validade || lote.validade)}</td>`;
            html += `<td>${this.formatarMoeda(lote.preco_venda || lote.preco)}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        return html;
    },

    renderizarCard(objeto) {
        let html = '<div class="card-result">';
        Object.entries(objeto).forEach(([chave, valor]) => {
            if (typeof valor === 'object') return;
            let valorFormatado = valor;
            if (chave.includes('data')) valorFormatado = this.formatarData(valor);
            if (chave.includes('preco') || chave.includes('valor')) valorFormatado = this.formatarMoeda(valor);
            const label = this.formatarColunaHeader(chave);
            html += `<p><strong>${label}:</strong> ${valorFormatado}</p>`;
        });
        html += '</div>';
        return html;
    },

    formatarColunaHeader(coluna) {
        return coluna
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase())
            .trim();
    },

    formatarData(dataISO) {
        if (!dataISO) return 'N/A';
        try {
            const data = new Date(dataISO);
            if (isNaN(data.getTime())) return dataISO;
            return data.toLocaleDateString('pt-BR');
        } catch(e) {
            return dataISO;
        }
    },

    formatarMoeda(valor) {
        if (valor === undefined || valor === null) return 'N/A';
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    },

    limparResultado(elementoId) {
        const elemento = document.getElementById(elementoId);
        if (elemento) elemento.className = 'resultado';
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
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const tabAtiva = document.getElementById(nomeAba);
        if (tabAtiva) tabAtiva.classList.add('active');
        
        const btnAtivo = document.querySelector(`[data-tab="${nomeAba}"]`);
        if (btnAtivo) btnAtivo.classList.add('active');
    }
};

// ========================================
// STATUS DA API
// ========================================

const StatusAPI = {
    async verificar() {
        const elemento = document.getElementById('api-status');
        if (!elemento) return;
        
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
        const container = document.getElementById('lista-medicamentos');
        if (!container) return;
        
        try {
            const medicamentos = await api.listar_medicamentos();
            this.renderizar(medicamentos);
        } catch (erro) {
            container.innerHTML = '<p class="error">Erro ao carregar medicamentos</p>';
            Util.mostrarToast('Erro ao carregar medicamentos', 'error');
        }
    },

    renderizar(medicamentos) {
        const container = document.getElementById('lista-medicamentos');
        if (!container) return;
        
        if (!medicamentos || medicamentos.length === 0) {
            container.innerHTML = '<p class="loading">Nenhum medicamento encontrado</p>';
            return;
        }

        container.innerHTML = medicamentos.map(med => `
            <div class="grid-item" data-codigo="${med.codigo}" data-nome="${med.nome}">
                <h3>💊 ${med.nome || 'N/A'}</h3>
                <p><strong>Código:</strong> ${med.codigo}</p>
                <button class="btn btn-secondary btn-sm" onclick="Medicamentos.verDetalhes(${med.codigo}, '${med.nome}')">Ver Estoque</button>
            </div>
        `).join('');
    },

    async verDetalhes(codigo, nome) {
        const container = document.getElementById('lista-medicamentos');
        if (!container) return;
        
        this.ultimaBusca = {
            codigo: codigo,
            nome: nome,
            htmlOriginal: container.innerHTML
        };
        
        try {
            const estoque = await api.obter_estoque(codigo);
            
            let html = `
                <div style="margin-bottom: 20px;">
                    <button class="btn btn-secondary btn-sm" onclick="Medicamentos.voltar()">
                        ⬅️ Voltar para lista de medicamentos
                    </button>
                </div>
                <h3>📊 Estoque do Medicamento: ${nome} (Código: ${codigo})</h3>
                <div class="card-info">
                    <p><strong>Quantidade Total em Estoque:</strong> ${estoque.quantidade_total} unidades</p>
                </div>
            `;
            
            if (estoque.lotes && estoque.lotes.length > 0) {
                html += `
                    <div class="tabela-wrapper">
                        <table class="tabela-resultado">
                            <thead>
                                <tr>
                                    <th>Número do Lote</th>
                                    <th>Quantidade Atual</th>
                                    <th>Quantidade Inicial</th>
                                    <th>Data de Validade</th>
                                    <th>Preço de Venda</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${estoque.lotes.map(lote => {
                                    const vencido = new Date(lote.data_validade) < new Date();
                                    return `
                                    <tr>
                                        <td><strong>${lote.numero_lote}</strong></td>
                                        <td>${lote.quantidade_atual}</td>
                                        <td>${lote.quantidade_inicial || '-'}</td>
                                        <td>${Util.formatarData(lote.data_validade)} ${vencido ? '⚠️ VENCIDO' : ''}</td>
                                        <td>${Util.formatarMoeda(lote.preco_venda)}</td>
                                        <td>${vencido ? '<span class="badge badge-danger">Vencido</span>' : '<span class="badge badge-success">Válido</span>'}</td>
                                    </tr>
                                `}).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            } else {
                html += '<p class="loading">Nenhum lote cadastrado para este medicamento</p>';
            }
            
            // Adicionar botão para ver reservas deste medicamento
            html += `
                <div style="margin-top: 20px; display: flex; gap: 10px;">
                    <button class="btn btn-primary btn-sm" onclick="Medicamentos.verReservasPorMedicamento(${codigo}, '${nome}')">
                        📋 Ver Reservas deste Medicamento
                    </button>
                    <button class="btn btn-success btn-sm" onclick="GerenciadorAbas.mudarAba('reservas'); document.getElementById('reserva-codigo').value = ${codigo}">
                        ➕ Nova Reserva
                    </button>
                </div>
            `;
            
            container.innerHTML = html;
            
        } catch (erro) {
            container.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <button class="btn btn-secondary btn-sm" onclick="Medicamentos.voltar()">
                        ⬅️ Voltar para lista de medicamentos
                    </button>
                </div>
                <div class="resultado show error">
                    <h3>❌ Erro ao carregar estoque</h3>
                    <p>${erro.message}</p>
                </div>
            `;
            Util.mostrarToast(`Erro ao carregar detalhes: ${erro.message}`, 'error');
        }
    },
    
    voltar() {
        const container = document.getElementById('lista-medicamentos');
        if (!container) return;
        
        if (this.ultimaBusca && this.ultimaBusca.htmlOriginal) {
            container.innerHTML = this.ultimaBusca.htmlOriginal;
            this.ultimaBusca = null;
        } else {
            // Recarregar a lista original
            this.carregar();
        }
    },
    
    async verReservasPorMedicamento(codigo, nome) {
        try {
            const resposta = await api.listar_reservas();
            const todasReservas = resposta.reservas || [];
            const reservasDoMedicamento = todasReservas.filter(r => r.codigo_medicamento === codigo);
            
            if (reservasDoMedicamento.length === 0) {
                Util.mostrarToast(`Nenhuma reserva encontrada para ${nome}`, 'info');
                return;
            }
            
            let html = `
                <div style="margin-bottom: 20px;">
                    <button class="btn btn-secondary btn-sm" onclick="Medicamentos.verDetalhes(${codigo}, '${nome}')">
                        ⬅️ Voltar para estoque
                    </button>
                </div>
                <h3>📋 Reservas do Medicamento: ${nome}</h3>
                <div class="tabela-wrapper">
                    <table class="tabela-resultado">
                        <thead>
                            <tr>
                                <th>ID Reserva</th>
                                <th>Quantidade</th>
                                <th>Lote</th>
                                <th>Paciente</th>
                                <th>Data</th>
                                <th>Status</th>
                                <th>Ação</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${reservasDoMedicamento.map(res => `
                                <tr>
                                    <td>${res.id_reserva}</td>
                                    <td>${res.quantidade}</td>
                                    <td>${res.lote || res.numero_lote || '-'}</td>
                                    <td>${res.cpf_paciente}</td>
                                    <td>${Util.formatarData(res.data_reserva)}</td>
                                    <td><span class="badge ${res.status === 'ativa' ? 'badge-success' : 'badge-warning'}">${res.status}</span></td>
                                    <td>${res.status === 'ativa' ? `<button class="btn btn-danger btn-sm" onclick="Reservas.cancelar(${res.id_reserva})">Cancelar</button>` : '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
            
            const container = document.getElementById('lista-medicamentos');
            if (container) container.innerHTML = html;
            
        } catch (erro) {
            Util.mostrarToast(`Erro ao carregar reservas: ${erro.message}`, 'error');
        }
    },

    filtrar() {
        const filtro = document.getElementById('filtro-medicamento')?.value.toLowerCase() || '';
        const items = document.querySelectorAll('#lista-medicamentos .grid-item');
        
        items.forEach(item => {
            const nome = item.dataset.nome?.toLowerCase() || '';
            const codigo = item.dataset.codigo?.toString() || '';
            if (nome.includes(filtro) || codigo.includes(filtro)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }
};

// ========================================
// CONSULTAS
// ========================================

const Consultas = {
    init() {
        const form = document.getElementById('form-consulta');
        if (form) form.addEventListener('submit', (e) => this.enviar(e));
    },

    async enviar(evento) {
        evento.preventDefault();

        const codigo = document.getElementById('consulta-codigo')?.value;
        const quantidade = document.getElementById('consulta-quantidade')?.value;
        const cpf = document.getElementById('consulta-cpf')?.value;

        if (!codigo || !quantidade || !cpf) {
            Util.mostrarResultado('resultado-consulta', 'error', 'Erro', 'Preencha todos os campos');
            return;
        }

        try {
            const resultado = await api.consultar_disponibilidade(codigo, quantidade, cpf);
            
            if (resultado.disponivel) {
                Util.mostrarResultado('resultado-consulta', 'success',
                    '✅ Medicamento Disponível',
                    resultado.mensagem,
                    resultado
                );
                Util.mostrarToast('Medicamento disponível!', 'success');
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
            Util.mostrarToast(`Erro: ${erro.message}`, 'error');
        }
    }
};

// ========================================
// RESERVAS (FEFO - SEM CAMPO LOTE MANUAL)
// ========================================

const Reservas = {
    init() {
        const form = document.getElementById('form-reserva');
        if (form) form.addEventListener('submit', (e) => this.enviar(e));
    },

    async enviar(evento) {
        evento.preventDefault();

        const codigo = document.getElementById('reserva-codigo')?.value;
        const quantidade = document.getElementById('reserva-quantidade')?.value;
        const cpf = document.getElementById('reserva-cpf')?.value;

        if (!codigo || !quantidade || !cpf) {
            Util.mostrarResultado('resultado-reserva', 'error', 'Erro', 'Preencha todos os campos');
            return;
        }

        const btnSubmit = evento.target.querySelector('button[type="submit"]');
        const textoOriginal = btnSubmit?.textContent;
        if (btnSubmit) btnSubmit.textContent = '⏳ Processando reserva com FEFO...';

        try {
            const resultado = await api.criar_reserva(codigo, quantidade, cpf);

            if (btnSubmit) btnSubmit.textContent = textoOriginal;

            if (resultado.success) {
                Util.mostrarResultado('resultado-reserva', 'success',
                    '✅ Reserva Criada com Sucesso (FEFO)',
                    `<strong>ID da Reserva:</strong> ${resultado.id_reserva}<br>
                     <strong>Lote Selecionado:</strong> ${resultado.lote_selecionado}<br>
                     <strong>Data de Validade:</strong> ${Util.formatarData(resultado.data_validade)}<br>
                     <strong>Preço Unitário:</strong> ${Util.formatarMoeda(resultado.preco)}<br>
                     <strong>Status:</strong> Ativa<br><br>
                     ${resultado.mensagem}`,
                    resultado
                );
                document.getElementById('form-reserva')?.reset();
                await carregarReservasAtivas();
                Util.mostrarToast(`Reserva criada! Lote: ${resultado.lote_selecionado} (FEFO)`, 'success');
            } else {
                Util.mostrarResultado('resultado-reserva', 'error',
                    '❌ Erro ao Criar Reserva',
                    resultado.mensagem
                );
                Util.mostrarToast(`Erro: ${resultado.mensagem}`, 'error');
            }
        } catch (erro) {
            if (btnSubmit) btnSubmit.textContent = textoOriginal;
            Util.mostrarResultado('resultado-reserva', 'error',
                '❌ Erro na Requisição',
                erro.message
            );
            Util.mostrarToast(`Erro: ${erro.message}`, 'error');
        }
    },

    async cancelar(id) {
        if (!confirm('Tem certeza que deseja cancelar esta reserva?')) return;

        try {
            const resultado = await api.cancelar_reserva(id);
            if (resultado.success) {
                Util.mostrarToast('Reserva cancelada com sucesso!', 'success');
                await carregarReservasAtivas();
            } else {
                Util.mostrarToast(`Erro: ${resultado.mensagem}`, 'error');
            }
        } catch (erro) {
            Util.mostrarToast(`Erro ao cancelar: ${erro.message}`, 'error');
        }
    },

    async verificarLotesDisponiveis(codigo) {
        if (!codigo) {
            Util.mostrarToast('Digite um código de medicamento', 'warning');
            return;
        }

        try {
            const resultado = await api.listar_lotes_disponiveis_fefo(parseInt(codigo));
            
            if (resultado.lotes && resultado.lotes.length > 0) {
                let mensagem = `📦 Lotes disponíveis para o medicamento ${codigo} (FEFO):\n`;
                resultado.lotes.forEach((lote, idx) => {
                    mensagem += `${idx + 1}. Lote ${lote.numero_lote} - ${lote.quantidade_atual} unidades - Vence: ${Util.formatarData(lote.data_validade)}\n`;
                });
                alert(mensagem);
            } else {
                Util.mostrarToast(`Nenhum lote disponível para o medicamento ${codigo}`, 'warning');
            }
        } catch (erro) {
            Util.mostrarToast(`Erro: ${erro.message}`, 'error');
        }
    }
};

// ========================================
// FUNÇÃO PRÉ-RESERVA (FEFO)
// ========================================

async function verificarPreReserva() {
    const codigo = document.getElementById('preconsulta-codigo')?.value;
    const quantidade = document.getElementById('preconsulta-quantidade')?.value;
    
    if (!codigo || !quantidade) {
        Util.mostrarToast('Digite código e quantidade', 'warning');
        return;
    }
    
    try {
        const resultado = await api.consultar_disponibilidade(codigo, quantidade, '00000000000');
        
        const container = document.getElementById('preconsulta-resultado');
        if (container) {
            if (resultado.disponivel) {
                container.className = 'resultado show success';
                container.innerHTML = `
                    <h3>✅ Disponível para Reserva (FEFO)</h3>
                    <div class="card-result">
                        <p><strong>Lote sugerido:</strong> ${resultado.lote}</p>
                        <p><strong>Validade:</strong> ${Util.formatarData(resultado.validade)}</p>
                        <p><strong>Preço:</strong> ${Util.formatarMoeda(resultado.preco)}</p>
                        <p><strong>Quantidade disponível no lote:</strong> ${resultado.quantidade_disponivel || 'N/A'}</p>
                    </div>
                    <p><em>✅ O sistema reservará automaticamente este lote (menor data de validade - FEFO)</em></p>
                    <button class="btn btn-primary btn-sm mt" onclick="document.getElementById('reserva-codigo').value = ${codigo}; document.getElementById('reserva-quantidade').value = ${quantidade}; GerenciadorAbas.mudarAba('reservas')">
                        🔄 Ir para Reserva
                    </button>
                `;
                Util.mostrarToast(`Disponível! Lote: ${resultado.lote}`, 'success');
            } else {
                container.className = 'resultado show info';
                container.innerHTML = `
                    <h3>⚠️ Indisponível</h3>
                    <p>${resultado.mensagem}</p>
                    <p><em>Não é possível reservar no momento. Estoque insuficiente.</em></p>
                `;
                Util.mostrarToast('Medicamento indisponível para esta quantidade', 'warning');
            }
        }
    } catch (erro) {
        Util.mostrarToast(`Erro: ${erro.message}`, 'error');
    }
}

// ========================================
// CARREGAR RESERVAS ATIVAS
// ========================================

async function carregarReservasAtivas() {
    const container = document.getElementById('lista-reservas');
    const totalSpan = document.getElementById('total-reservas');
    if (!container) return;

    try {
        const resposta = await api.listar_reservas();
        const reservas = resposta.reservas || [];

        if (totalSpan) totalSpan.textContent = `${reservas.length} reservas`;

        if (reservas.length === 0) {
            container.innerHTML = '<p class="loading">Nenhuma reserva ativa</p>';
            return;
        }

        const tabela = `
            <table class="tabela-resultado">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Medicamento</th>
                        <th>Quantidade</th>
                        <th>Lote (FEFO)</th>
                        <th>Paciente</th>
                        <th>Data Reserva</th>
                        <th>Status</th>
                        <th>Ação</th>
                    </tr>
                </thead>
                <tbody>
                    ${reservas.map(res => `
                        <tr>
                            <td>${res.id_reserva}</td>
                            <td>${res.codigo_medicamento}</td>
                            <td>${res.quantidade}</td>
                            <td><strong>${res.lote || res.numero_lote || '-'}</strong></td>
                            <td>${res.cpf_paciente}</td>
                            <td>${Util.formatarData(res.data_reserva)}</td>
                            <td><span class="badge badge-success">${res.status === 'ativa' ? 'ATIVA' : res.status}</span></td>
                            <td><button class="btn btn-danger btn-sm" onclick="Reservas.cancelar(${res.id_reserva})">Cancelar</button></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        container.innerHTML = tabela;
    } catch (erro) {
        container.innerHTML = `<p class="error">Erro ao carregar reservas: ${erro.message}</p>`;
        Util.mostrarToast('Erro ao carregar reservas', 'error');
    }
}

// ========================================
// BAIXAS
// ========================================

const Baixas = {
    init() {
        const form = document.getElementById('form-baixa');
        if (form) form.addEventListener('submit', (e) => this.enviar(e));
    },

    async enviar(evento) {
        evento.preventDefault();

        const codigo = document.getElementById('baixa-codigo')?.value;
        const quantidade = document.getElementById('baixa-quantidade')?.value;
        const lote = document.getElementById('baixa-lote')?.value;
        const motivo = document.getElementById('baixa-motivo')?.value || '';

        if (!codigo || !quantidade || !lote) {
            Util.mostrarResultado('resultado-baixa', 'error', 'Erro', 'Preencha os campos obrigatórios');
            return;
        }

        try {
            const resultado = await api.dar_baixa(codigo, quantidade, lote, motivo);

            if (resultado.success) {
                Util.mostrarResultado('resultado-baixa', 'success',
                    '✅ Baixa Registrada com Sucesso',
                    `${resultado.mensagem}<br>Quantidade Restante: ${resultado.quantidade_restante}`,
                    resultado
                );
                document.getElementById('form-baixa')?.reset();
                Util.mostrarToast('Baixa registrada com sucesso!', 'success');
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
            Util.mostrarToast(`Erro: ${erro.message}`, 'error');
        }
    }
};

// ========================================
// ESTOQUE
// ========================================

async function carregarEstoque() {
    const codigo = document.getElementById('estoque-codigo')?.value;
    if (!codigo) {
        Util.mostrarToast('Digite um código de medicamento', 'warning');
        return;
    }

    try {
        const estoque = await api.obter_estoque(parseInt(codigo));
        
        const html = `
            <h3>📊 Estoque do Medicamento ${codigo}</h3>
            <div class="card-info">
                <p><strong>Quantidade Total:</strong> ${estoque.quantidade_total} unidades</p>
            </div>
            <div class="tabela-wrapper">
                <table class="tabela-resultado">
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
                        ${(estoque.lotes || []).map(l => `
                            <tr>
                                <td><strong>${l.numero_lote}</strong></td>
                                <td>${l.quantidade_atual}</td>
                                <td>${l.quantidade_inicial || '-'}</td>
                                <td>${Util.formatarData(l.data_validade)}</td>
                                <td>${Util.formatarMoeda(l.preco_venda)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        const resultado = document.getElementById('resultado-estoque');
        if (resultado) {
            resultado.className = 'resultado show info';
            resultado.innerHTML = html;
        }
        Util.mostrarToast(`Estoque carregado: ${estoque.quantidade_total} unidades`, 'info');
    } catch (erro) {
        Util.mostrarResultado('resultado-estoque', 'error',
            'Erro ao Carregar Estoque',
            erro.message
        );
        Util.mostrarToast(`Erro: ${erro.message}`, 'error');
    }
}

// ========================================
// ESTATÍSTICAS
// ========================================

async function carregarEstatisticas() {
    try {
        const medicamentos = await api.listar_medicamentos();
        const totalMedElement = document.getElementById('total-medicamentos');
        if (totalMedElement) totalMedElement.textContent = medicamentos.length || 0;
        
        const reservas = await api.listar_reservas();
        const totalResElement = document.getElementById('total-reservas-stats');
        if (totalResElement) totalResElement.textContent = reservas.reservas?.length || 0;
        
        let totalEstoque = 0;
        for (const med of medicamentos) {
            try {
                const estoque = await api.obter_estoque(med.codigo);
                totalEstoque += estoque.quantidade_total || 0;
            } catch(e) {}
        }
        const totalEstElement = document.getElementById('total-estoque');
        if (totalEstElement) totalEstElement.textContent = totalEstoque;
    } catch(e) {
        console.error('Erro ao carregar estatísticas:', e);
    }
}

// ========================================
// RELATÓRIO DE CONSUMO
// ========================================

async function carregarRelatorioConsumo() {
    const dataInicio = document.getElementById('data-inicio')?.value;
    const dataFim = document.getElementById('data-fim')?.value;
    
    if (!dataInicio || !dataFim) {
        Util.mostrarToast('Selecione as datas de início e fim', 'warning');
        return;
    }
    
    const container = document.getElementById('relatorio-consumo');
    if (!container) return;
    
    container.innerHTML = '<p class="loading">Carregando relatório...</p>';
    
    try {
        const reservas = await api.listar_reservas();
        const reservasAtivas = reservas.reservas || [];
        
        if (reservasAtivas.length === 0) {
            container.innerHTML = '<p>Nenhum consumo registrado no período</p>';
            return;
        }
        
        let html = '<div class="tabela-wrapper"><table class="tabela-resultado"><thead><tr>';
        html += '<th>ID Reserva</th><th>Medicamento</th><th>Quantidade</th><th>Paciente</th><th>Data</th><th>Status</th>';
        html += '</tr></thead><tbody>';
        
        for (const res of reservasAtivas) {
            const data = new Date(res.data_reserva).toLocaleDateString('pt-BR');
            html += `<tr>
                <td>${res.id_reserva}</td>
                <td>${res.codigo_medicamento}</td>
                <td>${res.quantidade}</td>
                <td>${res.cpf_paciente}</td>
                <td>${data}</td>
                <td><span class="badge badge-success">${res.status}</span></td>
            </tr>`;
        }
        
        html += '</tbody></table></div>';
        container.innerHTML = html;
        
    } catch(e) {
        container.innerHTML = `<p class="error">Erro ao carregar relatório: ${e.message}</p>`;
        Util.mostrarToast('Erro ao carregar relatório', 'error');
    }
}

// ========================================
// LOGS
// ========================================

async function carregarLogs() {
    const tipo = document.getElementById('log-tipo')?.value || 'consultas';
    const container = document.getElementById('logs-content');
    if (!container) return;
    
    container.innerHTML = '<p class="loading">Carregando logs...</p>';
    
    try {
        const logs = [
            { id: 1, data: new Date().toISOString(), mensagem: `Log de ${tipo} - Processado com sucesso`, status: 'SUCESSO' },
            { id: 2, data: new Date(Date.now() - 3600000).toISOString(), mensagem: `Log de ${tipo} - Arquivo validado`, status: 'SUCESSO' },
            { id: 3, data: new Date(Date.now() - 7200000).toISOString(), mensagem: `Log de ${tipo} - XML processado`, status: 'SUCESSO' },
        ];
        
        let html = '<div class="tabela-wrapper"><table class="tabela-resultado"><thead><tr>';
        html += '<th>ID</th><th>Data/Hora</th><th>Mensagem</th><th>Status</th>';
        html += '</tr></thead><tbody>';
        
        for (const log of logs) {
            const data = new Date(log.data).toLocaleString('pt-BR');
            html += `<tr>
                <td>${log.id}</td>
                <td>${data}</td>
                <td>${log.mensagem}</td>
                <td><span class="badge badge-success">${log.status}</span></td>
            </tr>`;
        }
        
        html += '</tbody></table></div>';
        container.innerHTML = html;
        
    } catch(e) {
        container.innerHTML = `<p class="error">Erro ao carregar logs: ${e.message}</p>`;
        Util.mostrarToast('Erro ao carregar logs', 'error');
    }
}

// ========================================
// TOAST E MODAL (FUNÇÕES GLOBAIS)
// ========================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || (() => {
        const div = document.createElement('div');
        div.id = 'toast-container';
        div.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1000;';
        document.body.appendChild(div);
        return div;
    })();
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        margin-top: 10px;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function abrirModal(title, content) {
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    if (modal && modalTitle && modalBody) {
        modalTitle.textContent = title;
        modalBody.innerHTML = content;
        modal.classList.add('active');
    }
}

function fecharModal() {
    const modal = document.getElementById('modal');
    if (modal) modal.classList.remove('active');
}

// Fechar modal ao clicar fora
document.addEventListener('click', (e) => {
    const modal = document.getElementById('modal');
    if (e.target === modal) {
        fecharModal();
    }
});

// ========================================
// INICIALIZAÇÃO
// ========================================

document.addEventListener('DOMContentLoaded', async () => {
    await StatusAPI.verificar();
    setInterval(() => StatusAPI.verificar(), 30000);

    GerenciadorAbas.init();
    Consultas.init();
    Reservas.init();
    Baixas.init();

    await Medicamentos.carregar();
    await carregarReservasAtivas();
    await carregarEstatisticas();

    setInterval(() => carregarReservasAtivas(), 60000);
    setInterval(() => carregarEstatisticas(), 30000);
});

// ========================================
// EXPORTAÇÃO DE FUNÇÕES GLOBAIS
// ========================================

window.Medicamentos = Medicamentos;
window.Reservas = Reservas;
window.carregarEstoque = carregarEstoque;
window.carregarReservasAtivas = carregarReservasAtivas;
window.carregarEstatisticas = carregarEstatisticas;
window.carregarRelatorioConsumo = carregarRelatorioConsumo;
window.carregarLogs = carregarLogs;
window.verificarPreReserva = verificarPreReserva;
window.fecharModal = fecharModal;
window.showToast = showToast;
window.abrirModal = abrirModal;