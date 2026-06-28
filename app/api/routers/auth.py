"""
Router: /auth
POST /auth/login  — autentica e retorna JWT
Autor: Italo Ismailey G Durante | RU: 4471904 | UNINTER 2026

O login registra auditoria em dois casos:
  - LOGIN_SUCESSO: acesso bem-sucedido (rastreabilidade LGPD)
  - LOGIN_FALHA: tentativa com credenciais inválidas (segurança)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import registrar_log
from app.api.schemas.schemas import LoginInput, TokenOutput
from app.domain.models.models import Usuario
from app.infrastructure.database.session import get_db
from app.infrastructure.security import criar_access_token, verificar_senha

router = APIRouter()


@router.post("/login", response_model=TokenOutput, summary="Login — obtém token JWT")
def login(dados: LoginInput, request: Request, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(
        Usuario.email == dados.email,
        Usuario.ativo == True,
    ).first()

    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        # Registra tentativa de login inválida — importante para segurança
        registrar_log(
            db=db,
            acao="LOGIN_FALHA",
            detalhe=f"Tentativa com e-mail: {dados.email}",
            request=request,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "CREDENCIAIS_INVALIDAS", "message": "E-mail ou senha incorretos."},
        )

    token = criar_access_token({
        "sub": str(usuario.id),
        "perfil": usuario.perfil.value,
    })

    # Registra login bem-sucedido — exigido pela LGPD para rastreabilidade
    registrar_log(
        db=db,
        acao="LOGIN_SUCESSO",
        usuario_id=usuario.id,
        entidade="Usuario",
        entidade_id=usuario.id,
        detalhe=f"Login via perfil {usuario.perfil.value}",
        request=request,
    )
    db.commit()

    return TokenOutput(
        access_token=token,
        perfil=usuario.perfil.value,
        usuario_id=usuario.id,
        nome=usuario.nome,
    )
