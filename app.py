
from flask import Flask, jsonify, render_template, request, session, send_from_directory
from werkzeug.utils import secure_filename
from backend.core import SistemaFinanly, ErroValidacao
import os
import uuid

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "finanly-dev-secret-key-change-this"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

sistema = SistemaFinanly("data/finanly_data.json", "data/backups")


@app.errorhandler(ErroValidacao)
def handle_validation(error):
    return jsonify({"erro": str(error)}), 400


@app.errorhandler(ValueError)
def handle_value_error(error):
    return jsonify({"erro": "Dados inválidos enviados no formulário. Verifique evento, cobrador, valor e participantes."}), 400


@app.errorhandler(KeyError)
def handle_key_error(error):
    return jsonify({"erro": "Campo obrigatório ausente no formulário de despesa."}), 400


def current_user_id():
    return session.get("usuario_id")


def require_login():
    if not current_user_id():
        return False
    return True


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.get("/api/auth/me")
def me():
    uid = current_user_id()
    if not uid:
        return jsonify({"logado": False, "usuario": None})
    usuario = sistema.obter_usuario(uid)
    if not usuario:
        session.clear()
        return jsonify({"logado": False, "usuario": None})
    return jsonify({"logado": True, "usuario": usuario.para_dict_publico()})


@app.post("/api/auth/register")
def register():
    data = request.get_json(force=True)
    usuario = sistema.registrar_usuario(
        nome=data["nome"],
        email=data["email"],
        senha=data["senha"],
        pix=data.get("pix", "")
    )
    session["usuario_id"] = usuario.usuario_id
    return jsonify({"ok": True, "usuario": usuario.para_dict_publico()}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True)
    usuario = sistema.autenticar(data["email"], data["senha"])
    session["usuario_id"] = usuario.usuario_id
    return jsonify({"ok": True, "usuario": usuario.para_dict_publico()})


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/dashboard")
def dashboard():
    if not require_login():
        return jsonify({"erro": "Faça login para continuar."}), 401
    return jsonify(sistema.resumo_dashboard(current_user_id()))


@app.get("/api/contacts")
def contacts():
    if not require_login():
        return jsonify({"erro": "Faça login para continuar."}), 401
    return jsonify(sistema.serializar_contatos(current_user_id()))


@app.post("/api/contacts/add")
def add_contact():
    if not require_login():
        return jsonify({"erro": "Faça login para continuar."}), 401
    data = request.get_json(force=True)
    contato = sistema.adicionar_contato_por_chave(current_user_id(), data["chave"])
    return jsonify(contato.para_dict_publico())


@app.get("/api/groups")
def groups():
    if not require_login():
        return jsonify({"erro": "Faça login para continuar."}), 401
    return jsonify(sistema.serializar_grupos(current_user_id()))


@app.post("/api/groups")
def create_group():
    if not require_login():
        return jsonify({"erro": "Faça login para continuar."}), 401
    data = request.get_json(force=True)
    grupo = sistema.criar_grupo(
        dono_id=current_user_id(),
        nome=data["nome"],
        membros=data.get("membros", [])
    )
    return jsonify(sistema.serializar_grupo(grupo.grupo_id, current_user_id())), 201


@app.get("/api/expenses")
def expenses():
    if not require_login():
        return jsonify({"erro": "Faça login para continuar."}), 401
    return jsonify(sistema.serializar_despesas(current_user_id()))


@app.post("/api/expenses")
def create_expense():
    if not require_login():
        return jsonify({"erro": "Faça login para continuar."}), 401

    grupo_id = request.form.get("grupo_id", "").strip()
    descricao = request.form.get("descricao", "").strip()
    pago_por = request.form.get("pago_por", "").strip()
    valor = request.form.get("valor", "").strip()
    participantes_raw = request.form.getlist("participantes")

    if not grupo_id:
        raise ErroValidacao("Selecione um evento antes de registrar a despesa.")
    if not descricao:
        raise ErroValidacao("Informe uma descrição para a despesa.")
    if not pago_por:
        raise ErroValidacao("Selecione quem pagou/cobrou a despesa.")
    if not valor:
        raise ErroValidacao("Informe o valor da despesa.")
    if not participantes_raw:
        raise ErroValidacao("Selecione pelo menos um participante da despesa.")

    imagem = request.files.get("imagem")
    anexo = None

    if imagem and imagem.filename:
        filename = secure_filename(imagem.filename)
        unique_name = f"{uuid.uuid4()}_{filename}"
        path = os.path.join(UPLOAD_FOLDER, unique_name)
        imagem.save(path)
        anexo = unique_name

    despesa = sistema.criar_despesa_igualitaria(
        usuario_id=current_user_id(),
        grupo_id=int(grupo_id),
        descricao=descricao,
        pago_por=int(pago_por),
        total=float(valor),
        participantes=[int(x) for x in participantes_raw],
        categoria=request.form.get("categoria", "Outros"),
        anexo=anexo
    )
    return jsonify(sistema.serializar_despesa(despesa.despesa_id, current_user_id())), 201


@app.delete("/api/expenses/<int:expense_id>")
def delete_expense(expense_id):
    if not require_login():
        return jsonify({"erro": "Faça login para continuar."}), 401
    sistema.remover_despesa(current_user_id(), expense_id)
    return jsonify({"ok": True})


@app.get("/api/settlement/<int:group_id>")
def settlement(group_id):
    if not require_login():
        return jsonify({"erro": "Faça login para continuar."}), 401
    return jsonify({
        "saldos": sistema.serializar_saldos(current_user_id(), group_id),
        "liquidacao": sistema.serializar_liquidacao(current_user_id(), group_id)
    })


@app.post("/api/seed")
def seed():
    if not require_login():
        return jsonify({"erro": "Faça login para continuar."}), 401
    sistema.popular_demo(current_user_id())
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
