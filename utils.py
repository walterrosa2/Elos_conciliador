import pandas as pd
import os
import datetime
from typing import Dict, Any
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
# utils.py
from io import BytesIO
from email.mime.application import MIMEApplication

def enviar_email(nome_arquivo, destinatario):
    """
    Envia o arquivo gerado por email utilizando o servidor SMTP do Gmail.

    :param nome_arquivo: Caminho completo do arquivo a ser enviado.
    :param destinatario: Email do destinatário.
    """
    msg = MIMEMultipart()
    msg['From'] = 'walterrosa2@gmail.com'  # Remetente
    msg['To'] = destinatario  # Destinatário
    msg['Subject'] = 'Resultado de Conciliação'

    # Anexando o arquivo
    attachment = MIMEBase('application', 'octet-stream')
    with open(nome_arquivo, 'rb') as f:
        attachment.set_payload(f.read())
    encoders.encode_base64(attachment)
    attachment.add_header(
        'Content-Disposition',
        f'attachment; filename="{os.path.basename(nome_arquivo)}"'
    )
    msg.attach(MIMEText("Olá! Segue em anexo o resultado da conciliação.\n\nAtt,", "plain"))

    # Envio de email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('walterrosa2@gmail.com', 'rgpwxnusytalgkun')  # Login no Gmail
        text = msg.as_string()
        server.sendmail('ia@enthusconsulting.com.br', destinatario, text)
        server.quit()
        print(f"Email enviado para {destinatario}")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")


