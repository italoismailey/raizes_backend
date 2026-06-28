"""
Testes automatizados — Raízes do Nordeste API
A gente cria e popula o banco temporário do SQLite antes de rodar os testes
para validar os fluxos de auth, usuários, pedidos, estoque e fidelidade.
Autor: Italo Ismailey G Durante | RU: 4471904 | UNINTER 2026
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.infrastructure.database.session import Base, get_db
from app.domain.models.models import PontosFidelidade, PerfilUsuario, Usuario
from app.infrastructure.security import hash_senha

# --- BANCO DE TESTES ---
TEST_DB_URL = "sqlite:///./test_raizes.db"
engine_test = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def prepara_banco():
    """Garante banco limpo e populado antes de cada teste."""
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    _popula_dados_basicos()
    yield
    Base.metadata.drop_all(bind=engine_test)

def _popula_dados_basicos():
    """Massa de dados padrão para rodar as validações."""
    from app.domain.models.models import Unidade, Produto, CardapioItem, EstoqueMovimento, TipoMovimentoEstoque

    db = TestingSessionLocal()
    try:
        # Usuários base
        admin = Usuario(nome="Admin Teste", email="admin@raizes.com", senha_hash=hash_senha("Admin@123"), perfil=PerfilUsuario.ADMIN)
        cliente = Usuario(nome="Cliente Teste", email="cliente@teste.com", senha_hash=hash_senha("Cliente@123"), perfil=PerfilUsuario.CLIENTE, consentimento_fidelidade=True)
        atendente = Usuario(nome="Atendente Teste", email="atendente@teste.com", senha_hash=hash_senha("Atend@123"), perfil=PerfilUsuario.ATENDENTE)
        db.add_all([admin, cliente, atendente])
        db.flush()

        # Estrutura operacional
        uni = Unidade(nome="Unidade Teste", cidade="Recife", estado="PE", endereco="Rua Teste, 1", ativa=True)
        db.add(uni)
        db.flush()

        # Itens do cardápio
        tapioca = Produto(nome="Tapioca", preco=8.50, categoria="Tapioca", ativo=True)
        suco = Produto(nome="Suco de Cajá", preco=9.00, categoria="Suco", ativo=True)
        db.add_all([tapioca, suco])
        db.flush()

        db.add(CardapioItem(unidade_id=uni.id, produto_id=tapioca.id, disponivel=True))
        db.add(CardapioItem(unidade_id=uni.id, produto_id=suco.id, disponivel=True))

        # Carga de estoque e fidelidade ativa
        db.add(EstoqueMovimento(unidade_id=uni.id, produto_id=tapioca.id, tipo=TipoMovimentoEstoque.ENTRADA, quantidade=50, motivo="Inicial"))
        db.add(EstoqueMovimento(unidade_id=uni.id, produto_id=suco.id, tipo=TipoMovimentoEstoque.ENTRADA, quantidade=50, motivo="Inicial"))
        db.add(PontosFidelidade(usuario_id=cliente.id, saldo=100))
        db.commit()
    finally:
        db.close()


# --- HELPERS (Utilitários que limpam o código dos testes) ---
client = TestClient(app)

def get_auth_headers(perfil="admin"):
    """Gera o cabeçalho Bearer Token de forma dinâmica e limpa."""
    credenciais = {
        "admin": ("admin@raizes.com", "Admin@123"),
        "cliente": ("cliente@teste.com", "Cliente@123"),
        "atendente": ("atendente@teste.com", "Atend@123")
    }
    email, senha = credenciais.get(perfil, credenciais["admin"])
    r = client.post("/auth/login", json={"email": email, "senha": senha})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def cria_um_pedido(headers=None):
    """Retorna um pedido pronto para testes de fluxo."""
    if headers is None:
        headers = get_auth_headers("cliente")
    r = client.post("/pedidos", json={
        "unidade_id": 1,
        "canal_pedido": "APP",
        "itens": [{"produto_id": 1, "quantidade": 1}]
    }, headers=headers)
    return r.json()


# ====================== SESSÃO DE TESTES ======================

def test_login_com_sucesso():
    r = client.post("/auth/login", json={"email": "admin@raizes.com", "senha": "Admin@123"})
    assert r.status_code == 200
    assert "access_token" in r.json()

def test_login_senha_errada():
    r = client.post("/auth/login", json={"email": "admin@raizes.com", "senha": "senhaerrada123"})
    assert r.status_code == 401

def test_acesso_sem_estar_logado():
    r = client.get("/usuarios/me")
    assert r.status_code in (401, 403)

def test_cadastrar_novo_cliente():
    r = client.post("/usuarios", json={
        "nome": "Maria Silva", "email": "maria@teste.com",
        "senha": "Maria123", "perfil": "CLIENTE", "consentimento_fidelidade": True
    })
    assert r.status_code == 201
    assert r.json()["email"] == "maria@teste.com"

def test_nao_cadastrar_email_duplicado():
    r = client.post("/usuarios", json={
        "nome": "Admin Duplicado", "email": "admin@raizes.com",
        "senha": "123456", "perfil": "CLIENTE"
    })
    assert r.status_code == 409

def test_listar_unidades_logado():
    r = client.get("/unidades", headers=get_auth_headers("cliente"))
    assert r.status_code == 200
    assert len(r.json()) >= 1

def test_ver_cardapio_da_unidade():
    r = client.get("/unidades/1/cardapio", headers=get_auth_headers("cliente"))
    assert r.status_code == 200
    assert len(r.json()) >= 2

def test_criar_pedido_normal():
    r = client.post("/pedidos", json={
        "unidade_id": 1, "canal_pedido": "APP",
        "itens": [{"produto_id": 1, "quantidade": 2}, {"produto_id": 2, "quantidade": 1}]
    }, headers=get_auth_headers("cliente"))
    assert r.status_code == 201
    assert r.json()["status"] == "AGUARDANDO_PAGAMENTO"

def test_pedido_com_produto_que_nao_existe():
    r = client.post("/pedidos", json={
        "unidade_id": 1, "canal_pedido": "APP", "itens": [{"produto_id": 9999, "quantidade": 1}]
    }, headers=get_auth_headers("cliente"))
    assert r.status_code == 404

def test_realizar_pagamento():
    pedido_id = cria_um_pedido()["id"]
    r = client.post(f"/pedidos/{pedido_id}/pagamento", json={
        "pedido_id": pedido_id, "forma_pagamento": "PIX"
    }, headers=get_auth_headers("cliente"))
    assert r.status_code == 200
    assert r.json()["status"] in ("APROVADO", "RECUSADO")

def test_nao_pagar_pedido_duas_vezes():
    pedido_id = cria_um_pedido()["id"]
    headers = get_auth_headers("cliente")
    payload = {"pedido_id": pedido_id, "forma_pagamento": "PIX"}
    client.post(f"/pedidos/{pedido_id}/pagamento", json=payload, headers=headers)
    r2 = client.post(f"/pedidos/{pedido_id}/pagamento", json=payload, headers=headers)
    assert r2.status_code == 400

def test_atendente_altera_status():
    pedido_id = cria_um_pedido()["id"]
    client.post(f"/pedidos/{pedido_id}/pagamento", json={"pedido_id": pedido_id, "forma_pagamento": "PIX"}, headers=get_auth_headers("cliente"))
    r = client.patch(f"/pedidos/{pedido_id}/status", json={"status": "EM_PREPARO"}, headers=get_auth_headers("atendente"))
    assert r.status_code == 200
    assert r.json()["status"] == "EM_PREPARO"

def test_cliente_nao_pode_mudar_status():
    pedido_id = cria_um_pedido()["id"]
    r = client.patch(f"/pedidos/{pedido_id}/status", json={"status": "EM_PREPARO"}, headers=get_auth_headers("cliente"))
    assert r.status_code == 403

def test_estoque_e_baixado_ao_fazer_pedido():
    headers_admin = get_auth_headers("admin")
    r_antes = client.get("/estoque/saldo/1", headers=headers_admin)
    saldo_antes = next(p["saldo"] for p in r_antes.json() if p["produto_id"] == 1)
    client.post("/pedidos", json={"unidade_id": 1, "canal_pedido": "TOTEM", "itens": [{"produto_id": 1, "quantidade": 4}]}, headers=get_auth_headers("cliente"))
    r_depois = client.get("/estoque/saldo/1", headers=headers_admin)
    saldo_depois = next(p["saldo"] for p in r_depois.json() if p["produto_id"] == 1)
    assert saldo_depois == saldo_antes - 4

def test_pontos_fidelidade_sao_concedidos():
    headers = get_auth_headers("cliente")
    saldo_inicial = client.get("/fidelidade/saldo", headers=headers).json()["saldo"]
    for _ in range(8):
        pedido_id = cria_um_pedido(headers)["id"]
        r = client.post(f"/pedidos/{pedido_id}/pagamento", json={"pedido_id": pedido_id, "forma_pagamento": "PIX"}, headers=headers)
        if r.json().get("status") == "APROVADO":
            saldo_final = client.get("/fidelidade/saldo", headers=headers).json()["saldo"]
            assert saldo_final > saldo_inicial
            break

def test_resgatar_pontos():
    headers = get_auth_headers("cliente")
    saldo_antes = client.get("/fidelidade/saldo", headers=headers).json()["saldo"]
    r = client.post("/fidelidade/resgatar", json={"pontos": 40}, headers=headers)
    assert r.status_code == 200
    assert r.json()["saldo"] == saldo_antes - 40

def test_resgatar_com_saldo_insuficiente():
    r = client.post("/fidelidade/resgatar", json={"pontos": 9999}, headers=get_auth_headers("cliente"))
    assert r.status_code == 400

def test_pedido_com_estoque_insuficiente():
    r = client.post("/pedidos", json={"unidade_id": 1, "canal_pedido": "APP", "itens": [{"produto_id": 1, "quantidade": 999}]}, headers=get_auth_headers("cliente"))
    assert r.status_code == 400

def test_cliente_nao_consegue_listar_usuarios():
    r = client.get("/usuarios", headers=get_auth_headers("cliente"))
    assert r.status_code == 403

def test_pedido_pelo_totem():
    r = client.post("/pedidos", json={"unidade_id": 1, "canal_pedido": "TOTEM", "itens": [{"produto_id": 2, "quantidade": 1}]}, headers=get_auth_headers("cliente"))
    assert r.status_code == 201
    assert r.json()["canal_pedido"] == "TOTEM"

def test_filtrar_pedidos_por_canal():
    headers = get_auth_headers("cliente")
    client.post("/pedidos", json={"unidade_id": 1, "canal_pedido": "APP", "itens": [{"produto_id": 1, "quantidade": 1}]}, headers=headers)
    client.post("/pedidos", json={"unidade_id": 1, "canal_pedido": "TOTEM", "itens": [{"produto_id": 2, "quantidade": 1}]}, headers=headers)
    r = client.get("/pedidos?canal_pedido=TOTEM", headers=headers)
    assert r.status_code == 200
    assert all(p["canal_pedido"] == "TOTEM" for p in r.json())

def test_filtro_com_canal_invalido():
    r = client.get("/pedidos?canal_pedido=INVALIDO", headers=get_auth_headers("cliente"))
    assert r.status_code == 400
