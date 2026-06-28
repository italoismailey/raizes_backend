"""
Router: /usuarios
GET    /usuarios/me          — perfil do usuário logado
GET    /usuarios             — lista todos (ADMIN/GERENTE)
POST   /usuarios             — cadastro (público para CLIENTE, restrito para outros perfis)
GET    /usuarios/{id}        — detalhe (ADMIN/GERENTE ou próprio usuário)
PUT    /usuarios/{id}        — atualizar (ADMIN ou próprio usuário)
DELETE /usuarios/{id}        — desativar (ADMIN)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import exigir_perfil, get_usuario_atual
from app.api.schemas.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.domain.models.models import PerfilUsuario, PontosFidelidade, Usuario
from app.infrastructure.database.session import get_db
from app.infrastructure.security import hash_senha

router = APIRouter()


@router.get("/me", response_model=UsuarioOut, summary="Meu perfil")
def meu_perfil(usuario=Depends(get_usuario_atual)):
    return usuario


@router.get(
    "",
    response_model=List[UsuarioOut],
    summary="Listar usuários (ADMIN/GERENTE)",
)
def listar_usuarios(
    db: Session = Depends(get_db),
    _=Depends(exigir_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE)),
):
    return db.query(Usuario).order_by(Usuario.id).all()


@router.post("", response_model=UsuarioOut, status_code=201, summary="Cadastrar usuário")
def criar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "EMAIL_DUPLICADO", "message": "Este e-mail já está cadastrado."},
        )

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        perfil=dados.perfil,
        consentimento_fidelidade=dados.consentimento_fidelidade,
        consentimento_marketing=dados.consentimento_marketing,
    )
    db.add(usuario)
    db.flush()

    # Cria saldo de fidelidade automaticamente para CLIENTEs
    if dados.perfil == PerfilUsuario.CLIENTE:
        db.add(PontosFidelidade(usuario_id=usuario.id, saldo=0))

    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("/{usuario_id}", response_model=UsuarioOut, summary="Detalhe de usuário")
def detalhe_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    atual=Depends(get_usuario_atual),
):
    # Permite ao próprio usuário ver seu perfil; admins/gerentes veem qualquer um
    if atual.id != usuario_id and atual.perfil not in (PerfilUsuario.ADMIN, PerfilUsuario.GERENTE):
        raise HTTPException(status_code=403, detail={"error": "PERMISSAO_NEGADA"})

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail={"error": "USUARIO_NAO_ENCONTRADO"})
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioOut, summary="Atualizar usuário")
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioUpdate,
    db: Session = Depends(get_db),
    atual=Depends(get_usuario_atual),
):
    if atual.id != usuario_id and atual.perfil != PerfilUsuario.ADMIN:
        raise HTTPException(status_code=403, detail={"error": "PERMISSAO_NEGADA"})

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail={"error": "USUARIO_NAO_ENCONTRADO"})

    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=204, summary="Desativar usuário (ADMIN)")
def desativar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _=Depends(exigir_perfil(PerfilUsuario.ADMIN)),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail={"error": "USUARIO_NAO_ENCONTRADO"})
    usuario.ativo = False
    db.commit()