def _enforce_strict_pairing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Garante pareamento estrito (nunca concilia unilateralmente).
    Regras:
      - Grupo: (Conta, SubPlano Prev, valor_abs)
      - valor_abs: se não existir, calcula como |Débito| + |Crédito| (2 casas)
      - lado: "D" se Débito>0 e Crédito==0, "C" se Crédito!=0 (ou Débito==0)
      - Forma min(nD, nC) pares por grupo; excedentes ficam "Não conciliado"
      - id_par preenchido somente nos pares, compartilhado entre D e C
    """
    if df is None or df.empty:
        return df.copy() if df is not None else df

    d = df.copy()

    # STATUS default
    if "STATUS" not in d.columns:
        d["STATUS"] = "Não conciliado"

    # lado
    if "lado" not in d.columns:
        d["lado"] = None
    # Inferir lado se não existir ou se houver valores inconsistentes
    def _infer_lado(row):
        deb = row.get("Débito", 0.0) or 0.0
        cre = row.get("Crédito", 0.0) or 0.0
        # Se ambas colunas existirem, considerar qual é não-zero
        if abs(deb) > 0 and abs(cre) == 0:
            return "D"
        if abs(cre) > 0 and abs(deb) == 0:
            return "C"
        # fallback: sinal líquido
        signed = (deb or 0.0) - (cre or 0.0)
        return "D" if signed > 0 else "C"

    d["lado"] = d.apply(lambda r: r["lado"] if pd.notna(r.get("lado")) and r.get("lado") in ("D","C") else _infer_lado(r), axis=1)

    # valor_abs
    if "valor_abs" not in d.columns:
        d["valor_abs"] = (d.get("Débito", 0.0).abs() + d.get("Crédito", 0.0).abs())
    d["valor_abs"] = d["valor_abs"].astype(float).round(2)

    # Campos base
    if "Conta" not in d.columns:
        d["Conta"] = "(sem conta)"
    if "SubPlano Prev" not in d.columns:
        d["SubPlano Prev"] = "(sem subplano)"
    if "id_par" not in d.columns:
        d["id_par"] = ""

    # Ordenação estável para consistência de pareamento
    if "Data" in d.columns:
        d = d.sort_values(by=["SubPlano Prev","Conta","valor_abs","Data"], kind="stable")
    else:
        d = d.sort_values(by=["SubPlano Prev","Conta","valor_abs"], kind="stable")

    # Limpa rótulos antes de recalcular
    d["STATUS"] = "Não conciliado"
    d["id_par"] = ""

    # Pairing por grupo
    par_counter_global = {}
    for (sub, conta, val), gidx in d.groupby(["SubPlano Prev","Conta","valor_abs"]).groups.items():
        idx = list(gidx)
        # Separar por lado
        d_idx = [i for i in idx if d.at[i, "lado"] == "D"]
        c_idx = [i for i in idx if d.at[i, "lado"] == "C"]
        n_pairs = min(len(d_idx), len(c_idx))
        if n_pairs == 0:
            continue
        # contador ordinal por grupo
        key = (sub, conta, val)
        if key not in par_counter_global:
            par_counter_global[key] = 0
        for k in range(n_pairs):
            par_counter_global[key] += 1
            ordinal = par_counter_global[key]
            idp = f"PAR-{conta}-{sub}-{val:.2f}-{ordinal:03d}"
            iD = d_idx[k]
            iC = c_idx[k]
            d.at[iD, "STATUS"] = "Conciliado"
            d.at[iC, "STATUS"] = "Conciliado"
            d.at[iD, "id_par"] = idp
            d.at[iC, "id_par"] = idp

    return d

def listar_conciliacoes():
    caminho = "resultados"
    if not os.path.exists(caminho):
        return []
    arquivos = [f for f in os.listdir(caminho) if f.endswith(".xlsx")]
    return sorted(arquivos, reverse=True)

def _as_float(x):
    try:
        v = float(x)
        # normaliza -0.0 -> 0.0
        return 0.0 if abs(v) < 1e-12 else v
    except Exception:
        return 0.0

def _normalize_dados(df: pd.DataFrame) -> pd.DataFrame:
    # Tipos
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    for col in ["Débito", "Crédito"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0).map(_as_float)

    # Coluna para ordenação por proximidade
    if {"Débito", "Crédito"}.issubset(df.columns):
        df["_valor_abs"] = df["Débito"].abs() + df["Crédito"].abs()
    else:
        df["_valor_abs"] = 0.0

    # Ordenação no mesmo critério do bloco
    sort_cols = [c for c in ["SubPlano Prev", "Conta", "_valor_abs"] if c in df.columns]
    df = df.sort_values(by=sort_cols, kind="stable").reset_index(drop=True)

    # Ordena colunas numa ordem amigável
    base_order = ["Data","Lanc.","Conta","SubPlano Prev","Historico","Débito","Crédito","STATUS","Check Histórico"]
    ordered = [c for c in base_order if c in df.columns] + [c for c in df.columns if c not in base_order and c != "_valor_abs"]
    df = df[ordered]
    return df

def _calc_resumo_from_dados(df_dados: pd.DataFrame) -> pd.DataFrame:
    have_status = "STATUS" in df_dados.columns
    grp = df_dados.groupby(["Conta", "SubPlano Prev"], dropna=False)
    resumo = grp.agg(
        **{
            "Total Débito": ("Débito", "sum"),
            "Total Crédito": ("Crédito", "sum"),
            "Qtde Lançamentos": ("Lanc.", "count"),
            "Qtde Conciliados": ("STATUS", lambda s: (s == "Conciliado").sum()) if have_status else ("Lanc.", "count")
        }
    ).reset_index()

    # % Conciliação
    if "Qtde Conciliados" in resumo.columns and "Qtde Lançamentos" in resumo.columns:
        resumo["% Conciliação"] = (
            (resumo["Qtde Conciliados"] / resumo["Qtde Lançamentos"]) * 100.0
        ).round(2)
    else:
        resumo["% Conciliação"] = 0.0

    # Limpa -0.00
    for col in ["Total Débito", "Total Crédito"]:
        if col in resumo.columns:
            resumo[col] = resumo[col].map(_as_float)
    return resumo

def _calc_blocos_subconta(df_dados: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["SubPlano Prev", "Conta"] if c in df_dados.columns]
    if len(cols) < 2:
        return pd.DataFrame()

    grp = df_dados.groupby(cols, dropna=False).agg(
        **{
            "Total Débito": ("Débito", "sum") if "Débito" in df_dados.columns else ("Conta","size"),
            "Total Crédito": ("Crédito", "sum") if "Crédito" in df_dados.columns else ("Conta","size"),
            "Qtde Lançamentos": ("Lanc.", "count") if "Lanc." in df_dados.columns else ("Conta","size"),
            "Qtde Conciliados": ("STATUS", lambda s: (s == "Conciliado").sum()) if "STATUS" in df_dados.columns else ("Conta","size"),
        }
    ).reset_index()

    if "Qtde Lançamentos" in grp.columns and "Qtde Conciliados" in grp.columns:
        grp["% Conciliação"] = ((grp["Qtde Conciliados"] / grp["Qtde Lançamentos"]) * 100.0).round(2)
    else:
        grp["% Conciliação"] = 0.0

    grp = grp.sort_values(by=["SubPlano Prev", "Conta"], kind="stable")
    return grp

def _check_historico(df: pd.DataFrame) -> pd.DataFrame:
    """
    Verifica, para linhas marcadas como Conciliado, se existe interseção de números no texto do 'Historico'
    entre os dois lados do par. Usa 'id_par' quando disponível; caso contrário, faz um fallback por
    (Conta, SubPlano Prev, valor_abs) considerando pares de tamanho 2.
    Resultado na coluna "Check Histórico":
      - "Verificado histórico +<n1,n2,...>" se houver interseção
      - "Histórico divergente" se não houver números coincidentes
      - "" (vazio) para linhas não conciliadas ou sem par válido
    """
    if df is None or df.empty:
        return df

    d = df.copy()
    if "Check Histórico" not in d.columns:
        d["Check Histórico"] = ""

    # Função auxiliar para extrair números do histórico
    import re as _re
    def extrair_numeros(txt):
        return set(_re.findall(r"\d+", str(txt)))

    # Preferimos checar por id_par quando existir (pareamento exato)
    if "id_par" in d.columns:
        conciliados = d[d.get("STATUS", "").astype(str) == "Conciliado"]
        for par, grupo in conciliados.groupby("id_par"):
            if not par or pd.isna(par):
                continue
            if len(grupo) != 2:
                continue  # somente pares exatos
            idx1, idx2 = grupo.index
            nums1 = extrair_numeros(d.at[idx1, "Historico"] if "Historico" in d.columns else "")
            nums2 = extrair_numeros(d.at[idx2, "Historico"] if "Historico" in d.columns else "")
            intersec = nums1.intersection(nums2)
            if intersec:
                txt = f"Verificado histórico +{','.join(sorted(intersec))}"
            else:
                txt = "Histórico divergente"
            d.at[idx1, "Check Histórico"] = txt
            d.at[idx2, "Check Histórico"] = txt
        return d

    # Fallback sem id_par: agrupa por (Conta, SubPlano Prev, valor_abs) e checa pares de tamanho 2
    if "valor_abs" not in d.columns:
        d["valor_abs"] = (d.get("Débito", 0.0).abs() + d.get("Crédito", 0.0).abs()).astype(float).round(2)

    conciliados = d[d.get("STATUS", "").astype(str) == "Conciliado"]
    chave_cols = ["Conta", "SubPlano Prev", "valor_abs"]
    conciliados["__chave__"] = conciliados[chave_cols].astype(str).agg("|".join, axis=1)
    for chave, grupo in conciliados.groupby("__chave__"):
        if len(grupo) != 2:
            continue
        idx1, idx2 = grupo.index
        nums1 = extrair_numeros(d.at[idx1, "Historico"] if "Historico" in d.columns else "")
        nums2 = extrair_numeros(d.at[idx2, "Historico"] if "Historico" in d.columns else "")
        intersec = nums1.intersection(nums2)
        if intersec:
            txt = f"Verificado histórico +{','.join(sorted(intersec))}"
        else:
            txt = "Histórico divergente"
        d.at[idx1, "Check Histórico"] = txt
        d.at[idx2, "Check Histórico"] = txt

    if "__chave__" in d.columns:
        d.drop(columns=["__chave__"], inplace=True, errors="ignore")
    return d

def gerar_nome_conciliacao(nome_original: str) -> str:
    base = os.path.splitext(nome_original)[0].replace(" ", "_")
    agora = datetime.datetime.now().strftime("%d%m%Y_%H%M")
    return f"{base}_{agora}.xlsx"

def salvar_excel(resultado_json: Dict[str, Any], nome_arquivo: str) -> str:
    caminho_pasta = "resultados"
    os.makedirs(caminho_pasta, exist_ok=True)
    caminho_completo = os.path.join(caminho_pasta, nome_arquivo)

    # Monta DataFrames com resiliência
    df_dados = pd.DataFrame(resultado_json.get("dados", []))
    df_resumo = pd.DataFrame(resultado_json.get("resumo", []))
    df_nao = pd.DataFrame(resultado_json.get("nao_conciliados", []))

    # 🔒 Enforce pareamento estrito ANTES de qualquer cálculo/export
    if not df_dados.empty:
        df_dados = _enforce_strict_pairing(df_dados)
        # Recalcula "nao_conciliados" a partir do df_dados ajustado
        if {"STATUS"}.issubset(df_dados.columns):
            df_nao = df_dados[df_dados["STATUS"].astype(str).str.lower() == "não conciliado"].copy()
        # ✅ Checagem de histórico por par
        df_dados = _check_historico(df_dados)
        # Normaliza após enforcement e checagem
        df_dados = _normalize_dados(df_dados)

    # (Re)calcula resumo a partir do df_dados ajustado quando não vier ou vier inconsistente
    if (df_resumo.empty and not df_dados.empty) or (not df_dados.empty and ("%" not in " ".join(df_resumo.columns).lower())):
        df_resumo = _calc_resumo_from_dados(df_dados)

    # Calcula a visão por bloco SubPlano/Conta
    df_blocos = _calc_blocos_subconta(df_dados) if not df_dados.empty else pd.DataFrame()

    with pd.ExcelWriter(caminho_completo, engine="openpyxl") as writer:
        if not df_dados.empty:
            df_dados.to_excel(writer, sheet_name="Dados (Ordenados)", index=False)
        if not df_resumo.empty:
            df_resumo.to_excel(writer, sheet_name="Resumo", index=False)
        if not df_blocos.empty:
            df_blocos.to_excel(writer, sheet_name="Blocos (Sub-Conta)", index=False)
        if not df_nao.empty:
            # Ordena os não conciliados pelo mesmo critério
            df_nao = _normalize_dados(df_nao)
            df_nao.to_excel(writer, sheet_name="Não Conciliados", index=False)

    return caminho_completo



def salvar_excel_bytes(resultado_json: Dict[str, Any], nome_arquivo: str) -> tuple[BytesIO, str]:
    """
    Gera o Excel em memória (BytesIO) com as mesmas abas do salvar_excel.
    Retorna (buffer, filename).
    """
    # --- monta os mesmos DataFrames do salvar_excel ---
    df_dados = pd.DataFrame(resultado_json.get("dados", []))
    df_resumo = pd.DataFrame(resultado_json.get("resumo", []))
    df_nao = pd.DataFrame(resultado_json.get("nao_conciliados", []))

    if not df_dados.empty:
        df_dados = _enforce_strict_pairing(df_dados)
        if {"STATUS"}.issubset(df_dados.columns):
            df_nao = df_dados[df_dados["STATUS"].astype(str).str.lower() == "não conciliado"].copy()
        df_dados = _check_historico(df_dados)
        df_dados = _normalize_dados(df_dados)

    if (df_resumo.empty and not df_dados.empty) or (not df_dados.empty and ("%" not in " ".join(df_resumo.columns).lower())):
        df_resumo = _calc_resumo_from_dados(df_dados)

    df_blocos = _calc_blocos_subconta(df_dados) if not df_dados.empty else pd.DataFrame()

    # --- escreve em memória ---
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        if not df_dados.empty:
            df_dados.to_excel(writer, sheet_name="Dados (Ordenados)", index=False)
        if not df_resumo.empty:
            df_resumo.to_excel(writer, sheet_name="Resumo", index=False)
        if not df_blocos.empty:
            df_blocos.to_excel(writer, sheet_name="Blocos (Sub-Conta)", index=False)
        if not df_nao.empty:
            df_nao = _normalize_dados(df_nao)
            df_nao.to_excel(writer, sheet_name="Não Conciliados", index=False)
    buf.seek(0)
    return buf, nome_arquivo  # mantém o mesmo nome gerado por gerar_nome_conciliacao

def enviar_email_bytes(arquivo_nome: str, arquivo_buffer: BytesIO, destinatario: str,
                       host: str = "smtp.gmail.com", port: int = 587,
                       remetente: str | None = None, password: str | None = None,
                       subject: str = "Resultado de Conciliação",
                       body: str = "Olá! Segue em anexo o resultado da conciliação.") -> None:
    """
    Envia o arquivo (em memória) por e-mail via SMTP.
    """
    if remetente is None or password is None:
        raise ValueError("Remetente e password devem ser informados.")

    msg = MIMEMultipart()
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    part = MIMEApplication(arquivo_buffer.getvalue(), _subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    part.add_header("Content-Disposition", "attachment", filename=os.path.basename(arquivo_nome))
    msg.attach(part)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(remetente, password)
        server.sendmail(remetente, [destinatario], msg.as_string())

