/**
 * Cliente SOAP para o dashboard
 * Monta envelopes XML com HMAC-SHA256 compatível com o servidor Python/lxml
 */

const SOAP_NS = {
    SOAP: 'http://schemas.xmlsoap.org/soap/envelope/',
    TNS: 'http://estoque-farmacia.projeto.interop/v1',
    TIPOS: 'http://estoque-farmacia.projeto.interop/v1/tipos',
};

const SOAP_CHAVE_SECRETA = 'chave_secreta_compartilhada_entre_grupos_2026';
const SOAP_GRUPO_ORIGEM = 'GRUPO_DASHBOARD';

class SOAPClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.soapURL = `${baseURL}/soap`;
        this.healthURL = `${baseURL}/soap/health`;
        this.timeout = 15000;
    }

    _montarBodyXml(operacao, parametros = {}) {
        const ns = `xmlns:tns="${SOAP_NS.TNS}" xmlns:soap="${SOAP_NS.SOAP}" xmlns:tipos="${SOAP_NS.TIPOS}"`;
        const paramsXml = Object.entries(parametros)
            .filter(([, v]) => v !== null && v !== undefined && v !== '')
            .map(([k, v]) => `<tns:${k}>${this._escapeXml(String(v))}</tns:${k}>`)
            .join('');

        if (!paramsXml) {
            return `<tns:${operacao} ${ns}/>`;
        }
        return `<tns:${operacao} ${ns}>${paramsXml}</tns:${operacao}>`;
    }

    _escapeXml(value) {
        return value
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&apos;');
    }

    async _calcularHmac(conteudo) {
        const enc = new TextEncoder();
        const key = await crypto.subtle.importKey(
            'raw',
            enc.encode(SOAP_CHAVE_SECRETA),
            { name: 'HMAC', hash: 'SHA-256' },
            false,
            ['sign']
        );
        const assinatura = await crypto.subtle.sign('HMAC', key, enc.encode(conteudo));
        return Array.from(new Uint8Array(assinatura))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    async _montarEnvelope(operacao, parametros = {}) {
        const bodyXml = this._montarBodyXml(operacao, parametros);
        const hash = await this._calcularHmac(bodyXml);
        const timestamp = new Date().toISOString();

        return `<?xml version='1.0' encoding='utf-8'?>`
            + `<soap:Envelope xmlns:soap="${SOAP_NS.SOAP}" xmlns:tipos="${SOAP_NS.TIPOS}" xmlns:tns="${SOAP_NS.TNS}">`
            + `<soap:Header><tns:autenticacao>`
            + `<tns:hash>${hash}</tns:hash>`
            + `<tns:timestamp>${timestamp}</tns:timestamp>`
            + `<tns:grupo_origem>${SOAP_GRUPO_ORIGEM}</tns:grupo_origem>`
            + `<tns:algoritmo>HMAC-SHA256</tns:algoritmo>`
            + `</tns:autenticacao></soap:Header>`
            + `<soap:Body>${bodyXml}</soap:Body>`
            + `</soap:Envelope>`;
    }

    _elementoParaObjeto(elemento) {
        if (!elemento) return null;

        const filhos = Array.from(elemento.children);
        if (filhos.length === 0) {
            const texto = elemento.textContent?.trim() ?? '';
            if (/^-?\d+$/.test(texto)) return parseInt(texto, 10);
            if (/^-?\d+\.\d+$/.test(texto)) return parseFloat(texto);
            return texto;
        }

        const grupos = {};
        for (const filho of filhos) {
            const nome = filho.localName;
            const valor = this._elementoParaObjeto(filho);
            if (grupos[nome]) {
                if (!Array.isArray(grupos[nome])) {
                    grupos[nome] = [grupos[nome]];
                }
                grupos[nome].push(valor);
            } else {
                grupos[nome] = valor;
            }
        }
        return grupos;
    }

    _parsearResposta(xmlText) {
        const doc = new DOMParser().parseFromString(xmlText, 'text/xml');
        const parserErro = doc.querySelector('parsererror');
        if (parserErro) {
            throw new Error('Resposta XML inválida');
        }

        const faultString = doc.getElementsByTagName('faultstring')[0];
        if (faultString) {
            throw new Error(faultString.textContent || 'Erro SOAP');
        }

        const bodies = doc.getElementsByTagNameNS(SOAP_NS.SOAP, 'Body');
        if (!bodies.length || !bodies[0].firstElementChild) {
            throw new Error('Resposta SOAP sem conteúdo');
        }

        return this._elementoParaObjeto(bodies[0].firstElementChild);
    }

    async enviar(operacao, parametros = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const envelope = await this._montarEnvelope(operacao, parametros);
            const resposta = await fetch(this.soapURL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'text/xml; charset=utf-8',
                    'SOAPAction': operacao,
                },
                body: envelope,
                signal: controller.signal,
            });

            clearTimeout(timeoutId);
            const xmlText = await resposta.text();

            if (!resposta.ok && !xmlText.includes('Fault')) {
                throw new Error(`HTTP ${resposta.status}`);
            }

            const dados = this._parsearResposta(xmlText);
            const sufixo = 'Response';
            if (dados && typeof dados === 'object') {
                const chaveResposta = Object.keys(dados).find(k => k.endsWith(sufixo));
                if (chaveResposta) {
                    return dados[chaveResposta];
                }
            }
            return dados;
        } catch (erro) {
            clearTimeout(timeoutId);
            if (erro.name === 'AbortError') {
                throw new Error('Timeout na requisição SOAP');
            }
            throw erro;
        }
    }

    async verificarConexao() {
        try {
            const resposta = await fetch(this.healthURL, { method: 'GET' });
            if (!resposta.ok) return false;
            const dados = await resposta.json();
            return dados.status === 'ok';
        } catch {
            return false;
        }
    }
}
