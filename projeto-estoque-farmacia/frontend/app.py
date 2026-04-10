#!/usr/bin/env python
"""
Frontend simples para controlar o sistema
"""
import os
import sys
import webbrowser
from flask import Flask, render_template, request, jsonify, redirect, url_for

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.gerar_consulta import gerar_consulta
from scripts.gerar_reserva import gerar_reserva
from scripts.gerar_baixa import gerar_baixa
from scripts.gerar_todos import gerar_todos
from src.config.database import db

app = Flask(__name__)

# Rotas
@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/gerar/consulta', methods=['POST'])
def api_gerar_consulta():
    """API para gerar consulta"""
    dados = request.json
    caminho = gerar_consulta(
        codigo_medicamento=dados.get('codigo', 789123),
        quantidade=dados.get('quantidade', 2),
        cpf_paciente=dados.get('cpf', 12345678901)
    )
    return jsonify({'success': True, 'arquivo': caminho})

@app.route('/api/gerar/reserva', methods=['POST'])
def api_gerar_reserva():
    """API para gerar reserva"""
    dados = request.json
    caminho = gerar_reserva(
        codigo_medicamento=dados.get('codigo', 789123),
        quantidade=dados.get('quantidade', 2),
        lote=dados.get('lote', 'LOTE123'),
        cpf_paciente=dados.get('cpf', 12345678901)
    )
    return jsonify({'success': True, 'arquivo': caminho})

@app.route('/api/gerar/baixa', methods=['POST'])
def api_gerar_baixa():
    """API para gerar baixa"""
    dados = request.json
    caminho = gerar_baixa(
        codigo_medicamento=dados.get('codigo', 789123),
        quantidade=dados.get('quantidade', 2),
        lote=dados.get('lote', 'LOTE123'),
        cpf_paciente=dados.get('cpf', 12345678901)
    )
    return jsonify({'success': True, 'arquivo': caminho})

@app.route('/api/gerar/fluxo', methods=['POST'])
def api_gerar_fluxo():
    """API para gerar fluxo completo"""
    dados = request.json
    gerar_todos(
        codigo=dados.get('codigo', 789123),
        quantidade=dados.get('quantidade', 2),
        lote=dados.get('lote', 'LOTE123')
    )
    return jsonify({'success': True, 'message': 'Fluxo completo gerado'})

@app.route('/api/estoque', methods=['GET'])
def api_estoque():
    """API para ver estoque"""
    db.connect()
    lotes = db.execute("SELECT * FROM lotes ORDER BY numero_lote", fetch_all=True)
    db.close()
    return jsonify(lotes)

@app.route('/api/consumo', methods=['GET'])
def api_consumo():
    """API para ver consumo"""
    db.connect()
    itens = db.execute(
        "SELECT * FROM itens_consumo ORDER BY id_item DESC LIMIT 20",
        fetch_all=True
    )
    db.close()
    return jsonify(itens)

@app.route('/api/logs', methods=['GET'])
def api_logs():
    """API para ver logs"""
    db.connect()
    tipo = request.args.get('tipo', 'consultas')
    
    if tipo == 'consultas':
        logs = db.execute("SELECT * FROM logs_consultas ORDER BY id_log DESC LIMIT 20", fetch_all=True)
    elif tipo == 'reservas':
        logs = db.execute("SELECT * FROM logs_reservas ORDER BY id_log DESC LIMIT 20", fetch_all=True)
    elif tipo == 'baixas':
        logs = db.execute("SELECT * FROM logs_baixas ORDER BY id_log DESC LIMIT 20", fetch_all=True)
    else:
        logs = []
    
    db.close()
    return jsonify(logs)

if __name__ == '__main__':
    # Abrir navegador automaticamente
    webbrowser.open('http://127.0.0.1:5000')
    app.run(debug=True, port=5000)