# 🍽️ Raízes do Nordeste — API Back-End

> Projeto Multidisciplinar — Atividade Prática Back-End  
> **Autor:** Italo Ismailey G Durante | **RU:** 4471904  
> **Instituição:** UNINTER — 2026  

---

## 📋 Sobre o Projeto

Este projeto é a implementação do back-end para a rede de lanchonetes **Raízes do Nordeste**, desenvolvido como parte da Atividade Prática da disciplina de Projeto Back-End da UNINTER.

A solução é uma **API REST** que gerencia pedidos, cardápio, estoque, programa de fidelidade e pagamentos (mock), suportando múltiplos canais de atendimento: App, Totem, Balcão, Pickup e Web.

---

## 🧠 Decisões Técnicas

Durante o desenvolvimento precisei tomar algumas decisões de tecnologia e arquitetura que julguei importantes registrar:

**Por que Python?**  
Já tenho familiaridade com a linguagem, o que me permitiu focar na lógica de negócio em vez de lutar com a sintaxe.

**Por que FastAPI?**  
Gera documentação Swagger/OpenAPI automaticamente — o que o roteiro exige como evidência técnica. Além disso, tem validação de dados nativa via Pydantic.

**Por que SQLite?**  
Para simplificar o ambiente de desenvolvimento local. Não é necessário instalar nenhum servidor de banco de dados. Em produção, bastaria trocar a `DATABASE_URL` no `.env` para PostgreSQL — o código não mudaria nada.

**Por que arquitetura em camadas?**  
Separei o projeto em `domain`, `application`, `infrastructure` e `api` para manter cada responsabilidade no seu lugar. Isso facilita manutenção e testes isolados.

**Por que um mock de pagamento?**  
O roteiro não exige integração real com gateway. O mock simula aprovação (90%) e recusa (10%), o suficiente para validar o fluxo completo do pedido.

---

## 🗂️ Estrutura do Projeto

```
raizes_backend/
├── .env.example              # Modelo de variáveis de ambiente
├── requirements.txt          # Dependências do projeto
├── seed.py                   # Cria banco e insere dados iniciais
└── app/
    ├── config.py             # Leitura das variáveis de ambiente
    ├── main.py               # Ponto de entrada da aplicação
    ├── domain/
    │   └── models/
    │       └── models.py     # Entidades do banco (SQLAlchemy ORM)
    ├── infrastructure/
    │   ├── database/
    │   │   └── session.py    # Conexão com SQLite
    │   └── security.py       # bcrypt + JWT
    ├── application/
    │   └── services/         # (reservado para serviços de domínio)
    └── api/
        ├── deps.py           # Autenticação e controle de perfis
        ├── routers/          # Endpoints organizados por módulo
        │   ├── auth.py
        │   ├── usuarios.py
        │   ├── unidades.py
        │   ├── produtos.py
        │   ├── pedidos.py
        │   ├── estoque.py
        │   └── fidelidade.py
        └── schemas/
            └── schemas.py    # Contratos de entrada e saída (Pydantic)
```

---

## ⚙️ Como Rodar Localmente

### Pré-requisitos
- Python 3.11+
- Anaconda (recomendado) ou pip

### 1. Criar e ativar ambiente virtual

```bash
conda create -n raizesvs1 python=3.11 -y
conda activate raizesvs1
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
# O .env já vem com valores padrão para desenvolvimento local
```

### 4. Criar banco e popular com dados iniciais

```bash
python seed.py
```

Usuários criados pelo seed:

| E-mail | Senha | Perfil |
|--------|-------|--------|
| admin@raizes.com | Admin@123 | ADMIN |
| gerente.recife@raizes.com | Gerente@123 | GERENTE |
| maria@cliente.com | Cliente@123 | CLIENTE |
| joao.atendente@raizes.com | Atendente@123 | ATENDENTE |
| cozinha@raizes.com | Cozinha@123 | COZINHA |

### 5. Iniciar a API

```bash
uvicorn app.main:app --reload
```

Acesse a documentação interativa: **http://localhost:8000/docs**

---

## 🔗 Endpoints Disponíveis

### Auth
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/login` | Login — retorna token JWT |

### Usuários
| Método | Rota | Perfil exigido |
|--------|------|----------------|
| GET | `/usuarios/me` | Autenticado |
| GET | `/usuarios` | ADMIN, GERENTE |
| POST | `/usuarios` | Público |
| GET | `/usuarios/{id}` | Próprio ou ADMIN/GERENTE |
| PUT | `/usuarios/{id}` | Próprio ou ADMIN |
| DELETE | `/usuarios/{id}` | ADMIN |

### Unidades e Cardápio
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/unidades` | Lista unidades ativas |
| GET | `/unidades/{id}` | Detalhe da unidade |
| GET | `/unidades/{id}/cardapio` | Cardápio da unidade |

