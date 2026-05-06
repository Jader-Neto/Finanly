
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import secrets
import string
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def nome_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def gerar_chave_usuario() -> str:
    alfabeto = string.ascii_uppercase + string.digits
    bloco1 = "".join(secrets.choice(alfabeto) for _ in range(4))
    bloco2 = "".join(secrets.choice(alfabeto) for _ in range(4))
    bloco3 = "".join(secrets.choice(alfabeto) for _ in range(4))
    return f"FIN-{bloco1}-{bloco2}-{bloco3}"


class ErroValidacao(ValueError):
    pass


class RepositorioJSON:
    def __init__(self, arquivo_dados: str, pasta_backups: str):
        self.arquivo_dados = Path(arquivo_dados)
        self.pasta_backups = Path(pasta_backups)
        self.arquivo_dados.parent.mkdir(parents=True, exist_ok=True)
        self.pasta_backups.mkdir(parents=True, exist_ok=True)

    def estrutura_vazia(self) -> dict:
        return {
            "meta": {
                "app": "Finanly",
                "schema_version": 4,
                "criado_em": agora(),
                "atualizado_em": agora()
            },
            "usuarios": [],
            "grupos": [],
            "despesas": [],
            "contadores": {
                "proximo_usuario_id": 1,
                "proximo_grupo_id": 1,
                "proxima_despesa_id": 1
            }
        }

    def carregar(self) -> dict:
        if not self.arquivo_dados.exists():
            dados = self.estrutura_vazia()
            self.salvar(dados, criar_backup=False)
            return dados

        with open(self.arquivo_dados, "r", encoding="utf-8") as f:
            dados = json.load(f)

        return self.migrar(dados)

    def migrar(self, dados: dict) -> dict:
        dados.setdefault("meta", {
            "app": "Finanly",
            "schema_version": 4,
            "criado_em": agora(),
            "atualizado_em": agora(),
            "migrado": True
        })
        dados.setdefault("usuarios", [])
        dados.setdefault("grupos", [])
        dados.setdefault("despesas", [])
        dados.setdefault("contadores", {})
        dados["contadores"].setdefault("proximo_usuario_id", 1)
        dados["contadores"].setdefault("proximo_grupo_id", 1)
        dados["contadores"].setdefault("proxima_despesa_id", 1)

        for usuario in dados["usuarios"]:
            usuario.setdefault("chave_publica", gerar_chave_usuario())
            usuario.setdefault("contatos", [])
            usuario.setdefault("ativo", True)

        for grupo in dados["grupos"]:
            grupo.setdefault("dono_id", grupo.get("membros", [None])[0])
            grupo.setdefault("ativo", True)

        for despesa in dados["despesas"]:
            despesa.setdefault("dono_id", None)
            despesa.setdefault("anexo", None)
            despesa.setdefault("ativo", True)

        return dados

    def salvar(self, dados: dict, criar_backup: bool = True):
        if criar_backup and self.arquivo_dados.exists():
            self.criar_backup_automatico()

        dados.setdefault("meta", {})
        dados["meta"]["app"] = "Finanly"
        dados["meta"]["schema_version"] = 4
        dados["meta"]["atualizado_em"] = agora()

        fd, temp_path = tempfile.mkstemp(prefix="finanly_", suffix=".json", dir=str(self.arquivo_dados.parent))

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                json.dump(dados, tmp, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.arquivo_dados)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def criar_backup_automatico(self) -> str:
        destino = self.pasta_backups / f"backup_auto_{nome_timestamp()}.json"
        shutil.copy2(self.arquivo_dados, destino)
        self.limitar_backups(10)
        return str(destino)

    def criar_backup_manual(self) -> str:
        if not self.arquivo_dados.exists():
            self.salvar(self.estrutura_vazia(), criar_backup=False)
        destino = self.pasta_backups / f"backup_manual_{nome_timestamp()}.json"
        shutil.copy2(self.arquivo_dados, destino)
        return str(destino)

    def limitar_backups(self, maximo: int):
        arquivos = sorted(self.pasta_backups.glob("*.json"), reverse=True)
        for arquivo in arquivos[maximo:]:
            arquivo.unlink(missing_ok=True)


