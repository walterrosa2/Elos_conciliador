# Task List - Fluxo Único de Conciliação e E-mail

## Refatoração de UI e Lógica (`app.py`)

- [x] **1. Mover Campo de E-mail:**
  - Reposicionar a linha `email_user = st.text_input("📧 Informe o e-mail destinatário para envio do resultado:")` para que fique logo após a leitura do arquivo Excel.

- [x] **2. Unificar Botões de Ação:**
  - Remover os botões "Continuar para Etapa 2" e "Continuar para Etapa 3".
  - Criar um único botão central: `if st.button("🚀 Iniciar Conciliação e Enviar por E-mail"):`

- [x] **3. Validar E-mail Obrigatório:**
  - Adicionado `if not email_user: st.error(...)` e `st.stop()` para impedir processamento sem e-mail.

- [x] **4. Integrar Lógica de Processamento:**
  - Bloco de `processar_em_chunks` movido para dentro do botão único.

- [x] **5. Integrar Lógica de Envio de E-mail:**
  - Geração de Excel e envio via `enviar_email_bytes` integrados logo após o processamento.

- [x] **6. Limpeza de Código:**
  - Removidos estados de sessão e botões obsoletos.