### Produtos
| Método | Rota | Perfil exigido |
|--------|------|----------------|
| GET | `/produtos` | Autenticado |
| POST | `/produtos` | ADMIN, GERENTE |
| GET | `/produtos/{id}` | Autenticado |
| PUT | `/produtos/{id}` | ADMIN, GERENTE |

### Pedidos (Fluxo Crítico)
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/pedidos` | Criar pedido |
| GET | `/pedidos` | Listar pedidos |
| GET | `/pedidos/{id}` | Detalhe do pedido |
| PATCH | `/pedidos/{id}/status` | Atualizar status |
| POST | `/pedidos/{id}/pagamento` | Processar pagamento mock |

### Estoque
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/estoque/movimentos` | Registrar entrada/saída |
| GET | `/estoque/saldo/{unidade_id}` | Saldo por unidade |

### Fidelidade
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/fidelidade/saldo` | Consultar pontos |
| GET | `/fidelidade/historico` | Extrato de pontos |
| POST | `/fidelidade/resgatar` | Resgatar pontos |

---

## 🔐 Segurança e LGPD

- **Senhas** armazenadas com hash bcrypt — nunca em texto puro
- **JWT** com expiração de 60 minutos (configurável no `.env`)
- **Controle de acesso por perfil** em todas as rotas sensíveis
- **Consentimento LGPD** registrado no cadastro do usuário (`consentimento_fidelidade`, `consentimento_marketing`)
- **Log de auditoria** (`logs_auditoria`) rastreia ações sensíveis com IP e usuário responsável

---

## 🧪 Testes Automatizados

O projeto possui **22 testes automatizados** cobrindo cenários positivos e negativos.

### Como executar

```bash
pytest tests/test_api.py -v
```

### Resultado esperado

```
tests/test_api.py::test_login_com_sucesso                    PASSED
tests/test_api.py::test_login_senha_errada                   PASSED
tests/test_api.py::test_acesso_sem_estar_logado              PASSED
tests/test_api.py::test_cadastrar_novo_cliente               PASSED
tests/test_api.py::test_nao_cadastrar_email_duplicado        PASSED
tests/test_api.py::test_listar_unidades_logado               PASSED
tests/test_api.py::test_ver_cardapio_da_unidade              PASSED
tests/test_api.py::test_criar_pedido_normal                  PASSED
tests/test_api.py::test_pedido_com_produto_que_nao_existe    PASSED
tests/test_api.py::test_realizar_pagamento                   PASSED
tests/test_api.py::test_nao_pagar_pedido_duas_vezes          PASSED
tests/test_api.py::test_atendente_altera_status              PASSED
tests/test_api.py::test_cliente_nao_pode_mudar_status        PASSED
tests/test_api.py::test_estoque_e_baixado_ao_fazer_pedido    PASSED
tests/test_api.py::test_pontos_fidelidade_sao_concedidos     PASSED
tests/test_api.py::test_resgatar_pontos                      PASSED
tests/test_api.py::test_resgatar_com_saldo_insuficiente      PASSED
tests/test_api.py::test_pedido_com_estoque_insuficiente      PASSED
tests/test_api.py::test_cliente_nao_consegue_listar_usuarios PASSED
tests/test_api.py::test_pedido_pelo_totem                    PASSED
tests/test_api.py::test_filtrar_pedidos_por_canal            PASSED
tests/test_api.py::test_filtro_com_canal_invalido            PASSED