class Usuario:
    def __init__(self, usuario_id: int, nome: str, email: str, senha: str, pix: str = "", chave_publica: Optional[str] = None):
        self.usuario_id = usuario_id
        self.nome = nome.strip()
        self.email = email.lower().strip()
        self.__hash_senha = hash_senha(senha)
        self.__pix = pix.strip()
        self.chave_publica = chave_publica or gerar_chave_usuario()
        self.contatos: List[int] = []
        self.criado_em = agora()
        self.atualizado_em = agora()
        self.ativo = True

    @property
    def pix(self) -> str:
        return self.__pix

    def verificar_senha(self, senha: str) -> bool:
        return self.__hash_senha == hash_senha(senha)

    def adicionar_contato(self, contato_id: int):
        if contato_id != self.usuario_id and contato_id not in self.contatos:
            self.contatos.append(contato_id)
            self.atualizado_em = agora()

    def atualizar(self, nome: Optional[str] = None, email: Optional[str] = None, pix: Optional[str] = None):
        if nome is not None:
            self.nome = nome.strip()
        if email is not None:
            self.email = email.lower().strip()
        if pix is not None:
            self.__pix = pix.strip()
        self.atualizado_em = agora()

    def para_dict(self) -> dict:
        return {
            "usuario_id": self.usuario_id,
            "nome": self.nome,
            "email": self.email,
            "hash_senha": self._Usuario__hash_senha,
            "pix": self._Usuario__pix,
            "chave_publica": self.chave_publica,
            "contatos": self.contatos,
            "criado_em": self.criado_em,
            "atualizado_em": self.atualizado_em,
            "ativo": self.ativo
        }

    def para_dict_publico(self) -> dict:
        return {
            "usuario_id": self.usuario_id,
            "nome": self.nome,
            "email": self.email,
            "pix": self.pix,
            "chave_publica": self.chave_publica,
            "criado_em": self.criado_em,
            "atualizado_em": self.atualizado_em,
            "ativo": self.ativo
        }

    @classmethod
    def de_dict(cls, dados: dict) -> "Usuario":
        obj = cls(
            dados["usuario_id"],
            dados["nome"],
            dados["email"],
            "temp",
            dados.get("pix", ""),
            dados.get("chave_publica")
        )
        obj._Usuario__hash_senha = dados["hash_senha"]
        obj.contatos = dados.get("contatos", [])
        obj.criado_em = dados.get("criado_em", agora())
        obj.atualizado_em = dados.get("atualizado_em", obj.criado_em)
        obj.ativo = dados.get("ativo", True)
        return obj


class Grupo:
    def __init__(self, grupo_id: int, dono_id: int, nome: str, membros: List[int]):
        self.grupo_id = grupo_id
        self.dono_id = dono_id
        self.nome = nome.strip()
        self.membros = list(dict.fromkeys([dono_id] + membros))
        self.ids_despesas: List[int] = []
        self.criado_em = agora()
        self.atualizado_em = agora()
        self.ativo = True

    def pertence_ao_usuario(self, usuario_id: int) -> bool:
        return usuario_id == self.dono_id or usuario_id in self.membros

    def adicionar_despesa(self, despesa_id: int):
        if despesa_id not in self.ids_despesas:
            self.ids_despesas.append(despesa_id)
            self.atualizado_em = agora()

    def remover_despesa(self, despesa_id: int):
        if despesa_id in self.ids_despesas:
            self.ids_despesas.remove(despesa_id)
            self.atualizado_em = agora()

    def para_dict(self) -> dict:
        return {
            "grupo_id": self.grupo_id,
            "dono_id": self.dono_id,
            "nome": self.nome,
            "membros": self.membros,
            "ids_despesas": self.ids_despesas,
            "criado_em": self.criado_em,
            "atualizado_em": self.atualizado_em,
            "ativo": self.ativo
        }

    @classmethod
    def de_dict(cls, dados: dict) -> "Grupo":
        obj = cls(dados["grupo_id"], dados.get("dono_id"), dados["nome"], dados.get("membros", []))
        obj.ids_despesas = dados.get("ids_despesas", [])
        obj.criado_em = dados.get("criado_em", agora())
        obj.atualizado_em = dados.get("atualizado_em", obj.criado_em)
        obj.ativo = dados.get("ativo", True)
        return obj


