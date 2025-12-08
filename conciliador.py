# -*- coding: utf-8 -*-
"""
conciliador.py — ELOS (ajustado com nova lógica de chunking)
Melhorias:
1) Chunking refinado: agrupamento por Data, SubPlano Prev e Conta.
2) Ordenação dentro de cada grupo por valor absoluto (Débito/Crédito).
3) Pré-processamento garantindo valores numéricos em módulo.
4) Estrutura de logs, prompts e chamadas mantida.
"""

from __future__ import annotations

import os
import json
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Callable  # ✅ incluir Callable


# =========================
# Carregamento do .env
# =========================
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

def _openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("❌ ERRO: Variável OPENAI_API_KEY não encontrada no .env ou ambiente.")
    return OpenAI(api_key=api_key)

# =========================
# Configurações padrão
# =========================
MODEL = os.getenv("ELOS_OPENAI_MODEL", "gpt-4.1-2025-04-14")
TIMEOUT_S = int(os.getenv("ELOS_OPENAI_TIMEOUT_S", "120"))
MAX_TOKENS = int(os.getenv("ELOS_OPENAI_MAX_TOKENS", "4000"))
MAX_LINHAS_LOTE = int(os.getenv("ELOS_MAX_LINHAS_LOTE", "16"))
HIST_TRUNC = int(os.getenv("ELOS_HIST_TRUNC", "100"))

COLS_ENVIO = ["Data", "Lanc.", "Conta", "SubPlano Prev", "Historico", "Débito", "Crédito"]
COLS_MINIMAS = ["Data","Lanc.","Conta","SubPlano Prev","Historico","Débito","Crédito","Saldo"]

# =========================
# Utilidades de log
# =========================
def _ensure_dirs():
    os.makedirs("logs", exist_ok=True)

def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _save_text(path: str, text: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def _save_json(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# Carregar prompt base
# =========================
# substitua sua função carregar_prompt por esta
def carregar_prompt(path: Optional[str] = "prompt/elos_prompt.txt") -> str:
    """
    Tenta carregar o prompt de múltiplos caminhos razoáveis.
    Aceita caminho absoluto/relativo via argumento `path`.
    """
    candidatos = []

    # 1) Caminho explicitamente recebido (se vier)
    if path:
        try:
            candidatos.append(Path(path))
        except TypeError:
            # Se alguém passar algo não-string (ex.: None ou objeto), ignora
            pass

    # 2) Pastas padrão relativas ao arquivo atual e ao CWD
    aqui = Path(__file__).parent
    candidatos += [
        aqui / "prompt" / "elos_prompt.txt",
        aqui / "elos_prompt.txt",
        Path.cwd() / "prompt" / "elos_prompt.txt",
        Path.cwd() / "elos_prompt.txt",
    ]

    # 3) Var de ambiente opcional (ex.: ELOS_PROMPT=C:\...\elos_prompt.txt)
    env_prompt = os.getenv("ELOS_PROMPT")
    if env_prompt:
        try:
            candidatos.insert(0, Path(env_prompt))
        except TypeError:
            pass

    # 4) Itera candidatos até achar um arquivo legível
    erros = []
    for p in candidatos:
        try:
            if p.is_file():
                return p.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            # Em Windows, nomes com streams (ex.: :Zone.Identifier) podem disparar Errno 22
            erros.append(f"{p} -> {e}")

    # 5) Se nada deu certo, erga exceção com diagnóstico útil
    caminhos_testados = ", ".join(str(p) for p in candidatos)
    msg = (
        "Prompt base não encontrado ou ilegível.\n"
        f"Caminhos testados: {caminhos_testados}\n"
    )
    if erros:
        msg += "Erros encontrados: " + " | ".join(erros)
    raise FileNotFoundError(msg)

# =========================
# Pré-processamento
# =========================
def _normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in df.columns if c in COLS_MINIMAS]
    if not keep:
        raise ValueError("DataFrame não contém colunas compatíveis para conciliação.")
    d = df[keep].copy()

    # Garantir numéricos sempre em módulo
    for col in ["Débito", "Crédito", "Saldo"]:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0.0).abs()

    # Sanear campo Historico
    if "Historico" in d.columns:
        d["Historico"] = (
            d["Historico"].astype(str)
            .str.replace('"', "'", regex=False)             # troca aspas duplas por simples
            .str.replace(r"[\r\n\t]+", " ", regex=True)     # remove quebras de linha/tabs
            .str.replace(r"\s{2,}", " ", regex=True)        # normaliza espaços duplos
            .str.strip()                                    # remove espaços no início/fim
            .str.slice(0, HIST_TRUNC)                       # limita tamanho
        )

    # Converter Data
    if "Data" in d.columns:
        d["Data"] = pd.to_datetime(d["Data"], errors="coerce")

    return d


