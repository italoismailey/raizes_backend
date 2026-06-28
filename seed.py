"""
Script de carga inicial e população física do banco de dados (Seed).
Gera o schema do SQLAlchemy e injeta a massa de dados padrão para testes operacionais.
Autor: Italo Ismailey G Durante | RU: 4471904 | UNINTER 2026
"""

from app.infrastructure.database.session import Base, engine, SessionLocal
from app.domain.models.models import (
    Usuario, Unidade, Produto, CardapioItem,
    EstoqueMovimento, PontosFidelidade,
    PerfilUsuario, TipoMovimentoEstoque,
)
from passlib.context import CryptContext

# Instanciação do contexto de criptografia para mascaramento das senhas no banco
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def criar_tabelas():
    """Gera o mapeamento DDL físico no arquivo do SQLite."""
    print("Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("  Tabelas criadas com sucesso.")


def seed(db):
    """Massa de testes mapeando os atores e regras de negócio do roteiro."""

    # --- MATRIZ DE USUÁRIOS E PERFIS DE ACESSO (ACL) ---
    print("Inserindo usuários...")
    usuarios = [
        Usuario(
            nome="Admin Raízes",
            email="admin@raizes.com",
            senha_hash=pwd_context.hash("Admin@123"),
            perfil=PerfilUsuario.ADMIN,
            consentimento_fidelidade=False,
            consentimento_marketing=False,
        ),
        Usuario(
            nome="Gerente Recife",
            email="gerente.recife@raizes.com",
            senha_hash=pwd_context.hash("Gerente@123"),
            perfil=PerfilUsuario.GERENTE,
            consentimento_fidelidade=False,
            consentimento_marketing=False,
        ),
        Usuario(
            nome="Maria da Silva",
            email="maria@cliente.com",
            senha_hash=pwd_context.hash("Cliente@123"),
            perfil=PerfilUsuario.CLIENTE,
            consentimento_fidelidade=True,
            consentimento_marketing=True,
        ),
        Usuario(
            nome="João Atendente",
            email="joao.atendente@raizes.com",
            senha_hash=pwd_context.hash("Atendente@123"),
            perfil=PerfilUsuario.ATENDENTE,
            consentimento_fidelidade=False,
            consentimento_marketing=False,
        ),
        Usuario(
            nome="Cozinha Central",
            email="cozinha@raizes.com",
            senha_hash=pwd_context.hash("Cozinha@123"),
            perfil=PerfilUsuario.COZINHA,
            consentimento_fidelidade=False,
            consentimento_marketing=False,
        ),
    ]
    db.add_all(usuarios)
    db.flush()  # Isolando os IDs gerados para herança nas tabelas filhas

    # --- FILIAIS OPERACIONAIS ---
    print("Inserindo unidades...")
    unidades = [
        Unidade(nome="Raízes do Nordeste — Recife Centro",      cidade="Recife",    estado="PE", endereco="Rua do Bom Jesus, 100"),
        Unidade(nome="Raízes do Nordeste — Fortaleza Meireles", cidade="Fortaleza", estado="CE", endereco="Av. Beira Mar, 500"),
        Unidade(nome="Raízes do Nordeste — Salvador Pelourinho",cidade="Salvador",  estado="BA", endereco="Largo do Pelourinho, 20"),
    ]
    db.add_all(unidades)
    db.flush()

    # --- CATÁLOGO DE PRODUTOS ---
    print("Inserindo produtos...")
    produtos = [
        Produto(nome="Tapioca Simples",           preco=8.50,  categoria="Tapioca"),
        Produto(nome="Tapioca Frango com Queijo",  preco=14.90, categoria="Tapioca"),
        Produto(nome="Cuscuz Nordestino",          preco=10.00, categoria="Cuscuz"),
        Produto(nome="Bolo de Macaxeira",          preco=7.00,  categoria="Bolo"),
        Produto(nome="Suco de Cajá",               preco=9.00,  categoria="Suco"),
        Produto(nome="Café Passado",               preco=5.00,  categoria="Bebida"),
        Produto(nome="Manteiga de Garrafa",        preco=3.00,  categoria="Acompanhamento"),
        Produto(nome="Canjica (junino)",           preco=6.00,  categoria="Especial"),
    ]
    db.add_all(produtos)
    db.flush()

    # --- REGRA DE NEGÓCIO: DISPONIBILIDADE DE CARDÁPIO POR PRAÇA ---
    print("Inserindo cardápio por unidade...")
    cardapio = []
    for unidade in unidades:
        for produto in produtos:  # corrigido: era 'products' (bug de digitação)
            disponivel = True
            # Restrição geográfica do roteiro: Sazonal junino travado fora de Recife
            if produto.categoria == "Especial" and unidade.cidade != "Recife":
                disponivel = False
            cardapio.append(CardapioItem(
                unidade_id=unidade.id,
                produto_id=produto.id,
                disponivel=disponivel,
            ))
    db.add_all(cardapio)
    db.flush()

    # --- INPUT DE INVENTÁRIO (VOLUMETRIA INICIAL DE ESTOQUE) ---
    print("Inserindo estoque inicial...")
    movimentos = []
    for unidade in unidades:
        for produto in produtos:
            movimentos.append(EstoqueMovimento(
                unidade_id=unidade.id,
                produto_id=produto.id,
                tipo=TipoMovimentoEstoque.ENTRADA,
                quantidade=50,
                motivo="Estoque inicial (seed)",
            ))
    db.add_all(movimentos)
    db.flush()

    # --- INICIALIZAÇÃO DA CARTEIRA DE PONTOS (FIDELIDADE) ---
    print("Inserindo pontos de fidelidade...")
    cliente = next(u for u in usuarios if u.perfil == PerfilUsuario.CLIENTE)
    db.add(PontosFidelidade(usuario_id=cliente.id, saldo=0))

    db.commit()
    print("\n✅ Seed concluído com sucesso!")
    print("\nUsuários criados:")
    print("  admin@raizes.com          → senha: Admin@123      (ADMIN)")
    print("  gerente.recife@raizes.com → senha: Gerente@123    (GERENTE)")
    print("  maria@cliente.com         → senha: Cliente@123    (CLIENTE)")
    print("  joao.atendente@raizes.com → senha: Atendente@123  (ATENDENTE)")
    print("  cozinha@raizes.com        → senha: Cozinha@123    (COZINHA)")


if __name__ == "__main__":
    criar_tabelas()
    db = SessionLocal()
    try:
        seed(db)
    except Exception as e:
        db.rollback()  # Aborta a transação em bloco caso ocorra alguma violação de FK
        print(f"\n❌ Erro no seed: {e}")
        raise
    finally:
        db.close()
