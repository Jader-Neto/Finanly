
from flask import Flask, jsonify, render_template, request
from backend.core import SistemaFinanly

app = Flask(__name__, template_folder="templates", static_folder="static")
sistema = SistemaFinanly(data_file="data/finanly_data.json")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/dashboard")
def dashboard():
    return jsonify(sistema.resumo_dashboard())


@app.get("/api/users")
def listar_usuarios():
    return jsonify(sistema.serializar_usuarios())


@app.post("/api/users")
def criar_usuario():
    dados = request.get_json(force=True)
    usuario = sistema.registrar_usuario(
        nome=dados["nome"],
        email=dados["email"],
        senha=dados.get("senha", "123"),
        pix=dados.get("pix", "")
    )
    return jsonify(usuario.para_dict_publico()), 201


@app.get("/api/groups")
def listar_grupos():
    return jsonify(sistema.serializar_grupos())


@app.post("/api/groups")
def criar_grupo():
    dados = request.get_json(force=True)
    grupo = sistema.criar_grupo(
        nome=dados["nome"],
        membros=dados["membros"]
    )
    return jsonify(sistema.serializar_grupo(grupo.grupo_id)), 201


@app.get("/api/expenses")
def listar_despesas():
    return jsonify(sistema.serializar_despesas())


@app.post("/api/expenses")
def criar_despesa():
    dados = request.get_json(force=True)
    despesa = sistema.criar_despesa_igualitaria(
        grupo_id=dados["grupo_id"],
        descricao=dados["descricao"],
        pago_por=dados["pago_por"],
        total=float(dados["valor"]),
        participantes=dados["participantes"],
        categoria=dados.get("categoria", "Outros")
    )
    return jsonify(sistema.serializar_despesa(despesa.despesa_id)), 201


@app.get("/api/settlement/<int:grupo_id>")
def liquidacao(grupo_id: int):
    return jsonify({
        "saldos": sistema.serializar_saldos(grupo_id),
        "liquidacao": sistema.serializar_liquidacao(grupo_id)
    })


@app.post("/api/seed")
def popular_demo():
    sistema.popular_demo()
    return jsonify({"ok": True})


@app.post("/api/reset")
def resetar():
    sistema.resetar()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