class Despesa(ABC):
    def __init__(self, despesa_id: int, dono_id: int, grupo_id: int, descricao: str, pago_por: int,
                 categoria: str = "Outros", anexo: Optional[str] = None):
        self.despesa_id = despesa_id
        self.dono_id = dono_id
        self.grupo_id = grupo_id
        self.descricao = descricao.strip()
        self.pago_por = pago_por
        self.categoria = categoria
        self.anexo = anexo
        self.criado_em = agora()
        self.atualizado_em = agora()
        self.ativo = True

    @abstractmethod
    def calcular_cotas(self) -> Dict[int, float]:
        pass

    @abstractmethod
    def valor_total(self) -> float:
        pass

    @abstractmethod
    def para_dict(self) -> dict:
        pass

    def remover(self):
        self.ativo = False
        self.atualizado_em = agora()


class DespesaIgualitaria(Despesa):
    def __init__(self, despesa_id: int, dono_id: int, grupo_id: int, descricao: str, pago_por: int,
                 total: float, participantes: List[int], categoria: str = "Outros", anexo: Optional[str] = None):
        super().__init__(despesa_id, dono_id, grupo_id, descricao, pago_por, categoria, anexo)
        self.total = round(float(total), 2)
        self.participantes = list(dict.fromkeys(participantes))

    def calcular_cotas(self) -> Dict[int, float]:
        cota = round(self.total / len(self.participantes), 2)
        cotas = {uid: cota for uid in self.participantes}
        diff = round(self.total - sum(cotas.values()), 2)
        if diff:
            cotas[self.participantes[-1]] = round(cotas[self.participantes[-1]] + diff, 2)
        return cotas

    def valor_total(self) -> float:
        return self.total

    def para_dict(self) -> dict:
        return {
            "tipo": "DespesaIgualitaria",
            "despesa_id": self.despesa_id,
            "dono_id": self.dono_id,
            "grupo_id": self.grupo_id,
            "descricao": self.descricao,
            "pago_por": self.pago_por,
            "total": self.total,
            "participantes": self.participantes,
            "categoria": self.categoria,
            "anexo": self.anexo,
            "criado_em": self.criado_em,
            "atualizado_em": self.atualizado_em,
            "ativo": self.ativo
        }

    @classmethod
    def de_dict(cls, dados: dict) -> "DespesaIgualitaria":
        obj = cls(
            dados["despesa_id"],
            dados.get("dono_id"),
            dados["grupo_id"],
            dados["descricao"],
            dados["pago_por"],
            dados["total"],
            dados["participantes"],
            dados.get("categoria", "Outros"),
            dados.get("anexo")
        )
        obj.criado_em = dados.get("criado_em", agora())
        obj.atualizado_em = dados.get("atualizado_em", obj.criado_em)
        obj.ativo = dados.get("ativo", True)
        return obj


def despesa_de_dict(dados: dict) -> Despesa:
    return DespesaIgualitaria.de_dict(dados)


