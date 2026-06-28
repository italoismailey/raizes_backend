"""
Módulo de Gerenciamento de Configurações e Variáveis de Ambiente.
Centraliza as propriedades de runtime da API Raízes do Nordeste utilizando o padrão de Singleton.
Autor: Italo Ismailey G Durante | RU: 4471904 | UNINTER 2026
"""
import os
from pathlib import Path

# Mecanismo nativo de parseamento do arquivo de configuração de ambiente (.env).
# Desenvolvido para eliminar o acoplamento com gerenciadores de terceiros (ex: python-dotenv),
# garantindo a portabilidade e a otimização da árvore de dependências do projeto.
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


class Settings:
    # String de conexão do mecanismo de persistência. A escolha do SQLite local visa
    # mitigar a complexidade de infraestrutura em ambiente de desenvolvimento e testes homolados.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./raizes.db")

    # Parâmetros de segurança do subsistema de autenticação baseada em JWT (Json Web Tokens).
    # O algoritmo simétrico HS256 foi adotado visando o equilíbrio entre performance e criptografia robusta.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "chave-super-secreta-para-dev")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    ENV: str = os.getenv("ENV", "development")

    # Metadados de identificação integrados ao barramento OpenAPI (Swagger UI)
    APP_NAME: str = "Raízes do Nordeste — API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = """
API back-end para a rede de lanchonetes Raízes do Nordeste.<br>
Gerencia pedidos, cardápio, estoque, fidelização e pagamentos.<br>
**Desenvolvido por Italo Ismailey G Durante (RU 4471904) — UNINTER 2026.**
"""


# Instanciação do Singleton para consumo unificado entre as camadas do sistema
settings = Settings()
