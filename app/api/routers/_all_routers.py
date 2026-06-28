"""Routers: unidades e produtos"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import exigir_perfil, get_usuario_atual, registrar_log
from app.api.schemas.schemas import (
    CardapioItemOut, EstoqueMovimentoCreate, EstoqueMovimentoOut,
    EstoqueSaldoOut, HistoricoFidelidadeOut, ItemPedidoOut,
    PagamentoInput, PagamentoOut, PedidoCreate, PedidoOut,
    PedidoStatusUpdate, PontosSaldoOut, ProdutoCreate, ProdutoOut,
    ProdutoUpdate, ResgateInput, UnidadeOut,
)
from app.domain.models.models import (
    CardapioItem, EstoqueMovimento, HistoricoFidelidade, ItemPedido,
    Pagamento, Pedido, PerfilUsuario, PontosFidelidade, Produto,
    StatusPagamento, StatusPedido, TipoEventoFidelidade,
    TipoMovimentoEstoque, Unidade,
)
from app.infrastructure.database.session import get_db

import random
import uuid as _uuid

# ===========================================================================
# UNIDADES
# ===========================================================================

router_unidades = APIRouter()


@router_unidades.get("", response_model=List[UnidadeOut], summary="Listar unidades")
def listar_unidades(db: Session = Depends(get_db), _=Depends(get_usuario_atual)):
    return db.query(Unidade).filter(Unidade.ativa == True).all()


@router_unidades.get("/{unidade_id}", response_model=UnidadeOut, summary="Detalhe de unidade")
def detalhe_unidade(unidade_id: int, db: Session = Depends(get_db), _=Depends(get_usuario_atual)):
    u = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not u:
        raise HTTPException(status_code=404, detail={"error": "UNIDADE_NAO_ENCONTRADA"})
    return u


@router_unidades.get("/{unidade_id}/cardapio", response_model=List[CardapioItemOut], summary="Cardápio da unidade")
def cardapio_unidade(unidade_id: int, db: Session = Depends(get_db), _=Depends(get_usuario_atual)):
    itens = (
        db.query(CardapioItem)
        .filter(CardapioItem.unidade_id == unidade_id)
        .all()
    )
    resultado = []
    for item in itens:
        p = item.produto
        resultado.append(CardapioItemOut(
            produto_id=p.id,
            nome=p.nome,
            descricao=p.descricao,
            preco=item.preco_local if item.preco_local else p.preco,
            categoria=p.categoria,
            disponivel=item.disponivel,
        ))
    return resultado


# ===========================================================================
# PRODUTOS
# ===========================================================================

router_produtos = APIRouter()


@router_produtos.get("", response_model=List[ProdutoOut], summary="Listar produtos")
def listar_produtos(
    categoria: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_usuario_atual),
):
    q = db.query(Produto).filter(Produto.ativo == True)
    if categoria:
        q = q.filter(Produto.categoria == categoria)
    return q.all()


@router_produtos.post(
    "", response_model=ProdutoOut, status_code=201,
    summary="Criar produto (ADMIN/GERENTE)",
)
def criar_produto(
    dados: ProdutoCreate,
    db: Session = Depends(get_db),
    _=Depends(exigir_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE)),
):
    produto = Produto(**dados.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router_produtos.get("/{produto_id}", response_model=ProdutoOut, summary="Detalhe de produto")
def detalhe_produto(produto_id: int, db: Session = Depends(get_db), _=Depends(get_usuario_atual)):
    p = db.query(Produto).filter(Produto.id == produto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail={"error": "PRODUTO_NAO_ENCONTRADO"})
    return p


@router_produtos.put(
    "/{produto_id}", response_model=ProdutoOut,
    summary="Atualizar produto (ADMIN/GERENTE)",
)
def atualizar_produto(
    produto_id: int,
    dados: ProdutoUpdate,
    db: Session = Depends(get_db),
    _=Depends(exigir_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE)),
):
    p = db.query(Produto).filter(Produto.id == produto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail={"error": "PRODUTO_NAO_ENCONTRADO"})
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(p, campo, valor)
    db.commit()
    db.refresh(p)
    return p


# ===========================================================================
# ESTOQUE
# ===========================================================================

router_estoque = APIRouter()


@router_estoque.post(
    "/movimentos", response_model=EstoqueMovimentoOut, status_code=201,
    summary="Registrar movimento de estoque (ADMIN/GERENTE)",
)
def registrar_movimento(
    dados: EstoqueMovimentoCreate,
    db: Session = Depends(get_db),
    _=Depends(exigir_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE)),
):
    # Valida se há saldo suficiente para saída
    if dados.tipo == TipoMovimentoEstoque.SAIDA:
        saldo = _calcular_saldo(db, dados.unidade_id, dados.produto_id)
        if saldo < dados.quantidade:
            raise HTTPException(
                status_code=400,
                detail={"error": "SALDO_INSUFICIENTE", "saldo_atual": saldo},
            )

    mov = EstoqueMovimento(**dados.model_dump())
    db.add(mov)
    db.commit()
    db.refresh(mov)
    return mov


@router_estoque.get(
    "/saldo/{unidade_id}", response_model=List[EstoqueSaldoOut],
    summary="Saldo de estoque por unidade",
)
def saldo_por_unidade(
    unidade_id: int,
    db: Session = Depends(get_db),
    _=Depends(exigir_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE, PerfilUsuario.ATENDENTE)),
):
    produtos = db.query(Produto).filter(Produto.ativo == True).all()
    resultado = []
    for p in produtos:
        saldo = _calcular_saldo(db, unidade_id, p.id)
        resultado.append(EstoqueSaldoOut(
            unidade_id=unidade_id,
            produto_id=p.id,
            produto_nome=p.nome,
            saldo=saldo,
        ))
    return resultado


def _calcular_saldo(db: Session, unidade_id: int, produto_id: int) -> int:
    movimentos = db.query(EstoqueMovimento).filter(
        EstoqueMovimento.unidade_id == unidade_id,
        EstoqueMovimento.produto_id == produto_id,
    ).all()
    saldo = 0
    for m in movimentos:
        if m.tipo == TipoMovimentoEstoque.ENTRADA:
            saldo += m.quantidade
        else:
            saldo -= m.quantidade
    return saldo


# ===========================================================================
# PEDIDOS  (Fluxo crítico: Criar → Pagar → Atualizar status)
# ===========================================================================

router_pedidos = APIRouter()


@router_pedidos.post("", response_model=PedidoOut, status_code=201, summary="Criar pedido")
def criar_pedido(
    dados: PedidoCreate,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_atual),
):
    # Monta o pedido
    pedido = Pedido(
        cliente_id=usuario.id,
        unidade_id=dados.unidade_id,
        canal_pedido=dados.canal_pedido,
        observacao=dados.observacao,
        status=StatusPedido.AGUARDANDO_PAGAMENTO,
        total=0.0,
    )
    db.add(pedido)
    db.flush()

    total = 0.0
    for item_dados in dados.itens:
        produto = db.query(Produto).filter(
            Produto.id == item_dados.produto_id,
            Produto.ativo == True,
        ).first()
        if not produto:
            raise HTTPException(
                status_code=404,
                detail={"error": "PRODUTO_NAO_ENCONTRADO", "produto_id": item_dados.produto_id},
            )

        # Verifica saldo em estoque
        saldo = _calcular_saldo(db, dados.unidade_id, produto.id)
        if saldo < item_dados.quantidade:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "ESTOQUE_INSUFICIENTE",
                    "produto": produto.nome,
                    "saldo": saldo,
                },
            )

        subtotal = produto.preco * item_dados.quantidade
        total += subtotal

        db.add(ItemPedido(
            pedido_id=pedido.id,
            produto_id=produto.id,
            quantidade=item_dados.quantidade,
            preco_unitario=produto.preco,
            subtotal=subtotal,
        ))

        # Baixa estoque automaticamente
        db.add(EstoqueMovimento(
            unidade_id=dados.unidade_id,
            produto_id=produto.id,
            tipo=TipoMovimentoEstoque.SAIDA,
            quantidade=item_dados.quantidade,
            motivo=f"Venda pedido #{pedido.id}",
        ))

    pedido.total = total

    # Auditoria: registra criação do pedido (rastreabilidade LGPD)
    registrar_log(
        db=db,
        acao="PEDIDO_CRIADO",
        usuario_id=usuario.id,
        entidade="Pedido",
        entidade_id=pedido.id,
        detalhe=f"Canal: {dados.canal_pedido.value} | Total: R$ {total:.2f} | Unidade: {dados.unidade_id}",
        request=request,
    )

    db.commit()
    db.refresh(pedido)
    return pedido


@router_pedidos.get(
    "",
    response_model=List[PedidoOut],
    summary="Listar pedidos",
    description=(
        "Lista pedidos com filtros opcionais. "
        "CLIENTEs só visualizam os próprios pedidos. "
        "Use `?canalPedido=TOTEM` para filtrar por canal de origem. "
        "Use `?status=EM_PREPARO` para filtrar por status."
    ),
)
def listar_pedidos(
    canal_pedido: Optional[str] = None,   # ex.: ?canalPedido=TOTEM
    status: Optional[str] = None,          # ex.: ?status=EM_PREPARO
    unidade_id: Optional[int] = None,      # ex.: ?unidade_id=1
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_atual),
):
    """
    Filtros disponíveis via query params:
    - canalPedido: APP | TOTEM | BALCAO | PICKUP | WEB
    - status: AGUARDANDO_PAGAMENTO | PAGAMENTO_CONFIRMADO | EM_PREPARO | PRONTO | ENTREGUE | CANCELADO
    - unidade_id: ID da unidade
    """
    from app.domain.models.models import CanalPedido

    q = db.query(Pedido)

    # CLIENTEs só veem os próprios pedidos
    if usuario.perfil == PerfilUsuario.CLIENTE:
        q = q.filter(Pedido.cliente_id == usuario.id)

    # Filtro por canal — exigido explicitamente pelo roteiro (multicanalidade)
    if canal_pedido:
        try:
            canal_enum = CanalPedido(canal_pedido.upper())
            q = q.filter(Pedido.canal_pedido == canal_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "CANAL_INVALIDO",
                    "message": f"Canal '{canal_pedido}' inválido. Use: APP, TOTEM, BALCAO, PICKUP, WEB.",
                },
            )

    # Filtro por status
    if status:
        try:
            status_enum = StatusPedido(status.upper())
            q = q.filter(Pedido.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "STATUS_INVALIDO",
                    "message": f"Status '{status}' inválido.",
                },
            )

    # Filtro por unidade
    if unidade_id:
        q = q.filter(Pedido.unidade_id == unidade_id)

    return q.order_by(Pedido.id.desc()).all()


@router_pedidos.get("/{pedido_id}", response_model=PedidoOut, summary="Detalhe de pedido")
def detalhe_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_atual),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail={"error": "PEDIDO_NAO_ENCONTRADO"})
    if usuario.perfil == PerfilUsuario.CLIENTE and pedido.cliente_id != usuario.id:
        raise HTTPException(status_code=403, detail={"error": "PERMISSAO_NEGADA"})
    return pedido


@router_pedidos.patch(
    "/{pedido_id}/status", response_model=PedidoOut,
    summary="Atualizar status do pedido (ATENDENTE/COZINHA/GERENTE/ADMIN)",
)
def atualizar_status(
    pedido_id: int,
    dados: PedidoStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(exigir_perfil(
        PerfilUsuario.ATENDENTE, PerfilUsuario.COZINHA,
        PerfilUsuario.GERENTE, PerfilUsuario.ADMIN,
    )),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail={"error": "PEDIDO_NAO_ENCONTRADO"})

    status_anterior = pedido.status
    pedido.status = dados.status

    # Auditoria: qualquer mudança de status é um evento sensível
    registrar_log(
        db=db,
        acao="PEDIDO_STATUS_ALTERADO",
        usuario_id=usuario.id,
        entidade="Pedido",
        entidade_id=pedido_id,
        detalhe=f"{status_anterior.value} → {dados.status.value}",
        request=request,
    )

    db.commit()
    db.refresh(pedido)
    return pedido


@router_pedidos.post(
    "/{pedido_id}/pagamento", response_model=PagamentoOut,
    summary="Processar pagamento mock",
)
def processar_pagamento(
    pedido_id: int,
    dados: PagamentoInput,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_atual),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail={"error": "PEDIDO_NAO_ENCONTRADO"})

    if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise HTTPException(
            status_code=400,
            detail={"error": "PAGAMENTO_JA_PROCESSADO", "status_atual": pedido.status},
        )

    if db.query(Pagamento).filter(Pagamento.pedido_id == pedido_id).first():
        raise HTTPException(status_code=400, detail={"error": "PAGAMENTO_JA_REGISTRADO"})

    # ---- MOCK: simula aprovação com 90% de chance ----
    aprovado = random.random() < 0.9
    status_pgto = StatusPagamento.APROVADO if aprovado else StatusPagamento.RECUSADO
    referencia = str(_uuid.uuid4())[:8].upper()
    mensagem = "Pagamento aprovado com sucesso." if aprovado else "Pagamento recusado pela operadora."

    pagamento = Pagamento(
        pedido_id=pedido_id,
        forma_pagamento=dados.forma_pagamento,
        status=status_pgto,
        gateway_referencia=referencia,
        gateway_mensagem=mensagem,
    )
    db.add(pagamento)

    # Atualiza status do pedido conforme resultado
    if aprovado:
        pedido.status = StatusPedido.PAGAMENTO_CONFIRMADO
        _conceder_pontos(db, usuario.id, pedido.total)
    else:
        pedido.status = StatusPedido.CANCELADO

    # Auditoria: pagamento é evento financeiro — obrigatório registrar
    registrar_log(
        db=db,
        acao="PAGAMENTO_PROCESSADO",
        usuario_id=usuario.id,
        entidade="Pagamento",
        entidade_id=pedido_id,
        detalhe=f"Forma: {dados.forma_pagamento} | Status: {status_pgto.value} | Ref: {referencia} | Total: R$ {pedido.total:.2f}",
        request=request,
    )

    db.commit()
    db.refresh(pagamento)
    return pagamento


def _conceder_pontos(db: Session, usuario_id: int, total: float):
    pontos = int(total)  # 1 ponto por real gasto
    saldo = db.query(PontosFidelidade).filter(PontosFidelidade.usuario_id == usuario_id).first()
    if saldo:
        saldo.saldo += pontos
        db.add(HistoricoFidelidade(
            usuario_id=usuario_id,
            tipo=TipoEventoFidelidade.GANHO,
            pontos=pontos,
            descricao=f"Pontos por compra (R$ {total:.2f})",
        ))


# ===========================================================================
# FIDELIDADE
# ===========================================================================

router_fidelidade = APIRouter()


@router_fidelidade.get(
    "/saldo", response_model=PontosSaldoOut,
    summary="Consultar saldo de pontos",
)
def saldo_pontos(db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    saldo = db.query(PontosFidelidade).filter(
        PontosFidelidade.usuario_id == usuario.id
    ).first()
    if not saldo:
        raise HTTPException(status_code=404, detail={"error": "SALDO_NAO_ENCONTRADO"})
    return saldo


@router_fidelidade.get(
    "/historico", response_model=List[HistoricoFidelidadeOut],
    summary="Histórico de pontos",
)
def historico_pontos(db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    return (
        db.query(HistoricoFidelidade)
        .filter(HistoricoFidelidade.usuario_id == usuario.id)
        .order_by(HistoricoFidelidade.id.desc())
        .all()
    )


@router_fidelidade.post(
    "/resgatar", response_model=PontosSaldoOut,
    summary="Resgatar pontos",
)
def resgatar_pontos(
    dados: ResgateInput,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_atual),
):
    saldo = db.query(PontosFidelidade).filter(
        PontosFidelidade.usuario_id == usuario.id
    ).first()
    if not saldo or saldo.saldo < dados.pontos:
        raise HTTPException(
            status_code=400,
            detail={"error": "SALDO_INSUFICIENTE", "saldo_atual": saldo.saldo if saldo else 0},
        )
    saldo.saldo -= dados.pontos
    db.add(HistoricoFidelidade(
        usuario_id=usuario.id,
        tipo=TipoEventoFidelidade.RESGATE,
        pontos=dados.pontos,
        descricao=f"Resgate de {dados.pontos} pontos",
    ))
    db.commit()
    db.refresh(saldo)
    return saldo
