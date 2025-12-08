# 🔹 ELOS - Assistente de Conciliação Bancária e Contábil

Aplicação Streamlit para automatizar a conciliação bancária e contábil utilizando Inteligência Artificial (OpenAI GPT).

## 📌 Funcionalidades

- ✅ Upload de planilhas Excel (.xlsx)
- ✅ Processamento inteligente via OpenAI GPT
- ✅ Conciliação automática de lançamentos débito/crédito
- ✅ Geração de relatórios detalhados em Excel
- ✅ Envio automático por e-mail
- ✅ Sistema de login simples
- ✅ Logs auditáveis com Loguru

## 🚀 Como Executar Localmente

### Pré-requisitos

- Python 3.11+
- Chave de API da OpenAI

### Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/walterrosa2/Elos_conciliador.git
cd Elos_conciliador
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente:**

Crie um arquivo `.env` na raiz do projeto (baseado no `.env.example`):

```env
OPENAI_API_KEY=sua_chave_openai_aqui
```

4. **Configure o Streamlit (opcional para email):**

Crie o arquivo `.streamlit/secrets.toml` (baseado no exemplo):

```toml
[email]
host = "smtp.gmail.com"
port = 587
user = "seu_email@gmail.com"
from = "seu_email@gmail.com"
password = "sua_senha_app_gmail"
recipient = "destinatario@gmail.com"
```

> ⚠️ **Para Gmail**: Use uma [senha de aplicativo](https://myaccount.google.com/apppasswords), não sua senha normal.

5. **Execute a aplicação:**

```bash
streamlit run app.py
```

Ou usando o launcher customizado:

```bash
python run_app.py
```

## 🌐 Deploy em Produção

### Opção 1: Streamlit Cloud (Recomendado - Gratuito)

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Conecte seu repositório GitHub
3. Configure os **Secrets** no painel:
   - Vá em **Settings → Secrets**
   - Adicione as variáveis no formato TOML:

```toml
OPENAI_API_KEY = "sk-proj-..."

[email]
host = "smtp.gmail.com"
port = 587
user = "seu_email@gmail.com"
from = "seu_email@gmail.com"
password = "sua_senha_app"
recipient = "destinatario@gmail.com"
```

4. Deploy automático!

### Opção 2: Railway

1. Acesse [railway.app](https://railway.app)
2. Crie um novo projeto → Deploy from GitHub
3. Selecione o repositório `Elos_conciliador`
4. Configure as variáveis de ambiente:
   - `OPENAI_API_KEY`
   - (Opcionais para email via secrets.toml)
5. Deploy automático!

### Opção 3: Heroku

```bash
heroku create elos-conciliador
heroku config:set OPENAI_API_KEY=sua_chave_aqui
git push heroku main
```

## 📂 Estrutura do Projeto

```
P3_streamlit_v3/
├── app.py                    # Aplicação principal Streamlit
├── conciliador.py            # Motor de conciliação + chamadas OpenAI
├── utils.py                  # Funções auxiliares (Excel, Email, etc)
├── requirements.txt          # Dependências Python
├── runtime.txt               # Versão do Python
├── usuarios.json             # Base de usuários para login
├── prompt/
│   └── elos_prompt.txt      # Prompt base para a IA
├── .env.example             # Template de variáveis de ambiente
├── .streamlit/
│   └── secrets.toml.example # Template de configuração Streamlit
└── logs/                    # Logs de execução (ignorado no git)
```

## 🔐 Segurança

- ⚠️ **NUNCA** commite arquivos `.env` ou `secrets.toml` no Git
- Use variáveis de ambiente ou secrets das plataformas de deploy
- Para Gmail, use [senhas de aplicativo](https://myaccount.google.com/apppasswords)
- Revogue imediatamente qualquer secret exposto acidentalmente

## 📧 Configuração de Email

A aplicação suporta envio de relatórios por email. Configure via `.streamlit/secrets.toml`:

```toml
[email]
host = "smtp.gmail.com"
port = 587
user = "seu_email@gmail.com"
from = "seu_email@gmail.com"
password = "senha_app_gmail"
recipient = "destinatario_padrao@gmail.com"
```

> 💡 **Dica**: O usuário pode especificar um email diferente na interface.

## 🔧 Configurações Avançadas

Você pode ajustar o comportamento da IA através de variáveis de ambiente:

```env
ELOS_OPENAI_MODEL=gpt-4o              # Modelo GPT a usar
ELOS_OPENAI_TIMEOUT_S=120             # Timeout por requisição
ELOS_OPENAI_MAX_TOKENS=4000           # Máximo de tokens
ELOS_MAX_LINHAS_LOTE=16               # Linhas por chunk
```

## 📝 Login

O sistema possui autenticação básica. Usuários estão definidos em `usuarios.json`:

```json
[
  {"usuario": "admin", "senha": "senha123"}
]
```

## 🆘 Suporte

Para problemas ou dúvidas:
- Abra uma [issue no GitHub](https://github.com/walterrosa2/Elos_conciliador/issues)
- Email: ia@enthusconsulting.com.br

## 📄 Licença

Copyright © 2025 - Enthus Consulting

---

**Desenvolvido com ❤️ usando Streamlit e OpenAI**
