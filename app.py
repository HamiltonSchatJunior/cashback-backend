from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
import uuid
import random
import smtplib
from email.message import EmailMessage
from datetime import datetime

app = Flask(__name__)
CORS(app)

USERS_FILE = 'usuarios.json'
EMAIL_SENDER = "mevoltacashback@gmail.com"
EMAIL_SENDER_PASSWORD = "eowl sywx szjc davk"

# --- Funções auxiliares ---

def carregar_usuarios():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []

def salvar_usuarios(lista):
    with open(USERS_FILE, 'w') as f:
        json.dump(lista, f, indent=2)

def enviar_codigo_email(destinatario, codigo):
    msg = EmailMessage()
    msg['Subject'] = 'Seu código de verificação - Cashback Fácil'
    msg['From'] = EMAIL_SENDER
    msg['To'] = destinatario
    msg.set_content(f"""
Olá!

Seu código de verificação é: {codigo}

Digite este código na tela de verificação para ativar sua conta.

Equipe Cashback Fácil.
""")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_SENDER_PASSWORD)
        smtp.send_message(msg)

# --- Rotas ---

@app.route('/admin')
def admin_painel():
    return render_template('admin.html')

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    data = request.json
    usuarios = carregar_usuarios()

    if any(u['email'] == data['email'] for u in usuarios):
        return jsonify({"erro": "Email já cadastrado."}), 400

    codigo_verificacao = ''.join([str(random.randint(0, 9)) for _ in range(6)])

    novo_usuario = {
        "id": str(uuid.uuid4()),
        "nome": data['nome'],
        "email": data['email'],
        "senha": data['senha'],
        "cpf": data.get('cpf', ''),
        "telefone": data.get('telefone', ''),
        "data_cadastro": datetime.now().isoformat(),
        "saldo": 0.0,
        "cashback_total": 0.0,
        "ativo": False,
        "codigo_verificacao": codigo_verificacao
    }

    usuarios.append(novo_usuario)
    salvar_usuarios(usuarios)

    try:
        enviar_codigo_email(data['email'], codigo_verificacao)
    except Exception as e:
        return jsonify({"erro": "Erro ao enviar e-mail de verificação."}), 500

    return jsonify({
    "mensagem": "Cadastro realizado com sucesso. Verifique seu e-mail.",
    "usuario": {
        "nome": data["nome"],
        "email": data["email"],
        "ativo": False
    }
}), 200


@app.route('/verificar_codigo', methods=['POST'])
def verificar_codigo():
    data = request.json
    email = data.get('email')
    codigo = data.get('codigo')

    usuarios = carregar_usuarios()

    for u in usuarios:
        if u['email'] == email:
            if u['codigo_verificacao'] == codigo:
                u['ativo'] = True
                u.pop('codigo_verificacao', None)
                salvar_usuarios(usuarios)
                return jsonify({"mensagem": "Conta verificada com sucesso!", "usuario": u})
            else:
                return jsonify({"erro": "Código incorreto."}), 400

    return jsonify({"erro": "Usuário não encontrado."}), 404

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usuarios = carregar_usuarios()

    for u in usuarios:
        if u['email'] == data['email'] and u['senha'] == data['senha']:
            if not u.get('ativo'):
                return jsonify({"erro": "Conta ainda não verificada."}), 403
            return jsonify({"mensagem": "Login realizado com sucesso!", "usuario": u})

    return jsonify({"erro": "Email ou senha incorretos."}), 401

@app.route('/editar_usuario', methods=['POST'])
def editar_usuario():
    data = request.json
    usuarios = carregar_usuarios()

    for u in usuarios:
        if u.get('id') == data.get('id'):
            u['nome'] = data['nome']
            u['email'] = data['email']
            if data.get('senha'):
                u['senha'] = data['senha']
            u['cpf'] = data.get('cpf', '')
            u['telefone'] = data.get('telefone', '')
            salvar_usuarios(usuarios)
            return jsonify({"mensagem": "Usuário atualizado com sucesso!"})

    return jsonify({"erro": "Usuário não encontrado."}), 404

@app.route('/usuario', methods=['GET'])
def buscar_usuario():
    email = request.args.get('email')
    usuarios = carregar_usuarios()

    for u in usuarios:
        if u['email'] == email:
            return jsonify({
                "id": u.get("id", ""),
                "nome": u['nome'],
                "email": u['email'],
                "saldo": u.get('saldo', 0.0),
                "cashback_total": u.get('cashback_total', 0.0),
                "cpf": u.get('cpf', ''),
                "telefone": u.get('telefone', '')
            })

    return jsonify({"erro": "Usuário não encontrado."}), 404

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

if __name__ == '__main__':
    app.run(debug=True)
