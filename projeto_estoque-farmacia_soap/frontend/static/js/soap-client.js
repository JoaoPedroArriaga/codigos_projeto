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

/**
 * HMAC-SHA256 em JS puro para contextos não seguros (ex.: http://10.8.0.6).
 * crypto.subtle só funciona em localhost ou HTTPS.
 */
const HmacSha256 = {
    _rotr(n, x) {
        return (x >>> n) | (x << (32 - n));
    },

    _sha256Bytes(data) {
        const K = [
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
        ];
        let H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
        const msgLen = data.length;
        const bitLenHi = Math.floor((msgLen * 8) / 0x100000000);
        const bitLenLo = (msgLen * 8) >>> 0;
        let paddedLen = msgLen + 1 + 8;
        while (paddedLen % 64 !== 0) paddedLen++;
        const msg = new Uint8Array(paddedLen);
        msg.set(data);
        msg[msgLen] = 0x80;
        const view = new DataView(msg.buffer);
        view.setUint32(paddedLen - 8, bitLenHi, false);
        view.setUint32(paddedLen - 4, bitLenLo, false);

        const w = new Uint32Array(64);
        for (let i = 0; i < paddedLen; i += 64) {
            for (let t = 0; t < 16; t++) {
                w[t] = view.getUint32(i + t * 4, false);
            }
            for (let t = 16; t < 64; t++) {
                const s0 = this._rotr(7, w[t - 15]) ^ this._rotr(18, w[t - 15]) ^ (w[t - 15] >>> 3);
                const s1 = this._rotr(17, w[t - 2]) ^ this._rotr(19, w[t - 2]) ^ (w[t - 2] >>> 10);
                w[t] = (w[t - 16] + s0 + w[t - 7] + s1) >>> 0;
            }
            let a = H[0], b = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
            for (let t = 0; t < 64; t++) {
                const S1 = this._rotr(6, e) ^ this._rotr(11, e) ^ this._rotr(25, e);
                const ch = (e & f) ^ (~e & g);
                const t1 = (h + S1 + ch + K[t] + w[t]) >>> 0;
                const S0 = this._rotr(2, a) ^ this._rotr(13, a) ^ this._rotr(22, a);
                const maj = (a & b) ^ (a & c) ^ (b & c);
                const t2 = (S0 + maj) >>> 0;
                h = g; g = f; f = e; e = (d + t1) >>> 0;
                d = c; c = b; b = a; a = (t1 + t2) >>> 0;
            }
            H = [
                (H[0] + a) >>> 0, (H[1] + b) >>> 0, (H[2] + c) >>> 0, (H[3] + d) >>> 0,
                (H[4] + e) >>> 0, (H[5] + f) >>> 0, (H[6] + g) >>> 0, (H[7] + h) >>> 0
            ];
        }
        return H.map(v => v.toString(16).padStart(8, '0')).join('');
    },

    _hexToBytes(hex) {
        const out = new Uint8Array(hex.length / 2);
        for (let i = 0; i < out.length; i++) {
            out[i] = parseInt(hex.substr(i * 2, 2), 16);
        }
        return out;
    },

    calcular(chave, mensagem) {
        const blockSize = 64;
        let keyBytes = new TextEncoder().encode(chave);
        if (keyBytes.length > blockSize) {
            keyBytes = this._hexToBytes(this._sha256Bytes(keyBytes));
        }
        const oKeyPad = new Uint8Array(blockSize);
        const iKeyPad = new Uint8Array(blockSize);
        for (let i = 0; i < blockSize; i++) {
            const b = keyBytes[i] || 0;
            oKeyPad[i] = b ^ 0x5c;
            iKeyPad[i] = b ^ 0x36;
        }
        const msgBytes = new TextEncoder().encode(mensagem);
        const inner = new Uint8Array(blockSize + msgBytes.length);
        inner.set(iKeyPad);
        inner.set(msgBytes, blockSize);
        const innerHash = this._hexToBytes(this._sha256Bytes(inner));
        const outer = new Uint8Array(blockSize + innerHash.length);
        outer.set(oKeyPad);
        outer.set(innerHash, blockSize);
        return this._sha256Bytes(outer);
    }
};

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
        if (window.crypto?.subtle && window.isSecureContext) {
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
        return HmacSha256.calcular(SOAP_CHAVE_SECRETA, conteudo);
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
