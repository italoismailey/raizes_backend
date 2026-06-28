"""
Schemas Pydantic — contratos de entrada e saída da API.
Separa o que o cliente envia do que o banco armazena.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.domain.models.models import (
    CanalPedido,
    PerfilUsuario,
    StatusPagamento,
    StatusPedido,
    TipoEventoFidelidade,
    TipoMovimentoEstoque,
)


# ===========================================================================
# AUTH
# ===========================================================================

class LoginInput(BaseModel):
    email: EmailStr
    senha: str


class TokenOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
    perfil: str
    usuario_id: int
    nome: str


# ===========================================================================
# USUARIO
# ===========================================================================

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    perfil: PerfilUsuario = PerfilUsuario.CLIENTE
    consentimento_fidelidade: bool = False
    consentimento_marketing: bool = False

    @field_validator("senha")
    @classmethod
    def senha_forte(cls, v):
        if len(v) < 6:
            raise ValueError("A senha deve ter pelo menos 6 caracteres.")
        return v


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    consentimento_fidelidade: Optional[bool] = None
    consentimento_marketing: Optional[bool] = None
    ativo: Optional[bool] = None


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    perfil: PerfilUsuario
    ativo: bool
    consentimento_fidelidade: bool
    consentimento_marketing: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# UNIDADE
# ===========================================================================

class UnidadeOut(BaseModel):
    id: int
    nome: str
    cidade: str
    estado: str
    endereco: str
    ativa: bool

    model_config = {"from_attributes": True}


# ===========================================================================
# PRODUTO
# ===========================================================================

class ProdutoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    categoria: Optional[str] = None

    @field_validator("preco")
    @classmethod
    def preco_positivo(cls, v):
        if v <= 0:
            raise ValueError("O preço deve ser maior que zero.")
        return v


class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    categoria: Optional[str] = None
    ativo: Optional[bool] = None


class ProdutoOut(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]
    preco: float
    categoria: Optional[str]
    ativo: bool

    model_config = {"from_attributes": True}


class CardapioItemOut(BaseModel):
    produto_id: int
    nome: str
    descricao: Optional[str]
    preco: float           # preço local se definido, senão o padrão
    categoria: Optional[str]
    disponivel: bool

    model_config = {"from_attributes": True}


# ===========================================================================
# ESTOQUE
# ===========================================================================

class EstoqueMovimentoCreate(BaseModel):
    unidade_id: int
    produto_id: int
    tipo: TipoMovimentoEstoque
    quantidade: int
    motivo: Optional[str] = None

    @field_validator("quantidade")
    @classmethod
    def quantidade_positiva(cls, v):
        if v <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        return v


class EstoqueMovimentoOut(BaseModel):
    id: int
    unidade_id: int
    produto_id: int
    tipo: TipoMovimentoEstoque
    quantidade: int
    motivo: Optional[str]
    criado_em: datetime

    model_config = {"from_attributes": True}


class EstoqueSaldoOut(BaseModel):
    unidade_id: int
    produto_id: int
    produto_nome: str
    saldo: int


# ===========================================================================
# PEDIDO
# ===========================================================================

class ItemPedidoCreate(BaseModel):
    produto_id: int
    quantidade: int

    @field_validator("quantidade")
    @classmethod
    def qtd_positiva(cls, v):
        if v <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        return v


class PedidoCreate(BaseModel):
    unidade_id: int
    canal_pedido: CanalPedido
    itens: List[ItemPedidoCreate]
    observacao: Optional[str] = None


class ItemPedidoOut(BaseModel):
    id: int
    produto_id: int
    quantidade: int
    preco_unitario: float
    subtotal: float

    model_config = {"from_attributes": True}


class PedidoOut(BaseModel):
    id: int
    cliente_id: Optional[int]
    unidade_id: int
    canal_pedido: CanalPedido
    status: StatusPedido
    total: float
    observacao: Optional[str]
    itens: List[ItemPedidoOut]
    criado_em: datetime

    model_config = {"from_attributes": True}


class PedidoStatusUpdate(BaseModel):
    status: StatusPedido


# ===========================================================================
# PAGAMENTO (mock)
# ===========================================================================

class PagamentoInput(BaseModel):
    pedido_id: int
    forma_pagamento: str  # ex.: "PIX", "CARTAO", "MOCK"


class PagamentoOut(BaseModel):
    id: int
    pedido_id: int
    forma_pagamento: str
    status: StatusPagamento
    gateway_referencia: Optional[str]
    gateway_mensagem: Optional[str]

    model_config = {"from_attributes": True}


# ===========================================================================
# FIDELIDADE
# ===========================================================================

class ResgateInput(BaseModel):
    pontos: int

    @field_validator("pontos")
    @classmethod
    def pontos_positivos(cls, v):
        if v <= 0:
            raise ValueError("A quantidade de pontos deve ser maior que zero.")
        return v


class PontosSaldoOut(BaseModel):
    usuario_id: int
    saldo: int

    model_config = {"from_attributes": True}


class HistoricoFidelidadeOut(BaseModel):
    id: int
    tipo: TipoEventoFidelidade
    pontos: int
    descricao: Optional[str]
    criado_em: datetime

    model_config = {"from_attributes": True}
