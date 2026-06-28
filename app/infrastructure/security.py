"""
security.py — Hash de senha e geração/validação de JWT
Raízes do Nordeste — Projeto Back-End
Autor: Italo Ismailey G Durante | RU: 4471904 | UNINTER 2026

Decisão técnica: escolhi bcrypt para hash de senhas por ser o algoritmo
mais recomendado para esse fim — ele é lento por design, o que dificulta
ataques de força bruta. Para os tokens JWT, optei por HS256 (simétrico)
por ser suficiente para um sistema interno onde o próprio servidor
assina e valida os tokens.
"""

from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    """Gera hash bcrypt — nunca armazenamos senhas em texto puro."""
    return pwd_context.hash(senha)


def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    """Compara a senha informada com o hash armazenado no banco."""
    return pwd_context.verify(senha_pura, senha_hash)


def criar_access_token(data: dict) -> str:
    """
    Gera JWT assinado com a SECRET_KEY.
    O payload deve conter ao menos {'sub': str(usuario_id)}.
    A expiração é controlada pela variável ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    payload = data.copy()
    expiracao = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload.update({"exp": expiracao})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> dict:
    """
    Decodifica e valida o JWT.
    Lança JWTError se o token for inválido ou estiver expirado.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
