"""
Raízes do Nordeste - API Back-end
Versão final - UNINTER 2026

Desenvolvido por Italo Ismailey G Durante (RU 4471904)

"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="Raízes do Nordeste — API",
    version="1.0.0",
    description="""API Back-end da rede de lanchonetes Raízes do Nordeste.

Gerencia pedidos multicanal (App, Totem, Balcão, Pickup), controle de estoque por unidade, 
programa de fidelidade e integração simulada com gateway de pagamento.

Desenvolvido como parte da Atividade Prática da Trilha Back-End. """,
    contact={
        "name": "Italo Ismailey",
        "email": "italoismailey@gmail.com",
        "url": "https://github.com/italoismailey/raizes_backend"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {"name": "Auth", "description": "Autenticação e gestão de tokens JWT"},
        {"name": "Usuários", "description": "Cadastro, perfil e gestão de usuários"},
        {"name": "Unidades", "description": "Unidades da rede e cardápio por localização"},
        {"name": "Pedidos", "description": "Fluxo completo de pedidos (principal)"},
        {"name": "Estoque", "description": "Movimentação e consulta de estoque por unidade"},
        {"name": "Fidelidade", "description": "Programa de pontos e resgate"},
    ],
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "defaultModelsExpandDepth": -1,   # expande todos os schemas
        "docExpansion": "list",
        "filter": True,
    }
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers (depois do app)
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
    """Cria tabelas automaticamente no startup (útil para dev)."""
    try:
        from app.domain.models.models import Base
        from app.infrastructure.database.session import engine
        Base.metadata.create_all(bind=engine)
        print("Banco de dados verificado e tabelas criadas.")
    except Exception as e:
        print(f" Aviso ao criar tabelas: {e}")


@app.get("/", tags=["Status"], summary="Health Check da API")
def root():
    return {
        "api": "Raízes do Nordeste",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "mensagem": "Bem-vindo! A API está funcionando."
    }
