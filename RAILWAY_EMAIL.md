# 📧 Guia de Configuração de Email no Railway

## ✅ **Modificação Realizada**

O código foi atualizado para suportar configuração de email via **variáveis de ambiente**, funcionando em:
- ✅ Streamlit Cloud (via secrets.toml)
- ✅ Railway (via variáveis de ambiente)
- ✅ Heroku (via variáveis de ambiente)
- ✅ Qualquer plataforma

---

## 🚀 **Como Configurar Email no Railway**

### **Passo 1: Acesse seu projeto no Railway**

1. Vá para: https://railway.app
2. Faça login e abra seu projeto `Elos_conciliador`

### **Passo 2: Abra a aba "Variables"**

1. No dashboard do projeto, clique na aba **"Variables"** (ou "Environment")
2. Você verá uma lista de variáveis de ambiente

### **Passo 3: Adicione as Variáveis de Email**

Clique em **"New Variable"** e adicione as seguintes variáveis, **uma por vez**:

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `EMAIL_HOST` | `smtp.gmail.com` | Servidor SMTP do Gmail |
| `EMAIL_PORT` | `587` | Porta SMTP (TLS) |
| `EMAIL_FROM` | `seu_email@gmail.com` | Seu email Gmail |
| `EMAIL_PASSWORD` | `sua_senha_app_aqui` | Senha de aplicativo Gmail |
| `EMAIL_RECIPIENT` | `destinatario@gmail.com` | Email destinatário padrão |

### **📸 Visual da Configuração:**

```
┌─────────────────────────────────────────┐
│ Variables                               │
├─────────────────────────────────────────┤
│ OPENAI_API_KEY = sk-proj-xxxxx...      │
│ EMAIL_HOST = smtp.gmail.com             │
│ EMAIL_PORT = 587                        │
│ EMAIL_FROM = walterrosa2@gmail.com      │
│ EMAIL_PASSWORD = xxxxxxxxxxx            │
│ EMAIL_RECIPIENT = ia@enthusconsulting...│
└─────────────────────────────────────────┘
```

---

## 🔐 **Como Obter a Senha de Aplicativo Gmail**

### **⚠️ IMPORTANTE:** Não use sua senha normal do Gmail!

### **Passo a Passo:**

1. **Ative a autenticação de 2 fatores** (se ainda não tiver):
   - Acesse: https://myaccount.google.com/security
   - Ative "Verificação em duas etapas"

2. **Crie uma senha de aplicativo**:
   - Acesse: https://myaccount.google.com/apppasswords
   - Selecione "Mail" como app
   - Selecione "Outro" como dispositivo e digite "Railway"
   - Clique em "Gerar"
   - **Copie a senha de 16 caracteres** (sem espaços)

3. **Use essa senha** na variável `EMAIL_PASSWORD`

---

## 🧪 **Testando a Configuração**

### **Opção 1: Testar no Railway (após deploy)**

1. Aguarde o deploy completar
2. Acesse a URL do seu app
3. Faça login
4. Faça upload de uma planilha
5. Teste o envio de email

### **Opção 2: Testar Localmente**

Adicione as variáveis ao seu arquivo `.env` local:

```env
OPENAI_API_KEY=sk-proj-xxxxx...

# Configurações de Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_FROM=walterrosa2@gmail.com
EMAIL_PASSWORD=sua_senha_app_aqui
EMAIL_RECIPIENT=ia@enthusconsulting.com.br
```

Execute:
```bash
streamlit run app.py
```

---

## 🔄 **Prioridade de Configuração**

O código agora funciona com esta ordem de prioridade:

1. **st.secrets** (Streamlit Cloud)
2. **Variáveis de ambiente** (Railway, Heroku, etc)
3. **Valores padrão** (fallback)

Isso significa que:
- No **Streamlit Cloud**: Usa `secrets.toml`
- No **Railway/Heroku**: Usa variáveis de ambiente
- **Localmente**: Pode usar qualquer um (`.env` ou `secrets.toml`)

---

## ✅ **Exemplo Completo de Variáveis no Railway**

```
OPENAI_API_KEY=sk-proj-abc123def456ghi789...
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_FROM=walterrosa2@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
EMAIL_RECIPIENT=ia@enthusconsulting.com.br
```

---

## 🛠️ **Troubleshooting**

### **Erro: "SMTP authentication failed"**
- ✅ Verifique se está usando uma **senha de aplicativo**, não a senha normal
- ✅ Confirme que a autenticação de 2 fatores está ativada
- ✅ Verifique se copiou a senha sem espaços

### **Erro: "Connection timed out"**
- ✅ Verifique se `EMAIL_PORT` está como `587`
- ✅ Alguns provedores bloqueiam porta 587, tente `465`
- ✅ Verifique se a plataforma permite conexões SMTP

### **Email não chega**
- ✅ Verifique a caixa de SPAM
- ✅ Confirme que o email destinatário está correto
- ✅ Verifique os logs do Railway para erros

---

## 📋 **Checklist de Configuração**

- [ ] Criei a senha de aplicativo do Gmail
- [ ] Adicionei `EMAIL_HOST` no Railway
- [ ] Adicionei `EMAIL_PORT` no Railway
- [ ] Adicionei `EMAIL_FROM` no Railway
- [ ] Adicionei `EMAIL_PASSWORD` no Railway (senha de app)
- [ ] Adicionei `EMAIL_RECIPIENT` no Railway
- [ ] Testei o envio de email
- [ ] Verifiquei se o email chegou (incluindo SPAM)

---

## 🎯 **Próximo Passo**

Depois de configurar as variáveis no Railway:

1. Faça o **commit e push** do código atualizado:
```bash
git add app.py
git commit -m "feat: Suporte a configuração de email via env vars"
git push origin main
```

2. O Railway fará **redeploy automático**

3. Teste a funcionalidade de email!

---

**✅ Pronto! Agora sua aplicação funcionará em qualquer plataforma!** 🚀