def _csv_enxuto(df: pd.DataFrame) -> str:
    cols = [c for c in COLS_ENVIO if c in df.columns]
    return df[cols].to_csv(index=False)
    
def _save_lote_csv(df: pd.DataFrame, nome: str):
    """Salva um lote de registros como CSV para auditoria."""
    _ensure_dirs()
    caminho = os.path.join("logs", f"lote_{_ts()}_{nome}.csv")
    df.to_csv(caminho, index=False, encoding="utf-8-sig")

# =========================
# Chunking refinado
# =========================
def dividir_em_lotes(df: pd.DataFrame, max_linhas: int = MAX_LINHAS_LOTE) -> List[pd.DataFrame]:
    # Agora exigimos apenas SubPlano Prev e Conta
    if not {"Conta", "SubPlano Prev"}.issubset(df.columns):
        raise ValueError("As colunas 'Conta' e 'SubPlano Prev' são obrigatórias para o chunking.")

    df_sorted = df.copy()
    # valor_abs = proximidade por módulo dos valores
    df_sorted["valor_abs"] = df_sorted[["Débito","Crédito"]].abs().sum(axis=1)

    # NOVA ordenação global (sem Data)
    df_sorted = df_sorted.sort_values(
        by=["SubPlano Prev","Conta","valor_abs"],
        kind="stable"
    )

    lotes: List[pd.DataFrame] = []
    # NOVO agrupamento: SubPlano Prev + Conta (sem Data)
    for (subplano, conta), grupo in df_sorted.groupby(["SubPlano Prev","Conta"], dropna=False):
        n = len(grupo)
        for start in range(0, n, max_linhas):
            fatia = grupo.iloc[start:start + max_linhas].copy()

            # Log do lote (sem Data no nome)
            sp = str(subplano).strip().replace(" ", "_")
            ct = str(conta).strip().replace(" ", "_")
            chave = f"{sp}_{ct}_{start//max_linhas+1}"
            _save_lote_csv(fatia, chave)

            lotes.append(fatia)

    return lotes



# =========================
# Construção do prompt
# =========================
def _montar_prompt_lote(prompt_base: str, df_lote: pd.DataFrame) -> str:
    csv_block = _csv_enxuto(df_lote)
    partes = [
        prompt_base,
        "",
        "---",
        "📄 Abaixo está o conteúdo da planilha enviada (lote parcial):",
        "",
        csv_block,
        "",
        "⚠️ Retorne SOMENTE JSON válido, com as chaves:",
        '- "dados"',
        'Ou, em caso de erro estruturado: {"erro": "<mensagem>"}'
    ]
    return "\n".join(partes)