class SistemaFinanly:
    def __init__(self, arquivo_dados: str, pasta_backups: str):
        self.repositorio = RepositorioJSON(arquivo_dados, pasta_backups)
        self.usuarios: Dict[int, Usuario] = {}
        self.grupos: Dict[int, Grupo] = {}
        self.despesas: Dict[int, Despesa] = {}
        self.proximo_usuario_id = 1
        self.proximo_grupo_id = 1
        self.proxima_despesa_id = 1
        self.carregar()

    def carregar(self):
        dados = self.repositorio.carregar()
        self.usuarios = {u["usuario_id"]: Usuario.de_dict(u) for u in dados.get("usuarios", [])}
        self.grupos = {g["grupo_id"]: Grupo.de_dict(g) for g in dados.get("grupos", [])}
        self.despesas = {d["despesa_id"]: despesa_de_dict(d) for d in dados.get("despesas", [])}
        cont = dados.get("contadores", {})
        self.proximo_usuario_id = cont.get("proximo_usuario_id", 1)
        self.proximo_grupo_id = cont.get("proximo_grupo_id", 1)
        self.proxima_despesa_id = cont.get("proxima_despesa_id", 1)

    def salvar(self):
        self.repositorio.salvar({
            "usuarios": [u.para_dict() for u in self.usuarios.values()],
            "grupos": [g.para_dict() for g in self.grupos.values()],
            "despesas": [d.para_dict() for d in self.despesas.values()],
            "contadores": {
                "proximo_usuario_id": self.proximo_usuario_id,
                "proximo_grupo_id": self.proximo_grupo_id,
                "proxima_despesa_id": self.proxima_despesa_id
            }
        })

    def obter_usuario(self, usuario_id: int) -> Optional[Usuario]:
        usuario = self.usuarios.get(usuario_id)
        if not usuario or not usuario.ativo:
            return None
        return usuario

    def autenticar(self, email: str, senha: str) -> Usuario:
        email = email.lower().strip()
        for usuario in self.usuarios.values():
            if usuario.email == email and usuario.ativo and usuario.verificar_senha(senha):
                return usuario
        raise ErroValidacao("E-mail ou senha inválidos.")

    def usuarios_ativos(self) -> List[Usuario]:
        return [u for u in self.usuarios.values() if u.ativo]

    def validar_usuario(self, usuario_id: int):
        if usuario_id not in self.usuarios or not self.usuarios[usuario_id].ativo:
            raise ErroValidacao("Usuário não encontrado.")

    def registrar_usuario(self, nome: str, email: str, senha: str, pix: str = "") -> Usuario:
        if not nome.strip():
            raise ErroValidacao("Nome é obrigatório.")
        if "@" not in email:
            raise ErroValidacao("E-mail inválido.")
        if len(senha) < 4:
            raise ErroValidacao("A senha deve ter pelo menos 4 caracteres.")
        for usuario in self.usuarios_ativos():
            if usuario.email == email.lower().strip():
                raise ErroValidacao("E-mail já cadastrado.")

        chave = gerar_chave_usuario()
        while any(u.chave_publica == chave for u in self.usuarios.values()):
            chave = gerar_chave_usuario()

        usuario = Usuario(self.proximo_usuario_id, nome, email, senha, pix, chave)
        self.usuarios[usuario.usuario_id] = usuario
        self.proximo_usuario_id += 1
        self.salvar()
        return usuario

    def buscar_usuario_por_chave(self, chave: str) -> Usuario:
        chave = chave.strip().upper()
        for usuario in self.usuarios_ativos():
            if usuario.chave_publica.upper() == chave:
                return usuario
        raise ErroValidacao("Nenhum usuário encontrado com essa chave.")

    def adicionar_contato_por_chave(self, usuario_id: int, chave: str) -> Usuario:
        self.validar_usuario(usuario_id)
        contato = self.buscar_usuario_por_chave(chave)
        if contato.usuario_id == usuario_id:
            raise ErroValidacao("Você não pode adicionar a si mesmo.")
        self.usuarios[usuario_id].adicionar_contato(contato.usuario_id)
        contato.adicionar_contato(usuario_id)
        self.salvar()
        return contato

    def contatos_do_usuario(self, usuario_id: int) -> List[Usuario]:
        self.validar_usuario(usuario_id)
        usuario = self.usuarios[usuario_id]
        ids = [usuario_id] + usuario.contatos
        return [self.usuarios[i] for i in ids if i in self.usuarios and self.usuarios[i].ativo]

    def grupos_do_usuario(self, usuario_id: int) -> List[Grupo]:
        return [g for g in self.grupos.values() if g.ativo and g.pertence_ao_usuario(usuario_id)]

    def validar_grupo_acesso(self, usuario_id: int, grupo_id: int):
        if grupo_id not in self.grupos or not self.grupos[grupo_id].ativo:
            raise ErroValidacao("Grupo não encontrado.")
        if not self.grupos[grupo_id].pertence_ao_usuario(usuario_id):
            raise ErroValidacao("Você não tem acesso a este grupo.")

    def criar_grupo(self, dono_id: int, nome: str, membros: List[int]) -> Grupo:
        self.validar_usuario(dono_id)
        if not nome.strip():
            raise ErroValidacao("Nome do grupo é obrigatório.")

        contatos_permitidos = {u.usuario_id for u in self.contatos_do_usuario(dono_id)}
        membros_validos = []
        for uid in membros:
            if uid not in contatos_permitidos:
                raise ErroValidacao("Você só pode adicionar contatos ao evento.")
            membros_validos.append(uid)

        grupo = Grupo(self.proximo_grupo_id, dono_id, nome, membros_validos)
        self.grupos[grupo.grupo_id] = grupo
        self.proximo_grupo_id += 1
        self.salvar()
        return grupo

    def despesas_do_usuario(self, usuario_id: int) -> List[Despesa]:
        grupos = {g.grupo_id for g in self.grupos_do_usuario(usuario_id)}
        return [d for d in self.despesas.values() if d.ativo and d.grupo_id in grupos]

    def criar_despesa_igualitaria(self, usuario_id: int, grupo_id: int, descricao: str, pago_por: int,
                                  total: float, participantes: List[int], categoria: str, anexo: Optional[str]) -> Despesa:
        self.validar_grupo_acesso(usuario_id, grupo_id)
        grupo = self.grupos[grupo_id]
        if total <= 0:
            raise ErroValidacao("Valor precisa ser maior que zero.")
        if pago_por not in grupo.membros:
            raise ErroValidacao("Cobrador precisa estar no grupo.")
        if not participantes:
            raise ErroValidacao("Despesa precisa ter participantes.")
        for uid in participantes:
            if uid not in grupo.membros:
                raise ErroValidacao("Todos os participantes precisam estar no grupo.")

        despesa = DespesaIgualitaria(
            self.proxima_despesa_id,
            usuario_id,
            grupo_id,
            descricao,
            pago_por,
            total,
            participantes,
            categoria,
            anexo
        )
        self.despesas[despesa.despesa_id] = despesa
        grupo.adicionar_despesa(despesa.despesa_id)
        self.proxima_despesa_id += 1
        self.salvar()
        return despesa

    def remover_despesa(self, usuario_id: int, despesa_id: int):
        if despesa_id not in self.despesas or not self.despesas[despesa_id].ativo:
            raise ErroValidacao("Despesa não encontrada.")
        despesa = self.despesas[despesa_id]
        self.validar_grupo_acesso(usuario_id, despesa.grupo_id)
        despesa.remover()
        if despesa.grupo_id in self.grupos:
            self.grupos[despesa.grupo_id].remover_despesa(despesa_id)
        self.salvar()

    def calcular_saldos_grupo(self, usuario_id: int, grupo_id: int) -> Dict[int, float]:
        self.validar_grupo_acesso(usuario_id, grupo_id)
        grupo = self.grupos[grupo_id]
        saldos = {uid: 0.0 for uid in grupo.membros if uid in self.usuarios and self.usuarios[uid].ativo}
        for despesa in [d for d in self.despesas.values() if d.ativo and d.grupo_id == grupo_id]:
            cotas = despesa.calcular_cotas()
            for uid, valor in cotas.items():
                saldos[uid] = round(saldos.get(uid, 0.0) - valor, 2)
            saldos[despesa.pago_por] = round(saldos.get(despesa.pago_por, 0.0) + despesa.valor_total(), 2)
        return saldos

    def simplificar_dividas(self, usuario_id: int, grupo_id: int) -> List[Tuple[int, int, float]]:
        saldos = self.calcular_saldos_grupo(usuario_id, grupo_id)
        credores, devedores = [], []
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

    def resumo_dashboard(self, usuario_id: int) -> dict:
        despesas = self.despesas_do_usuario(usuario_id)
        return {
            "usuarios": len(self.contatos_do_usuario(usuario_id)),
            "grupos": len(self.grupos_do_usuario(usuario_id)),
            "despesas": len(despesas),
            "total": round(sum(d.valor_total() for d in despesas), 2)
        }

    def serializar_contatos(self, usuario_id: int) -> List[dict]:
        return [u.para_dict_publico() for u in self.contatos_do_usuario(usuario_id)]

    def serializar_grupo(self, grupo_id: int, usuario_id: int) -> dict:
        self.validar_grupo_acesso(usuario_id, grupo_id)
        grupo = self.grupos[grupo_id]
        return {
            "grupo_id": grupo.grupo_id,
            "dono_id": grupo.dono_id,
            "nome": grupo.nome,
            "criado_em": grupo.criado_em,
            "atualizado_em": grupo.atualizado_em,
            "membros": [
                self.usuarios[uid].para_dict_publico()
                for uid in grupo.membros
                if uid in self.usuarios and self.usuarios[uid].ativo
            ]
        }

    def serializar_grupos(self, usuario_id: int) -> List[dict]:
        return [self.serializar_grupo(g.grupo_id, usuario_id) for g in self.grupos_do_usuario(usuario_id)]

    def serializar_despesa(self, despesa_id: int, usuario_id: int) -> dict:
        despesa = self.despesas[despesa_id]
        self.validar_grupo_acesso(usuario_id, despesa.grupo_id)
        grupo = self.grupos[despesa.grupo_id]
        cobrador = self.usuarios[despesa.pago_por]
        return {
            "despesa_id": despesa.despesa_id,
            "descricao": despesa.descricao,
            "categoria": despesa.categoria,
            "valor": despesa.valor_total(),
            "grupo_id": despesa.grupo_id,
            "grupo_nome": grupo.nome,
            "pago_por": despesa.pago_por,
            "pago_por_nome": cobrador.nome,
            "pago_por_pix": cobrador.pix,
            "participantes": [
                self.usuarios[uid].nome
                for uid in despesa.participantes
                if uid in self.usuarios and self.usuarios[uid].ativo
            ],
            "anexo": despesa.anexo,
            "anexo_url": f"/uploads/{despesa.anexo}" if despesa.anexo else None,
            "pix_link": f"pix://pagamento/{cobrador.pix}" if cobrador.pix else "",
            "criado_em": despesa.criado_em,
            "atualizado_em": despesa.atualizado_em
        }

    def serializar_despesas(self, usuario_id: int) -> List[dict]:
        return [self.serializar_despesa(d.despesa_id, usuario_id) for d in self.despesas_do_usuario(usuario_id)]

    def serializar_saldos(self, usuario_id: int, grupo_id: int) -> List[dict]:
        saldos = self.calcular_saldos_grupo(usuario_id, grupo_id)
        return [
            {
                "usuario_id": uid,
                "nome": self.usuarios[uid].nome,
                "pix": self.usuarios[uid].pix,
                "saldo": round(valor, 2)
            }
            for uid, valor in saldos.items()
        ]

    def serializar_liquidacao(self, usuario_id: int, grupo_id: int) -> List[dict]:
        return [
            {
                "devedor": self.usuarios[devedor].nome,
                "credor": self.usuarios[credor].nome,
                "pix_credor": self.usuarios[credor].pix,
                "valor": round(valor, 2)
            }
            for devedor, credor, valor in self.simplificar_dividas(usuario_id, grupo_id)
        ]

    def popular_demo(self, usuario_id: int):
        self.validar_usuario(usuario_id)
        maria = self.registrar_usuario(f"Maria Demo {usuario_id}", f"maria{usuario_id}@demo.com", "1234", f"maria{usuario_id}@pix")
        joao = self.registrar_usuario(f"João Demo {usuario_id}", f"joao{usuario_id}@demo.com", "1234", f"joao{usuario_id}@pix")
        ana = self.registrar_usuario(f"Ana Demo {usuario_id}", f"ana{usuario_id}@demo.com", "1234", f"ana{usuario_id}@pix")
        self.usuarios[usuario_id].adicionar_contato(maria.usuario_id)
        self.usuarios[usuario_id].adicionar_contato(joao.usuario_id)
        self.usuarios[usuario_id].adicionar_contato(ana.usuario_id)
        maria.adicionar_contato(usuario_id)
        joao.adicionar_contato(usuario_id)
        ana.adicionar_contato(usuario_id)
        grupo = self.criar_grupo(usuario_id, "Jantar de sábado", [maria.usuario_id, joao.usuario_id, ana.usuario_id])
        self.criar_despesa_igualitaria(usuario_id, grupo.grupo_id, "Conta do restaurante", usuario_id, 200, grupo.membros, "Alimentação", None)
        self.criar_despesa_igualitaria(usuario_id, grupo.grupo_id, "Uber ida", joao.usuario_id, 28, grupo.membros, "Transporte", None)
