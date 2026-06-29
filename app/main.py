"""
Raízes do Nordeste - API Back-end
Versão final para entrega

Feito com bastante café :) 
RU 4471904 - Italo Ismailey - UNINTER 2026
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="Raízes do Nordeste — API",
    version="1.0.0",
    description="""API do back-end da rede Raízes do Nordeste.

Gerencia pedidos vindos do App, Totem, Balcão e Pickup, controle de estoque por loja, 
fidelidade e pagamento simulado.

Trabalho final da Trilha Back-End - Projeto Multidisciplinar.""",
    contact={
        "name": "Italo Ismailey Gonçalves Durante",
        "email": "italoismailey@gmail.com",
        "url": "https://github.com/italoismailey/raizes_backend"
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.api.routers import auth, usuarios, unidades, produtos, pedidos, estoque, fidelidade

app.include_router(auth.router,        prefix="/auth",       tags=["Auth"])
app.include_router(usuarios.router,    prefix="/usuarios",   tags=["Usuários"])
app.include_router(unidades.router,    prefix="/unidades",   tags=["Unidades"])
app.include_router(produtos.router,    prefix="/produtos",   tags=["Produtos"])
app.include_router(pedidos.router,     prefix="/pedidos",    tags=["Pedidos"])
app.include_router(estoque.router,     prefix="/estoque",    tags=["Estoque"])
app.include_router(fidelidade.router,  prefix="/fidelidade", tags=["Fidelidade"])


@app.on_event("startup")
def startup_event():
    """Inicializa o banco de dados."""
    try:
        from app.domain.models.models import Base
        from app.infrastructure.database.session import engine
        Base.metadata.create_all(bind=engine)
        print(" Banco pronto!")
    except Exception as e:
        print(f" Algo deu errado ao iniciar o banco: {e}")


@app.get("/", tags=["Status"])
def root():
    """Rota para checar se a API está rodando."""
    return {
        "api": "Raízes do Nordeste",
        "status": "online",
        "versao": "1.0.0",
        "mensagem": "Bem-vindo! Pode testar no /docs "
    }