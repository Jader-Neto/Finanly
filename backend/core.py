
from __future__ import annotations
import json
import os
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


class Usuario:
    def __init__(self, usuario_id: int, nome: str, email: str, senha: str, pix: str = ""):
        self.usuario_id = usuario_id
        self.nome = nome.strip()
        self.email = email.lower().strip()
        self.__hash_senha = hash_senha(senha)
        self.__pix = pix.strip()
        self.criado_em = agora()
        self.ativo = True

    @property
    def pix(self) -> str:
        return self.__pix

    def definir_pix(self, valor: str):
        self.__pix = valor.strip()

    def verificar_senha(self, senha: str) -> bool:
        return self.__hash_senha == hash_senha(senha)

    def para_dict(self) -> dict:
        return {
            "usuario_id": self.usuario_id,
            "nome": self.nome,
            "email": self.email,
            "hash_senha": self._Usuario__hash_senha,
            "pix": self._Usuario__pix,
            "criado_em": self.criado_em,
            "ativo": self.ativo,
        }

    def para_dict_publico(self) -> dict:
        return {
            "usuario_id": self.usuario_id,
            "nome": self.nome,
            "email": self.email,
            "pix": self.pix,
            "criado_em": self.criado_em,
        }

    @classmethod
    def de_dict(cls, dados: dict) -> "Usuario":
        obj = cls(
            usuario_id=dados["usuario_id"],
            nome=dados["nome"],
            email=dados["email"],
            senha="temp",
            pix=dados.get("pix", "")
        )
        obj._Usuario__hash_senha = dados["hash_senha"]
        obj.criado_em = dados.get("criado_em", agora())
        obj.ativo = dados.get("ativo", True)
        return obj


@dataclass
class AlocacaoItem:
    usuario_id: int
    valor: float


@dataclass
class ItemDespesa:
    nome: str
    valor: float
    categoria: str
    alocacoes: List[AlocacaoItem] = field(default_factory=list)


@dataclass
class Pagamento:
    pagamento_id: int
    grupo_id: int
    de_usuario: int
    para_usuario: int
    valor: float
    criado_em: str = field(default_factory=agora)


class Grupo:
    def __init__(self, grupo_id: int, nome: str, membros: List[int]):
        self.grupo_id = grupo_id
        self.nome = nome
        self.membros = list(dict.fromkeys(membros))
        self.ids_despesas: List[int] = []
        self.ids_pagamentos: List[int] = []

    def adicionar_membro(self, usuario_id: int):
        if usuario_id not in self.membros:
            self.membros.append(usuario_id)

    def adicionar_despesa(self, despesa_id: int):
        self.ids_despesas.append(despesa_id)

    def adicionar_pagamento(self, pagamento_id: int):
        self.ids_pagamentos.append(pagamento_id)

    def para_dict(self) -> dict:
        return {
            "grupo_id": self.grupo_id,
            "nome": self.nome,
            "membros": self.membros,
            "ids_despesas": self.ids_despesas,
            "ids_pagamentos": self.ids_pagamentos,
        }

    @classmethod
    def de_dict(cls, dados: dict) -> "Grupo":
        obj = cls(dados["grupo_id"], dados["nome"], dados["membros"])
        obj.ids_despesas = dados.get("ids_despesas", [])
        obj.ids_pagamentos = dados.get("ids_pagamentos", [])
        return obj


class Despesa(ABC):
    def __init__(self, despesa_id: int, grupo_id: int, descricao: str, pago_por: int,
                 moeda: str = "BRL", categoria: str = "Outros"):
        self.despesa_id = despesa_id
        self.grupo_id = grupo_id
        self.descricao = descricao
        self.pago_por = pago_por
        self.moeda = moeda
        self.categoria = categoria
        self.criado_em = agora()

    @abstractmethod
    def calcular_cotas(self) -> Dict[int, float]:
        pass

    @abstractmethod
    def valor_total(self) -> float:
        pass

    @abstractmethod
    def para_dict(self) -> dict:
        pass


class DespesaIgualitaria(Despesa):
    def __init__(self, despesa_id, grupo_id, descricao, pago_por, total, participantes,
                 moeda="BRL", categoria="Outros"):
        super().__init__(despesa_id, grupo_id, descricao, pago_por, moeda, categoria)
        self.total = round(total, 2)
        self.participantes = participantes

    def calcular_cotas(self) -> Dict[int, float]:
        cota = round(self.total / len(self.participantes), 2)
        cotas = {uid: cota for uid in self.participantes}
        diff = round(self.total - sum(cotas.values()), 2)
        if diff != 0:
            cotas[self.participantes[-1]] = round(cotas[self.participantes[-1]] + diff, 2)
        return cotas

    def valor_total(self) -> float:
        return self.total

    def para_dict(self) -> dict:
        return {
            "tipo": "DespesaIgualitaria",
            "despesa_id": self.despesa_id,
            "grupo_id": self.grupo_id,
            "descricao": self.descricao,
            "pago_por": self.pago_por,
            "total": self.total,
            "participantes": self.participantes,
            "moeda": self.moeda,
            "categoria": self.categoria,
            "criado_em": self.criado_em,
        }


