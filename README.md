# Finanly
Fianly é um aplicativo desenvolvido para ajudar no gerenciamento de gastos em grupos de amigos ou conhecidos, facilitando de diversas formas a sua vida financeira.

Github para avaliação do protejo da matéria de Projeto de Software da Universidade Federal de Alagoas (UFAL).

<p align="center">
  <img src="https://user-images.githubusercontent.com/91018438/204195385-acc6fcd4-05a7-4f25-87d1-cb7d5cc5c852.png" alt="animated" />
</p>

## Estrutura

- `app.py` — servidor Flask
- `backend/core.py` — classes e regras de negocio do Finanly
- `templates/index.html` — frontend
- `static/styles.css` — estilos
- `static/script.js` — conexao do frontend com a API
- `data/finanly_data.json` — persistencia dos dados
- `requirements.txt`

> Clone esse projeto em seu computador com o comando:
>
> ```
> 	git clone https://github.com/Jader-Neto/Finanly.git
> ```
>
> Acesse o diretório do projeto seu terminal:
>
> ```
> 	cd [Nome da pasta onde você salvou]
> ```

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

