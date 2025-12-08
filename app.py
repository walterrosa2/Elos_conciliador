import streamlit as st
from conciliador import processar_conciliacao, processar_em_chunks
from utils import gerar_nome_conciliacao, salvar_excel_bytes, enviar_email_bytes
import pandas as pd
import json
import os

# === Carrega usuários de JSON ===
def carregar_usuarios(path="usuarios.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return []

# === Tela de login simples ===
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Login - ELOS Conciliação")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        usuarios = carregar_usuarios()
        credenciais_validas = any(u["usuario"] == usuario and u["senha"] == senha for u in usuarios)
        if credenciais_validas:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# === Página principal após login ===
st.set_page_config(page_title="ELOS - Conciliação Bancária", layout="centered")
st.title("🔹 ELOS – Assistente de Conciliação Bancária e Contábil")
st.markdown("Faça upload de um arquivo Excel (.xlsx) para iniciar a conciliação.")

# Estado
if "resultado_json" not in st.session_state:
    st.session_state.resultado_json = None

# Upload
arquivo = st.file_uploader("📁 Upload da Planilha Excel", type=["xlsx"])

if arquivo:
    nome_conciliacao = gerar_nome_conciliacao(arquivo.name)
    st.info(f"Nome da conciliação gerado: `{nome_conciliacao}`")

    # Leitura do Excel
    df_excel = pd.read_excel(arquivo, header=2)

    # Etapa 1
    st.write("### Etapa 1: Preparar prompt")
    if st.button("👉 Continuar para Etapa 2 (Enviar à OpenAI)"):
        progresso = st.progress(0)

        def _cb(lote_atual: int, total_lotes: int):
            frac = lote_atual / max(total_lotes, 1)
            progresso.progress(min(max(frac, 0.0), 1.0))

        with st.spinner("🔄 Processando conciliação via OpenAI..."):
            st.session_state.resultado_json = processar_em_chunks(
                df_excel,
                nome_conciliacao,
                on_progress=_cb
            )
        progresso.progress(1)

    # Etapa 2 + 3
    if st.session_state.resultado_json is not None:
        st.write("### Etapa 2: Processar resposta")

        # Campo de email no front
        email_user = st.text_input("📧 Informe o e-mail destinatário para envio do resultado:")
        if email_user:
            st.session_state["email_destinatario"] = email_user

        if st.button("👉 Continuar para Etapa 3 (Gerar Excel e Enviar por Email)"):
            if "erro" in st.session_state.resultado_json:
                st.error(f"❌ Erro durante o processamento: {st.session_state.resultado_json['erro']}")
            else:
                buf, fname = salvar_excel_bytes(st.session_state.resultado_json, nome_conciliacao)

                # Carrega configurações (suporta st.secrets OU variáveis de ambiente)
                try:
                    # Tenta ler do st.secrets (Streamlit Cloud)
                    cfg = st.secrets.get("email", {})
                except Exception:
                    # Se não existir secrets.toml, usa dict vazio
                    cfg = {}
                
                # Prioriza st.secrets, depois env vars, depois padrões
                host = cfg.get("host") or os.getenv("EMAIL_HOST", "smtp.gmail.com")
                port = int(cfg.get("port") or os.getenv("EMAIL_PORT", "587"))
                remetente = cfg.get("from") or os.getenv("EMAIL_FROM", "walterrosa2@gmail.com")
                password = cfg.get("password") or os.getenv("EMAIL_PASSWORD")
                destinatario = st.session_state.get("email_destinatario") or cfg.get("recipient") or os.getenv("EMAIL_RECIPIENT", "ia@enthusconsulting.com.br")

                try:
                    enviar_email_bytes(
                        arquivo_nome=fname,
                        arquivo_buffer=buf,
                        destinatario=destinatario,
                        host=host,
                        port=port,
                        remetente=remetente,
                        password=password,
                        subject="Resultado de Conciliação",
                        body="Olá! Segue em anexo o resultado da conciliação."
                    )
                    st.success("✅ Conciliação finalizada com sucesso!")
                    st.info(f"📧 Arquivo enviado com sucesso para {destinatario}!")
                except Exception as e:
                    st.error(f"❌ Falha ao enviar e-mail: {e}")