def despesa_de_dict(dados: dict) -> Despesa:
    obj = DespesaIgualitaria(
        dados["despesa_id"],
        dados["grupo_id"],
        dados["descricao"],
        dados["pago_por"],
        dados["total"],
        dados["participantes"],
        dados.get("moeda", "BRL"),
        dados.get("categoria", "Outros"),
    )
    obj.criado_em = dados.get("criado_em", agora())
    return obj


class SistemaFinanly:
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.usuarios: Dict[int, Usuario] = {}
        self.grupos: Dict[int, Grupo] = {}
        self.despesas: Dict[int, Despesa] = {}
        self.pagamentos: Dict[int, Pagamento] = {}
        self.proximo_usuario_id = 1
        self.proximo_grupo_id = 1
        self.proxima_despesa_id = 1
        self.carregar()

    def salvar(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump({
                "usuarios": [u.para_dict() for u in self.usuarios.values()],
                "grupos": [g.para_dict() for g in self.grupos.values()],
                "despesas": [d.para_dict() for d in self.despesas.values()],
                "pagamentos": [asdict(p) for p in self.pagamentos.values()],
                "contadores": {
                    "proximo_usuario_id": self.proximo_usuario_id,
                    "proximo_grupo_id": self.proximo_grupo_id,
                    "proxima_despesa_id": self.proxima_despesa_id,
                }
            }, f, ensure_ascii=False, indent=2)

    def carregar(self):
        if not os.path.exists(self.data_file):
            return
        with open(self.data_file, "r", encoding="utf-8") as f:
            dados = json.load(f)
        self.usuarios = {u["usuario_id"]: Usuario.de_dict(u) for u in dados.get("usuarios", [])}
        self.grupos = {g["grupo_id"]: Grupo.de_dict(g) for g in dados.get("grupos", [])}
        self.despesas = {d["despesa_id"]: despesa_de_dict(d) for d in dados.get("despesas", [])}
        self.pagamentos = {p["pagamento_id"]: Pagamento(**p) for p in dados.get("pagamentos", [])}
        cont = dados.get("contadores", {})
        self.proximo_usuario_id = cont.get("proximo_usuario_id", 1)
        self.proximo_grupo_id = cont.get("proximo_grupo_id", 1)
        self.proxima_despesa_id = cont.get("proxima_despesa_id", 1)

    def resetar(self):
        self.usuarios = {}
        self.grupos = {}
        self.despesas = {}
        self.pagamentos = {}
        self.proximo_usuario_id = 1
        self.proximo_grupo_id = 1
        self.proxima_despesa_id = 1
        self.salvar()

    def registrar_usuario(self, nome: str, email: str, senha: str, pix: str = "") -> Usuario:
        if any(u.email == email.lower().strip() for u in self.usuarios.values()):
            raise ValueError("E-mail já cadastrado.")
        usuario = Usuario(self.proximo_usuario_id, nome, email, senha, pix)
        self.usuarios[usuario.usuario_id] = usuario
        self.proximo_usuario_id += 1
        self.salvar()
        return usuario

    def criar_grupo(self, nome: str, membros: List[int]) -> Grupo:
        grupo = Grupo(self.proximo_grupo_id, nome, membros)
        self.grupos[grupo.grupo_id] = grupo
        self.proximo_grupo_id += 1
        self.salvar()
        return grupo

    def criar_despesa_igualitaria(self, grupo_id: int, descricao: str, pago_por: int, total: float,
                                  participantes: List[int], categoria: str = "Outros") -> Despesa:
        grupo = self.grupos[grupo_id]
        despesa = DespesaIgualitaria(
            self.proxima_despesa_id, grupo_id, descricao, pago_por, total, participantes, "BRL", categoria
        )
        self.despesas[despesa.despesa_id] = despesa
        grupo.adicionar_despesa(despesa.despesa_id)
        self.proxima_despesa_id += 1
        self.salvar()
        return despesa

    def despesas_do_grupo(self, grupo_id: int) -> List[Despesa]:
        grupo = self.grupos[grupo_id]
        return [self.despesas[i] for i in grupo.ids_despesas if i in self.despesas]

    def calcular_saldos_grupo(self, grupo_id: int) -> Dict[int, float]:
        grupo = self.grupos[grupo_id]
        saldos = {uid: 0.0 for uid in grupo.membros}
        for despesa in self.despesas_do_grupo(grupo_id):
            cotas = despesa.calcular_cotas()
            for uid, valor in cotas.items():
                saldos[uid] = round(saldos.get(uid, 0.0) - valor, 2)
            saldos[despesa.pago_por] = round(saldos.get(despesa.pago_por, 0.0) + despesa.valor_total(), 2)
        return saldos

    def simplificar_dividas(self, grupo_id: int) -> List[Tuple[int, int, float]]:
        saldos = self.calcular_saldos_grupo(grupo_id)
        credores = []
        devedores = []
        for uid, saldo in saldos.items():
            if saldo > 0:
                credores.append([uid, saldo])
            elif saldo < 0:
                devedores.append([uid, -saldo])

        credores.sort(key=lambda x: x[1], reverse=True)
        devedores.sort(key=lambda x: x[1], reverse=True)

        resultado = []
        i = j = 0
        while i < len(devedores) and j < len(credores):
            valor = round(min(devedores[i][1], credores[j][1]), 2)
            resultado.append((devedores[i][0], credores[j][0], valor))
            devedores[i][1] = round(devedores[i][1] - valor, 2)
            credores[j][1] = round(credores[j][1] - valor, 2)
            if devedores[i][1] <= 0.009:
                i += 1
            if credores[j][1] <= 0.009:
                j += 1
        return resultado

    def resumo_dashboard(self) -> dict:
        total = sum(d.valor_total() for d in self.despesas.values())
        return {
            "usuarios": len(self.usuarios),
            "grupos": len(self.grupos),
            "despesas": len(self.despesas),
            "total": round(total, 2),
        }

    def serializar_usuarios(self) -> List[dict]:
        return [u.para_dict_publico() for u in self.usuarios.values()]

    def serializar_grupo(self, grupo_id: int) -> dict:
        grupo = self.grupos[grupo_id]
        return {
            "grupo_id": grupo.grupo_id,
            "nome": grupo.nome,
            "membros": [
                self.usuarios[uid].para_dict_publico() for uid in grupo.membros if uid in self.usuarios
            ]
        }

    def serializar_grupos(self) -> List[dict]:
        return [self.serializar_grupo(gid) for gid in self.grupos]

    def serializar_despesa(self, despesa_id: int) -> dict:
        despesa = self.despesas[despesa_id]
        grupo = self.grupos[despesa.grupo_id]
        return {
            "despesa_id": despesa.despesa_id,
            "descricao": despesa.descricao,
            "categoria": despesa.categoria,
            "valor": despesa.valor_total(),
            "grupo_id": despesa.grupo_id,
            "grupo_nome": grupo.nome,
            "pago_por": despesa.pago_por,
            "pago_por_nome": self.usuarios[despesa.pago_por].nome,
            "participantes": [
                self.usuarios[uid].nome for uid in despesa.participantes if uid in self.usuarios
            ],
            "criado_em": despesa.criado_em,
        }

    def serializar_despesas(self) -> List[dict]:
        return [self.serializar_despesa(did) for did in self.despesas]

    def serializar_saldos(self, grupo_id: int) -> List[dict]:
        saldos = self.calcular_saldos_grupo(grupo_id)
        resultado = []
        for uid, valor in saldos.items():
            resultado.append({
                "usuario_id": uid,
                "nome": self.usuarios[uid].nome,
                "pix": self.usuarios[uid].pix,
                "saldo": round(valor, 2)
            })
        return resultado

    def serializar_liquidacao(self, grupo_id: int) -> List[dict]:
        rotas = self.simplificar_dividas(grupo_id)
        resultado = []
        for devedor, credor, valor in rotas:
            resultado.append({
                "devedor": self.usuarios[devedor].nome,
                "credor": self.usuarios[credor].nome,
                "pix_credor": self.usuarios[credor].pix,
                "valor": round(valor, 2)
            })
        return resultado

    def popular_demo(self):
        self.resetar()
        u1 = self.registrar_usuario("Jader", "jader@email.com", "123", "jader@pix")
        u2 = self.registrar_usuario("Maria", "maria@email.com", "123", "maria@pix")
        u3 = self.registrar_usuario("João", "joao@email.com", "123", "joao@pix")
        u4 = self.registrar_usuario("Ana", "ana@email.com", "123", "ana@pix")

        g1 = self.criar_grupo("Jantar de sábado", [u1.usuario_id, u2.usuario_id, u3.usuario_id, u4.usuario_id])
        g2 = self.criar_grupo("Viagem de praia", [u1.usuario_id, u2.usuario_id, u4.usuario_id])

        self.criar_despesa_igualitaria(g1.grupo_id, "Conta do restaurante", u1.usuario_id, 200, [u1.usuario_id, u2.usuario_id, u3.usuario_id, u4.usuario_id], "Alimentação")
        self.criar_despesa_igualitaria(g1.grupo_id, "Uber ida", u3.usuario_id, 28, [u1.usuario_id, u2.usuario_id, u3.usuario_id, u4.usuario_id], "Transporte")
        self.criar_despesa_igualitaria(g2.grupo_id, "Reserva da pousada", u4.usuario_id, 450, [u1.usuario_id, u2.usuario_id, u4.usuario_id], "Viagem")
