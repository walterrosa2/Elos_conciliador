# PRD - Otimização do Fluxo de Envio de E-mail

## 1. Objetivo
Melhorar a experiência do usuário (UX) no aplicativo Streamlit do ELOS Conciliação. Atualmente, o usuário faz o upload, clica em processar e aguarda cerca de 1 hora. Após esse longo período, ele precisa interagir novamente com a interface para informar o e-mail e solicitar o envio. O objetivo é permitir que o usuário informe o e-mail logo no início (junto com o upload do arquivo) e que todo o fluxo (processamento -> geração de Excel -> envio de e-mail) ocorra de forma assíncrona/contínua com apenas um clique.

## 2. Requisitos Funcionais
- **Input de E-mail Antecipado**: O campo de e-mail deve aparecer imediatamente após o upload do arquivo `.xlsx`.
- **Fluxo Único (One-Click)**: O botão de ação deve iniciar o processamento da OpenAI e, em seguida, automaticamente gerar o arquivo Excel em memória e disparar o e-mail para o endereço fornecido.
- **Feedback Visual**: A barra de progresso do processamento da OpenAI deve ser mantida, seguida por um *spinner* indicando o envio do e-mail, e mensagens de sucesso/falha no final.

## 3. Avaliação de Risco e Impacto na Pipeline Atual (Análise Técnica)
- **Risco Baixo / Seguro**: A alteração concentra-se exclusivamente no arquivo de apresentação (frontend `app.py`). 
- **Funções Core Inalteradas**: As funções do core (`processar_em_chunks`, `salvar_excel_bytes`, `enviar_email_bytes` em `utils.py` e `conciliador.py`) não sofrerão nenhuma alteração.
- **Configurações de E-mail Mantidas**: A lógica de leitura das configurações de e-mail (`st.secrets` e variáveis de ambiente) continuará exatamente a mesma.
- **Estabilidade do Streamlit**: Ao unir o processamento da OpenAI (longa duração) e o envio de e-mail no mesmo bloco de `st.button`, nós mitigamos o risco de o usuário perder o momento de interagir com o segundo botão caso se ausente da frente do computador. O Streamlit manterá o loop do bloco executando até a conclusão e enviará o e-mail automaticamente.

## 4. O que muda no Código?
- O estado da sessão (`st.session_state.resultado_json` e `st.session_state.email_destinatario`) pode ser simplificado, já que as etapas não dependem mais de botões separados forçando *reruns* da interface.
- A "Etapa 1", "Etapa 2" e "Etapa 3" descritas no código serão fundidas visualmente e tecnicamente em uma única esteira.
