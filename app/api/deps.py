"""
deps.py — Dependências de autenticação e autorização
Raízes do Nordeste — Projeto Back-End
Autor: Italo Ismailey G Durante | RU: 4471904 | UNINTER 2026

Aqui centralizo toda a lógica de "quem pode fazer o quê".
Usei o padrão de injeção de dependências do FastAPI (Depends),
que permite proteger qualquer rota com uma única linha de código.

Exemplo de uso nas rotas:
    # Exige apenas autenticação
    usuario = Depends(get_usuario_atual)

    # Exige perfil específico
    _ = Depends(exigir_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE))
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.domain.models.models import PerfilUsuario, Usuario
from app.infrastructure.database.session import get_db
from app.infrastructure.security import decodificar_token

bearer_scheme = HTTPBearer()


def get_usuario_atual(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Extrai o JWT do header Authorization: Bearer <token>.
    Valida a assinatura e a expiração, e retorna o usuário autenticado.
    Retorna 401 se o token for inválido ou o usuário estiver inativo.
    """
    token = credentials.credentials
    try:
        payload = decodificar_token(token)
        usuario_id: str = payload.get("sub")
        if usuario_id is None:
            raise JWTError("sub ausente no payload")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "TOKEN_INVALIDO", "message": "Token inválido ou expirado."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario = db.query(Usuario).filter(
        Usuario.id == int(usuario_id),
        Usuario.ativo == True,
    ).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "USUARIO_INATIVO", "message": "Usuário não encontrado ou inativo."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario


def exigir_perfil(*perfis_permitidos: PerfilUsuario):
    """
    Factory de dependências: retorna uma função que bloqueia a rota
    caso o usuário logado não tenha um dos perfis informados.
    Retorna 403 PERMISSAO_NEGADA se o perfil não for suficiente.
    """
    def _dependencia(usuario: Usuario = Depends(get_usuario_atual)) -> Usuario:
        if usuario.perfil not in perfis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "PERMISSAO_NEGADA",
                    "message": f"Perfil '{usuario.perfil}' não tem permissão para este recurso.",
                },
            )
        return usuario
    return _dependencia


def registrar_log(
    db: Session,
    acao: str,
    usuario_id: int | None = None,
    entidade: str | None = None,
    entidade_id: int | None = None,
    detalhe: str | None = None,
    request: Request | None = None,
):
    """
    Registra ações sensíveis na tabela logs_auditoria.
    Incluí esse mecanismo para atender ao requisito de LGPD do roteiro:
    toda ação relevante sobre dados pessoais deve ser rastreável.
    """
    from app.domain.models.models import LogAuditoria

    ip = None
    if request:
        ip = request.client.host if request.client else None

    log = LogAuditoria(
        usuario_id=usuario_id,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhe=detalhe,
        ip=ip,
    )
    db.add(log)
