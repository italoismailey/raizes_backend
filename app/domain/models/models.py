"""
models.py — Entidades do domínio (tabelas do banco de dados)
Raízes do Nordeste — Projeto Back-End
Autor: Italo Ismailey G Durante | RU: 4471904 | UNINTER 2026

Modelei as entidades com base no estudo de caso da rede Raízes do Nordeste.
Cada classe representa uma tabela no banco. Usei SQLAlchemy ORM para
manter o código desacoplado do banco — se precisar trocar SQLite por
PostgreSQL, só muda a URL de conexão.

Entidades principais:
  - Usuario          : clientes, atendentes, gerentes e admins
  - Unidade          : cada lanchonete da rede
  - Produto          : itens do cardápio
  - CardapioItem     : disponibilidade de produto por unidade
  - EstoqueMovimento : entradas e saídas de estoque
  - Pedido           : pedido realizado em qualquer canal
  - ItemPedido       : itens de um pedido
  - Pagamento        : registro do pagamento (mock)
  - PontosFidelidade : saldo de pontos do cliente
  - HistoricoFidelidade : extrato de pontos
  - LogAuditoria     : ações sensíveis (LGPD)
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float,
    ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.infrastructure.database.session import Base


# ---------------------------------------------------------------------------
# Enumerações — uso Enum para garantir que só valores válidos entrem no banco
# ---------------------------------------------------------------------------

class PerfilUsuario(str, enum.Enum):
    CLIENTE    = "CLIENTE"
    ATENDENTE  = "ATENDENTE"
    COZINHA    = "COZINHA"
    GERENTE    = "GERENTE"
    ADMIN      = "ADMIN"


class CanalPedido(str, enum.Enum):
    """
    Representa a multicanalidade da rede.
    Um pedido pode vir do App, Totem, Balcão, Pickup ou Web.
    """
    APP    = "APP"
    TOTEM  = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB    = "WEB"


class StatusPedido(str, enum.Enum):
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    PAGAMENTO_CONFIRMADO = "PAGAMENTO_CONFIRMADO"
    EM_PREPARO           = "EM_PREPARO"
    PRONTO               = "PRONTO"
    ENTREGUE             = "ENTREGUE"
    CANCELADO            = "CANCELADO"


class StatusPagamento(str, enum.Enum):
    PENDENTE  = "PENDENTE"
    APROVADO  = "APROVADO"
    RECUSADO  = "RECUSADO"


class TipoMovimentoEstoque(str, enum.Enum):
    ENTRADA = "ENTRADA"
    SAIDA   = "SAIDA"


class TipoEventoFidelidade(str, enum.Enum):
    GANHO   = "GANHO"
    RESGATE = "RESGATE"


# ---------------------------------------------------------------------------
# Mixin de timestamps — reutilizado em todas as entidades principais
# ---------------------------------------------------------------------------

class TimestampMixin:
    criado_em    = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Usuario
# ---------------------------------------------------------------------------

class Usuario(TimestampMixin, Base):
    __tablename__ = "usuarios"

    id      = Column(Integer, primary_key=True, index=True)
    nome    = Column(String(120), nullable=False)
    email   = Column(String(180), unique=True, nullable=False, index=True)
    senha_hash = Column(String(256), nullable=False)  # bcrypt — nunca texto puro

    perfil  = Column(Enum(PerfilUsuario), nullable=False, default=PerfilUsuario.CLIENTE)
    ativo   = Column(Boolean, default=True, nullable=False)

    # Campos de consentimento exigidos pela LGPD
    consentimento_fidelidade  = Column(Boolean, default=False, nullable=False)
    consentimento_marketing   = Column(Boolean, default=False, nullable=False)

    pedidos              = relationship("Pedido", back_populates="cliente")
    pontos_fidelidade    = relationship("PontosFidelidade", back_populates="usuario", uselist=False)
    historico_fidelidade = relationship("HistoricoFidelidade", back_populates="usuario")

    def __repr__(self):
        return f"<Usuario id={self.id} email={self.email} perfil={self.perfil}>"


# ---------------------------------------------------------------------------
# Unidade
# ---------------------------------------------------------------------------

class Unidade(TimestampMixin, Base):
    __tablename__ = "unidades"

    id       = Column(Integer, primary_key=True, index=True)
    nome     = Column(String(120), nullable=False)
    cidade   = Column(String(100), nullable=False)
    estado   = Column(String(2),   nullable=False)
    endereco = Column(String(250), nullable=False)
    ativa    = Column(Boolean, default=True, nullable=False)

    cardapio_itens      = relationship("CardapioItem",      back_populates="unidade")
    movimentos_estoque  = relationship("EstoqueMovimento",  back_populates="unidade")
    pedidos             = relationship("Pedido",            back_populates="unidade")

    def __repr__(self):
        return f"<Unidade id={self.id} nome={self.nome}>"


# ---------------------------------------------------------------------------
# Produto
# ---------------------------------------------------------------------------

class Produto(TimestampMixin, Base):
    __tablename__ = "produtos"

    id        = Column(Integer, primary_key=True, index=True)
    nome      = Column(String(120), nullable=False)
    descricao = Column(Text,        nullable=True)
    preco     = Column(Float,       nullable=False)
    categoria = Column(String(60),  nullable=True)
    ativo     = Column(Boolean, default=True, nullable=False)

    cardapio_itens = relationship("CardapioItem", back_populates="produto")
    itens_pedido   = relationship("ItemPedido",   back_populates="produto")

    def __repr__(self):
        return f"<Produto id={self.id} nome={self.nome} preco={self.preco}>"


# ---------------------------------------------------------------------------
# CardapioItem — disponibilidade do produto por unidade
# ---------------------------------------------------------------------------

class CardapioItem(TimestampMixin, Base):
    """
    Cada unidade pode ter um subconjunto diferente de produtos disponíveis.
    Isso permite variações regionais — ex.: Canjica junina só em Recife.
    O campo preco_local sobrepõe o preço padrão do produto quando informado.
    """
    __tablename__ = "cardapio_itens"
    __table_args__ = (
        UniqueConstraint("unidade_id", "produto_id", name="uq_cardapio_unidade_produto"),
    )

    id          = Column(Integer, primary_key=True, index=True)
    unidade_id  = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    produto_id  = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    disponivel  = Column(Boolean, default=True, nullable=False)
    preco_local = Column(Float, nullable=True)

    unidade = relationship("Unidade", back_populates="cardapio_itens")
    produto = relationship("Produto", back_populates="cardapio_itens")


# ---------------------------------------------------------------------------
# EstoqueMovimento
# ---------------------------------------------------------------------------

class EstoqueMovimento(TimestampMixin, Base):
    """
    Optei por uma abordagem de livro-caixa: cada linha é uma entrada ou saída.
    O saldo atual é sempre calculado somando ENTRADA − SAIDA.
    Isso facilita auditoria e rastreabilidade de toda a movimentação.
    """
    __tablename__ = "estoque_movimentos"

    id         = Column(Integer, primary_key=True, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    tipo       = Column(Enum(TipoMovimentoEstoque), nullable=False)
    quantidade = Column(Integer, nullable=False)
    motivo     = Column(String(200), nullable=True)

    unidade = relationship("Unidade", back_populates="movimentos_estoque")
    produto = relationship("Produto")


# ---------------------------------------------------------------------------
# Pedido
# ---------------------------------------------------------------------------

class Pedido(TimestampMixin, Base):
    __tablename__ = "pedidos"

    id           = Column(Integer, primary_key=True, index=True)
    cliente_id   = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    unidade_id   = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    canal_pedido = Column(Enum(CanalPedido),   nullable=False)
    status       = Column(Enum(StatusPedido),  nullable=False, default=StatusPedido.AGUARDANDO_PAGAMENTO)
    total        = Column(Float,  nullable=False, default=0.0)
    observacao   = Column(Text,   nullable=True)

    cliente  = relationship("Usuario",   back_populates="pedidos")
    unidade  = relationship("Unidade",   back_populates="pedidos")
    itens    = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    pagamento = relationship("Pagamento", back_populates="pedido", uselist=False)

    def __repr__(self):
        return f"<Pedido id={self.id} status={self.status} canal={self.canal_pedido}>"


# ---------------------------------------------------------------------------
# ItemPedido
# ---------------------------------------------------------------------------

class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id             = Column(Integer, primary_key=True, index=True)
    pedido_id      = Column(Integer, ForeignKey("pedidos.id"),  nullable=False)
    produto_id     = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade     = Column(Integer, nullable=False)
    preco_unitario = Column(Float,   nullable=False)  # preço travado no momento do pedido
    subtotal       = Column(Float,   nullable=False)

    pedido  = relationship("Pedido",  back_populates="itens")
    produto = relationship("Produto", back_populates="itens_pedido")


# ---------------------------------------------------------------------------
# Pagamento (mock)
# ---------------------------------------------------------------------------

class Pagamento(TimestampMixin, Base):
    """
    A API não processa pagamento real — simula um gateway externo.
    Essa decisão foi intencional: em produção, bastaria substituir a
    função mock por uma chamada real à API do gateway (ex.: Stripe, PagSeguro).
    """
    __tablename__ = "pagamentos"

    id                 = Column(Integer, primary_key=True, index=True)
    pedido_id          = Column(Integer, ForeignKey("pedidos.id"), unique=True, nullable=False)
    forma_pagamento    = Column(String(30),  nullable=False)
    status             = Column(Enum(StatusPagamento), nullable=False, default=StatusPagamento.PENDENTE)
    gateway_referencia = Column(String(100), nullable=True)
    gateway_mensagem   = Column(String(250), nullable=True)

    pedido = relationship("Pedido", back_populates="pagamento")


# ---------------------------------------------------------------------------
# Fidelidade
# ---------------------------------------------------------------------------

class PontosFidelidade(Base):
    """Saldo atual de pontos — 1 ponto por real gasto em pedidos aprovados."""
    __tablename__ = "pontos_fidelidade"

    id         = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    saldo      = Column(Integer, default=0, nullable=False)

    usuario = relationship("Usuario", back_populates="pontos_fidelidade")


class HistoricoFidelidade(Base):
    """Extrato completo: cada linha é um ganho ou resgate de pontos."""
    __tablename__ = "historico_fidelidade"

    id         = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    tipo       = Column(Enum(TipoEventoFidelidade), nullable=False)
    pontos     = Column(Integer, nullable=False)
    descricao  = Column(String(200), nullable=True)
    criado_em  = Column(DateTime, default=datetime.utcnow, nullable=False)

    usuario = relationship("Usuario", back_populates="historico_fidelidade")


# ---------------------------------------------------------------------------
# LogAuditoria — conformidade com LGPD
# ---------------------------------------------------------------------------

class LogAuditoria(Base):
    """
    Registra ações sensíveis para fins de auditoria e LGPD.
    Incluí esse modelo porque o roteiro exige rastreabilidade de ações
    como criação de pedido, mudança de status e acesso a dados pessoais.
    """
    __tablename__ = "logs_auditoria"

    id          = Column(Integer, primary_key=True, index=True)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    acao        = Column(String(100), nullable=False)
    entidade    = Column(String(60),  nullable=True)
    entidade_id = Column(Integer,     nullable=True)
    detalhe     = Column(Text,        nullable=True)
    ip          = Column(String(45),  nullable=True)
    criado_em   = Column(DateTime, default=datetime.utcnow, nullable=False)
