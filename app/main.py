"""
Ponto de entrada principal da API Raízes do Nordeste.
Configuração do ciclo de vida da aplicação (startup), injeção de middlewares e barramento de rotas.
Autor: Italo Ismailey G Durante | RU: 4471904 | UNINTER 2026
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Inicialização do core com metadados do config.py
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    contact={
        "name": "Italo Ismailey G Durante",
        "email": "italoismailey@gmail.com",
    }
)

# Configuração de política de CORS voltada para o ambiente de desenvolvimento local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estratégia de Import Tardio (Lazy Import) para quebrar o acoplamento cíclico de dependências
# entre os módulos de rotas, esquemas do Pydantic e sessões de banco de dados.
from app.api.routers import (
    auth,
    usuarios,
    unidades,
    produtos,
    pedidos,
    estoque,
    fidelidade,
)

# Acoplamento dos roteadores do ecossistema da aplicação
app.include_router(auth.router,       prefix="/auth",       tags=["Auth"])
app.include_router(usuarios.router,   prefix="/usuarios",   tags=["Usuários"])
app.include_router(unidades.router,   prefix="/unidades",   tags=["Unidades"])
app.include_router(produtos.router,   prefix="/produtos",   tags=["Produtos"])
app.include_router(pedidos.router,    prefix="/pedidos",    tags=["Pedidos"])
app.include_router(estoque.router,    prefix="/estoque",    tags=["Estoque"])
app.include_router(fidelidade.router, prefix="/fidelidade", tags=["Fidelidade"])


@app.on_event("startup")
async def startup_event():
    """
    Rotina de inicialização automática. Dispara o mapeamento ORM do SQLAlchemy
    garantindo que o schema do SQLite local reflita o estado atual dos modelos.
    """
    try:
        from app.domain.models import models  # noqa: F401
        from app.infrastructure.database.session import Base, engine

        # Gera o mapeamento DDL físico no arquivo do banco
        Base.metadata.create_all(bind=engine)
        print("Tabelas criadas/verificadas com sucesso!")
    except Exception as e:
        print(f"Erro na verificação de tabelas físicas no startup: {e}")


@app.get("/", tags=["Status"], summary="Status da API")
def root():
    """Endpoint básico para monitoramento de integridade e checagem de estado da API."""
    return {
        "api": settings.APP_NAME,
        "versao": settings.APP_VERSION,
        "status": "online",
        "endpoints_docs": ["/docs", "/redoc"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