22 passed in ~22s
```

### Plano de Testes — Tabela Resumida

| ID | Função de teste | Cenário | Tipo |
|----|----------------|---------|------|
| T01 | `test_login_com_sucesso` | Login com credenciais válidas retorna token JWT | ✅ Positivo |
| T02 | `test_login_senha_errada` | Login com senha errada retorna 401 | ❌ Negativo |
| T03 | `test_acesso_sem_estar_logado` | Endpoint protegido sem token retorna 401/403 | ❌ Negativo |
| T04 | `test_cadastrar_novo_cliente` | Cadastro de novo cliente retorna 201 | ✅ Positivo |
| T05 | `test_nao_cadastrar_email_duplicado` | E-mail já existente retorna 409 | ❌ Negativo |
| T06 | `test_listar_unidades_logado` | Usuário autenticado lista unidades | ✅ Positivo |
| T07 | `test_ver_cardapio_da_unidade` | Cardápio retorna produtos disponíveis | ✅ Positivo |
| T08 | `test_criar_pedido_normal` | Pedido criado com status AGUARDANDO_PAGAMENTO | ✅ Positivo |
| T09 | `test_pedido_com_produto_que_nao_existe` | Produto inválido retorna 404 | ❌ Negativo |
| T10 | `test_realizar_pagamento` | Pagamento mock retorna APROVADO ou RECUSADO | ✅ Positivo |
| T11 | `test_nao_pagar_pedido_duas_vezes` | Segunda tentativa de pagamento retorna 400 | ❌ Negativo |
| T12 | `test_atendente_altera_status` | Atendente atualiza status para EM_PREPARO | ✅ Positivo |
| T13 | `test_cliente_nao_pode_mudar_status` | Cliente tentando alterar status recebe 403 | ❌ Negativo |
| T14 | `test_estoque_e_baixado_ao_fazer_pedido` | Saldo de estoque diminui após pedido | ✅ Positivo |
| T15 | `test_pontos_fidelidade_sao_concedidos` | Pontos concedidos após pagamento aprovado | ✅ Positivo |
| T16 | `test_resgatar_pontos` | Resgate com saldo suficiente retorna 200 | ✅ Positivo |
| T17 | `test_resgatar_com_saldo_insuficiente` | Resgate acima do saldo retorna 400 | ❌ Negativo |
| T18 | `test_pedido_com_estoque_insuficiente` | Quantidade acima do estoque retorna 400 | ❌ Negativo |
| T19 | `test_cliente_nao_consegue_listar_usuarios` | Cliente tentando listar usuários recebe 403 | ❌ Negativo |
| T20 | `test_pedido_pelo_totem` | Pedido via canal TOTEM aceito corretamente | ✅ Positivo |
| T21 | `test_filtrar_pedidos_por_canal` | Filtro ?canal_pedido=TOTEM retorna só TOTEMs | ✅ Positivo |
| T22 | `test_filtro_com_canal_invalido` | Canal inválido no filtro retorna 400 | ❌ Negativo |

---

## 🚀 Fluxo Crítico — Passo a Passo

Este é o fluxo principal exigido pelo roteiro, testável diretamente no Swagger (`/docs`):

```
1. POST /auth/login          → obtém token JWT
2. POST /pedidos             → cria pedido (status: AGUARDANDO_PAGAMENTO)
3. POST /pedidos/{id}/pagamento → processa pagamento mock
   → se APROVADO: status vira PAGAMENTO_CONFIRMADO + pontos concedidos
   → se RECUSADO: status vira CANCELADO
4. PATCH /pedidos/{id}/status → atendente avança: EM_PREPARO → PRONTO → ENTREGUE
```

---

## 💡 O que eu adicionaria com mais tempo

Algumas melhorias que ficaram como proposta futura:

- **Autenticação social** (Google/redes sociais) via OAuth2
- **Painel administrativo web** para gerentes acompanharem pedidos em tempo real
- **Relatórios de vendas por unidade** com filtros por período e categoria
- **Envio de e-mail** de confirmação de pedido e notificação de status
- **Integração real com gateway de pagamento** (ex.: Stripe ou PagSeguro)
- **Deploy em nuvem** (Railway ou Render) para o Swagger ficar acessível publicamente

---

## 📁 Estrutura de Dados (Resumo do DER)

```
usuarios ──────────────────────────────────────────────────────────┐
    │ id, nome, email, senha_hash, perfil, ativo                   │
    │ consentimento_fidelidade, consentimento_marketing             │
    │                                                               │
    ├── pedidos (cliente_id → usuarios.id)                         │
    │       │ id, unidade_id, canal_pedido, status, total          │
    │       │                                                       │
    │       ├── itens_pedido (pedido_id → pedidos.id)              │
    │       │       id, produto_id, quantidade, preco_unitario      │
    │       │                                                       │
    │       └── pagamentos (pedido_id → pedidos.id)                │
    │               id, forma_pagamento, status, gateway_ref        │
    │                                                               │
    ├── pontos_fidelidade (usuario_id → usuarios.id)               │
    │       id, saldo                                               │
    │                                                               │
    └── historico_fidelidade (usuario_id → usuarios.id)            │
            id, tipo, pontos, descricao                             │
                                                                    │
unidades ──────────────────────────────────────────────────────────┘
    │ id, nome, cidade, estado, endereco, ativa
    │
    ├── cardapio_itens (unidade_id + produto_id → unique)
    │       disponivel, preco_local
    │
    └── estoque_movimentos (unidade_id → unidades.id)
            produto_id, tipo (ENTRADA/SAIDA), quantidade

produtos
    id, nome, descricao, preco, categoria, ativo

logs_auditoria
    id, usuario_id, acao, entidade, entidade_id, detalhe, ip
```

---

*Projeto desenvolvido para fins acadêmicos — UNINTER 2026*
