# Finanly


## Estrutura

- `app.py` — servidor Flask
- `backend/core.py` — classes e regras de negocio do Finanly
- `templates/index.html` — frontend
- `static/styles.css` — estilos
- `static/script.js` — conexao do frontend com a API
- `data/finanly_data.json` — persistencia dos dados
- `requirements.txt`

## Como executar

### 1. Criar ambiente virtual

No Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Rodar o sistema

```bash
python app.py
```

### 4. Abrir no navegador

Acesse:

```
http://127.0.0.1:5000
```

## O que esta integrado

- cadastro de pessoas via frontend -> backend Python
- criacao de grupos via frontend -> backend Python
- criacao de despesas via frontend -> backend Python
- calculo de saldos e liquidacao via backend -> frontend
- persistencia real em JSON

## Observacao

Mantive o backend em Python orientado a objetos. A interface agora faz chamadas reais para ele usando `fetch`.
