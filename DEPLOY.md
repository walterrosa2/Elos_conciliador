# 🚀 Guia de Deploy - ELOS Conciliação Bancária

## ⚠️ **IMPORTANTE: Segurança de Credenciais**

Antes de fazer o deploy, você deve **REVOGAR E CRIAR NOVAS CREDENCIAIS**:

### 1. Nova API Key da OpenAI
- Acesse: https://platform.openai.com/api-keys
- Delete a chave antiga (que estava no .env)
- Crie uma nova chave
- Copie e guarde em local seguro

### 2. Nova Senha de Aplicativo Gmail
- Acesse: https://myaccount.google.com/apppasswords
- Revogue a senha antiga
- Crie uma nova "Senha de app" para "Mail"
- Copie e guarde em local seguro

---

## 📍 Opção 1: Deploy no Streamlit Cloud (RECOMENDADO - Gratuito)

### Vantagens:
- ✅ 100% Gratuito para apps públicos
- ✅ Deploy automático do GitHub
- ✅ HTTPS incluído
- ✅ Reinício automático
- ✅ Gerenciamento simples de secrets

### Passo a Passo:

#### 1. Faça push do código atualizado para GitHub

```bash
cd "c:\Users\walte\OneDrive\Workspace\IA\ELOS\Projeto - Elos Conciliação bancária\conciliador_elos\P3_streamlit_v3"
git add README.md .streamlit/config.toml
git commit -m "docs: Adiciona README e config para deploy"
git push origin main
```

#### 2. Acesse o Streamlit Cloud

- Vá para: https://share.streamlit.io
- Faça login com sua conta GitHub
- Clique em **"New app"**

#### 3. Configure o App

- **Repository**: `walterrosa2/Elos_conciliador`
- **Branch**: `main`
- **Main file path**: `app.py`
- **App URL**: `elos-conciliador` (ou o nome que preferir)

#### 4. Configure os Secrets

Antes de fazer deploy, clique em **"Advanced settings"** → **"Secrets"**

Cole o seguinte conteúdo (substitua pelos seus valores reais):

```toml
OPENAI_API_KEY = "sk-proj-SUA_NOVA_CHAVE_AQUI"

[email]
host = "smtp.gmail.com"
port = 587
user = "seu_email@gmail.com"
from = "seu_email@gmail.com"
password = "sua_nova_senha_app_gmail"
recipient = "destinatario_padrao@gmail.com"
```

#### 5. Deploy!

- Clique em **"Deploy!"**
- Aguarde alguns minutos
- Sua aplicação estará disponível em: `https://elos-conciliador.streamlit.app`

---

## 📍 Opção 2: Deploy no Railway

### Vantagens:
- ✅ $5 de crédito gratuito/mês
- ✅ Deploy direto do GitHub
- ✅ Suporte a Docker
- ✅ Domínio customizado

### Passo a Passo:

#### 1. Acesse o Railway
- Vá para: https://railway.app
- Faça login com GitHub

#### 2. Crie um Novo Projeto
- Clique em **"New Project"**
- Selecione **"Deploy from GitHub repo"**
- Escolha: `walterrosa2/Elos_conciliador`

#### 3. Configure as Variáveis de Ambiente
- Vá para a aba **"Variables"**
- Adicione:
  - `OPENAI_API_KEY` = `sk-proj-SUA_NOVA_CHAVE_AQUI`
  - `PORT` = `8501` (opcional)

#### 4. Configure Secrets do Streamlit (Email)
- Crie um arquivo `secrets.toml` no repositório (NÃO RECOMENDADO)
- OU use apenas a variável OPENAI_API_KEY e configure email manualmente

#### 5. Deploy Automático
- Railway detectará automaticamente que é um projeto Python
- Usará o `requirements.txt` e `runtime.txt`
- O deploy iniciará automaticamente

---

## 📍 Opção 3: Deploy no Heroku

### Passo a Passo:

#### 1. Instale o Heroku CLI
```bash
# Windows (usando winget)
winget install Heroku.HerokuCLI
```

#### 2. Faça Login
```bash
heroku login
```

#### 3. Crie o App
```bash
cd "c:\Users\walte\OneDrive\Workspace\IA\ELOS\Projeto - Elos Conciliação bancária\conciliador_elos\P3_streamlit_v3"
heroku create elos-conciliador
```

#### 4. Configure as Variáveis
```bash
heroku config:set OPENAI_API_KEY=sk-proj-SUA_NOVA_CHAVE_AQUI
```

#### 5. Crie um Procfile
Crie um arquivo na raiz chamado `Procfile` (sem extensão):
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

#### 6. Deploy
```bash
git add Procfile
git commit -m "feat: Adiciona Procfile para Heroku"
git push heroku main
```

---

## 🔐 Gerenciamento de Secrets por Plataforma

### Streamlit Cloud
- **Interface Web**: Settings → Secrets
- **Formato**: TOML
- **Acesso**: `st.secrets["chave"]`

### Railway
- **Interface Web**: Variables
- **Formato**: KEY=VALUE
- **Acesso**: `os.getenv("KEY")`

### Heroku
- **CLI**: `heroku config:set KEY=VALUE`
- **Interface Web**: Settings → Config Vars
- **Formato**: KEY=VALUE
- **Acesso**: `os.getenv("KEY")`

---

## 📝 Checklist Pós-Deploy

Após fazer o deploy, verifique:

- [ ] A aplicação está acessível via URL pública
- [ ] O login funciona corretamente
- [ ] É possível fazer upload de arquivos Excel
- [ ] A integração com OpenAI está funcionando
- [ ] O envio de email funciona (se configurado)
- [ ] As credenciais antigas foram revogadas
- [ ] Os logs estão sendo gerados corretamente

---

## 🆘 Troubleshooting

### Erro: "OPENAI_API_KEY não encontrada"
- Verifique se configurou a variável de ambiente ou secret
- No Streamlit Cloud: use `st.secrets["OPENAI_API_KEY"]`
- No Railway/Heroku: use `os.getenv("OPENAI_API_KEY")`

### Erro: "Falha ao enviar email"
- Verifique se a senha do Gmail é uma "senha de aplicativo"
- Confirme que a autenticação de 2 fatores está ativada
- Verifique as configurações SMTP

### App muito lento
- Considere usar um modelo mais rápido (gpt-3.5-turbo)
- Ajuste a variável `ELOS_MAX_LINHAS_LOTE` para processar menos linhas

### Excesso de uso da API
- Configure limites de uso na OpenAI Platform
- Monitore o uso em: https://platform.openai.com/usage

---

## 💰 Custos Estimados

### Streamlit Cloud
- **Gratuito** para apps públicos
- Apps privados: $20/mês

### Railway
- $5 gratuito/mês
- ~$1-5/mês para apps pequenos

### Heroku
- Dyno Eco: $5/mês
- Dyno Basic: $7/mês

### OpenAI API
- Varia conforme uso
- GPT-4: ~$0.03 por 1K tokens
- GPT-3.5-turbo: ~$0.002 por 1K tokens
- Monitore em: https://platform.openai.com/usage

---

## 🎯 Próximos Passos

Depois do deploy bem-sucedido:

1. Configure alertas de erro
2. Implemente analytics (opcional)
3. Crie backup dos dados
4. Documente processos internos
5. Treine usuários finais

---

**Boa sorte com o deploy! 🚀**