# =========================
# Chamada à LLM
# =========================
def _chamar_llm(prompt: str,
                model: str = MODEL,
                timeout_s: int = TIMEOUT_S,
                max_tokens: int = MAX_TOKENS) -> Dict[str, Any]:
    _ensure_dirs()
    uid = uuid.uuid4().hex[:8]
    
    # Remover o log de envio
    # _save_text(os.path.join("logs", f"prompt_{_ts()}_{uid}.txt"), prompt)  # Remover/Comentar esta linha

    client = _openai_client()
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Você é o ELOS, especialista em conciliação bancária. Responda apenas JSON válido."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
            timeout=timeout_s,
        )
        dt = time.perf_counter() - t0
        content = resp.choices[0].message.content
        
        # Log do retorno da OpenAI
        _save_text(os.path.join("logs", f"resp_{_ts()}_{uid}.json"), content)  # Log do retorno

        out = json.loads(content)
        out["_meta"] = {"duracao_s": round(dt,3), "uid": uid}
        return out
    except Exception as e:
        dt = time.perf_counter() - t0
        err_text = f"Duracao: {round(dt,3)}s\nErro: {type(e).__name__}: {e}"
        
        # Log de erro no retorno
        _save_text(os.path.join("logs", f"erro_{_ts()}_{uid}.txt"), err_text)
        raise

# =========================
# Agregação de resultados
# =========================
def _agregar_resultados(lotes_saidas: List[Dict[str, Any]]) -> Dict[str, Any]:
    dados_all, resumo_all, nao_conc_all, erros = [], [], [], []
    for saida in lotes_saidas:
        if not isinstance(saida, dict):
            continue
        if "erro" in saida:
            erros.append(saida["erro"])
        if "dados" in saida:
            dados_all.extend(saida["dados"])
        if "resumo" in saida:
            resumo_all.extend(saida["resumo"])
        if "nao_conciliados" in saida:
            nao_conc_all.extend(saida["nao_conciliados"])
    result = {"dados": dados_all, "resumo": resumo_all, "nao_conciliados": nao_conc_all}
    if erros:
        result["erros"] = erros
    return result

# =========================
# API pública
# =========================
# topo do arquivo


def processar_em_chunks(
    df: pd.DataFrame,
    nome_conciliacao: Optional[str] = None,
    prompt_base_path: str = "prompt/elos_prompt.txt",
    max_linhas: int = MAX_LINHAS_LOTE,
    timeout_s: int = TIMEOUT_S,
    max_tokens: int = MAX_TOKENS,
    model: str = MODEL,
    on_progress: Optional[Callable[[int, int], None]] = None  # ✅ NOVO
) -> Dict[str, Any]:
    df_norm = _normalizar_dataframe(df)
    lotes = dividir_em_lotes(df_norm, max_linhas=max_linhas)
    if not lotes:
        return {"dados": [], "resumo": [], "nao_conciliados": [], "erros": ["DataFrame vazio após chunking."]}
    prompt_base = carregar_prompt(prompt_base_path)

    saidas = []
    total = len(lotes)
    for i, lote in enumerate(lotes, start=1):
        try:
            prompt = _montar_prompt_lote(prompt_base, lote)
            saida = _chamar_llm(prompt, model=model, timeout_s=timeout_s, max_tokens=max_tokens)
            saida["_lote"] = {"indice": i, "linhas": len(lote)}
            saidas.append(saida)
        except Exception as e:
            saidas.append({"erro": f"Lote {i}: {str(e)}"})
        # ✅ atualiza progresso a cada lote
        if on_progress:
            on_progress(i, total)

    combinado = _agregar_resultados(saidas)
    combinado["_meta"] = {
        "modelo": model,
        "timeout_s": timeout_s,
        "max_tokens": max_tokens,
        "max_linhas_lote": max_linhas,
        "total_lotes": total,
        "nome_conciliacao": nome_conciliacao or ""
    }
    return combinado

def processar_conciliacao(df: pd.DataFrame,
                          prompt_base_path: str = "prompt/elos_prompt.txt",
                          timeout_s: int = TIMEOUT_S,
                          max_tokens: int = MAX_TOKENS,
                          model: str = MODEL) -> Dict[str, Any]:
    df_norm = _normalizar_dataframe(df)
    prompt_base = carregar_prompt(prompt_base_path)
    prompt = _montar_prompt_lote(prompt_base, df_norm)
    try:
        return _chamar_llm(prompt, model=model, timeout_s=timeout_s, max_tokens=max_tokens)
    except Exception as e:
        return {"erro": str(e)}
