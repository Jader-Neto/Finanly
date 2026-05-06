# Finanly 

Fianly é um aplicativo desenvolvido para ajudar no gerenciamento de gastos em grupos de amigos ou conhecidos, facilitando de diversas formas a sua vida financeira.

Github para avaliação do protejo da matéria de Projeto de Software da Universidade Federal de Alagoas (UFAL).

<p align="center">
  <img src="https://user-images.githubusercontent.com/91018438/204195385-acc6fcd4-05a7-4f25-87d1-cb7d5cc5c852.png" alt="animated" />
</p>

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

Depois acesse:

```text
http://127.0.0.1:5000
```

## 10 funcionalidades principais

### 1. Criação de contas utilizando a classe `Usuario`
Cada usuário possui um perfil único contendo:
- Nome
- E-mail
- Senha
- Chave pública
- Chave Pix

---

### 2. Sistema de login com autenticação encapsulada
O sistema realiza autenticação segura utilizando métodos internos da classe `Usuario`.

---

### 3. Geração automática de chave pública
Cada conta recebe uma chave única no formato:

```text
FIN-XXXX-XXXX-XXXX
```

Essa chave permite que usuários adicionem outros participantes ao sistema.

---

### 4. Adição de contatos por chave pública
Usuários podem adicionar amigos ou participantes apenas compartilhando suas chaves únicas.

---

### 5. Criação de eventos/grupos utilizando a classe `Grupo`
Os usuários conseguem criar:
- Eventos
- Grupos de despesas
- Ambientes compartilhados

---

### 6. Controle de acesso por usuário logado
A aplicação garante que apenas participantes autorizados tenham acesso aos grupos e despesas.

---

### 7. Registro de despesas utilizando classe abstrata
O sistema utiliza uma estrutura abstrata para permitir múltiplos tipos de despesas futuramente.

---

### 8. Implementação de despesas igualitárias
A classe `DespesaIgualitaria` divide automaticamente os valores entre os participantes.

---

### 9. Cálculo automático das cotas
O sistema calcula quanto cada participante deve pagar com base na divisão configurada.

---

### 10. Simplificação automática de dívidas
O algoritmo reduz transferências desnecessárias entre usuários utilizando os saldos calculados.

Conceitos de Programação Orientada a Objetos (POO)

## Classe Abstrata

A classe abstrata define a estrutura base para qualquer tipo de despesa.

### Código

```python
class Despesa(ABC):
```

Linha:
```text
271
```

---

## Herança

A classe `DespesaIgualitaria` herda características da classe abstrata `Despesa`.

### Código

```python
class DespesaIgualitaria(Despesa):
```

Linha:
```text
302
```

---

## 🔸 Polimorfismo / Binding Dinâmico

O sistema executa métodos de despesas sem precisar conhecer o tipo exato da despesa.

### Código

```python
cotas = despesa.calcular_cotas()
```

Linha:
```text
534
```

---

### Código

```python
despesa.valor_total()
```

Linha:
```text
537
```

