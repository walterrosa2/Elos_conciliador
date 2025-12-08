import pandas as pd
import os
import datetime
from typing import Dict, Any

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
    base_order = ["Data", "Lanc.", "Conta", "SubPlano Prev", "Historico", "Débito", "Crédito", "STATUS"]
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

    # Normaliza e ordena os dados no critério do bloco
    if not df_dados.empty:
        df_dados = _normalize_dados(df_dados)

    # Se não veio resumo, calcula
    if df_resumo.empty and not df_dados.empty:
        df_resumo = _calc_resumo_from_dados(df_dados)

    # Calcula a visão por bloco Dia/SubPlano/Conta
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
