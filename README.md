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

10 funcionalidades do app

1- Criação de conta com a classe Usuario.
2- Login com verificação de senha encapsulada em Usuario.
3- Geração de chave pública única para cada usuário.
4- Adição de contatos por chave pública.
5- Criação de eventos/grupos com a classe Grupo.
6- Controle de acesso aos grupos por usuário logado.
7- Registro de despesas usando a classe abstrata Despesa.
8- Implementação de despesa igualitária com DespesaIgualitaria.
9- Cálculo automático das cotas dos participantes.
10- Simplificação de dívidas usando os saldos calculados.

Casos pedidas no código
Classe abstrata	-> class Despesa(ABC) -> linha 271
Herança -> class DespesaIgualitaria(Despesa): -> linha 302
Polimorfismo / binding dinâmico	-> cotas = despesa.calcular_cotas()	-> linha 534
Polimorfismo / binding dinâmico	-> despesa.valor_total()	-> linha 537
