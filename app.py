from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)
USERS_FILE = 'usuarios.json'

@app.route('/admin')
def admin_painel():
    return render_template('admin.html')

# Carregar usuários do arquivo
def carregar_usuarios():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []

# Salvar usuários no arquivo
def salvar_usuarios(lista):
    with open(USERS_FILE, 'w') as f:
        json.dump(lista, f, indent=2)

# Rota para cadastrar novo usuário
@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    data = request.json
    usuarios = carregar_usuarios()

    if any(u['email'] == data['email'] for u in usuarios):
        return jsonify({"erro": "Email já cadastrado."}), 400

    novo_usuario = {
        "nome": data['nome'],
        "email": data['email'],
        "senha": data['senha'],
        "cpf": data.get('cpf', ''),
        "telefone": data.get('telefone', ''),
        "data_cadastro": datetime.now().isoformat(),
        "saldo": 0.0,
        "cashback_total": 0.0
    }

    usuarios.append(novo_usuario)
    salvar_usuarios(usuarios)
    return jsonify({"mensagem": "Usuário cadastrado com sucesso!"})

# Rota para login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usuarios = carregar_usuarios()

    for u in usuarios:
        if u['email'] == data['email'] and u['senha'] == data['senha']:
            return jsonify({"mensagem": "Login realizado com sucesso!", "usuario": u})

    return jsonify({"erro": "Email ou senha incorretos."}), 401

# Rota para buscar dados do usuário
@app.route('/usuario', methods=['GET'])
def buscar_usuario():
    email = request.args.get('email')
    usuarios = carregar_usuarios()

    for u in usuarios:
        if u['email'] == email:
            return jsonify({
                "nome": u['nome'],
                "email": u['email'],
                "saldo": u.get('saldo', 0.0),
                "cashback_total": u.get('cashback_total', 0.0),
                "cpf": u.get('cpf', ''),
                "telefone": u.get('telefone', '')
            })

    return jsonify({"erro": "Usuário não encontrado."}), 404

# Rota de redirecionamento com cashback
@app.route('/redirecionar', methods=['GET'])
def redirecionar():
    email = request.args.get('email')
    destino = request.args.get('destino')

    redirecionamentos = {
        "mercadolivre": "https://www.mercadolivre.com.br",
        "americanas": "https://www.americanas.com.br",
        "magazineluiza": "https://www.magazineluiza.com.br",
        "shopee": "https://shopee.com.br"
    }

    if not email or not destino or destino not in redirecionamentos:
        return jsonify({"erro": "Parâmetros inválidos."}), 400

    usuarios = carregar_usuarios()

    for u in usuarios:
        if u['email'] == email:
            u['cashback_total'] = u.get('cashback_total', 0.0) + 1.0
            u['saldo'] = u.get('saldo', 0.0) + 1.0
            salvar_usuarios(usuarios)
            break

    return '', 302, {'Location': redirecionamentos[destino]}

@app.route('/admin/usuarios', methods=['GET'])
def listar_usuarios():
    usuarios = carregar_usuarios()
    return jsonify(usuarios)

# Iniciar servidor
if __name__ == '__main__':
    app.run(debug=True)
