import pandas as pd
import json
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
from utils import salvar_excel

# 🔐 Carrega .env sobrescrevendo variáveis do sistema
load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    sys.exit("❌ ERRO: Variável OPENAI_API_KEY não encontrada no .env ou ambiente.")

client = OpenAI(api_key=api_key)


# -----------------------------
# FUNÇÕES AUXILIARES
# -----------------------------

def carregar_prompt():
    with open("prompt/elos_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def salvar_log(nome, conteudo, extensao="txt"):
    pasta = "logs"
    os.makedirs(pasta, exist_ok=True)
    agora = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho = os.path.join(pasta, f"{nome}_{agora}.{extensao}")
    with open(caminho, "w", encoding="utf-8") as f:
        if isinstance(conteudo, (dict, list)):
            json.dump(conteudo, f, ensure_ascii=False, indent=2)
        else:
            f.write(str(conteudo))
    return caminho


def dividir_em_lotes(df, max_linhas=400):
    """
    Divide o DataFrame em lotes baseados em Conta + SubPlano Prev,
    garantindo que cada lote tenha no máximo `max_linhas` registros.
    """
    if "Conta" not in df.columns or "SubPlano Prev" not in df.columns:
        raise ValueError("As colunas 'Conta' e 'SubPlano Prev' são obrigatórias para o chunking.")

    df = df.sort_values(by=["Conta", "SubPlano Prev"]).copy()
    grupos = list(df.groupby(["Conta", "SubPlano Prev"]))

    lotes = []
    lote_atual = []
    linhas_atual = 0

    for chave, grupo in grupos:
        tamanho = len(grupo)

        if linhas_atual + tamanho > max_linhas and lote_atual:
            lotes.append(pd.concat(lote_atual))
            lote_atual = [grupo]
            linhas_atual = tamanho
        else:
            lote_atual.append(grupo)
            linhas_atual += tamanho

    if lote_atual:
        lotes.append(pd.concat(lote_atual))

    return lotes


def processar_conciliacao(df: pd.DataFrame) -> dict:
    """
    Envia um lote (DataFrame) para a OpenAI e retorna o JSON estruturado.
    """
    prompt_base = carregar_prompt()
    conteudo_excel = df.to_csv(index=False)

    prompt_final = f"""
{prompt_base}

---
📄 Abaixo está o conteúdo da planilha enviada.

⚠️ IMPORTANTE: Retorne a resposta **apenas em JSON válido**, sem explicações adicionais.

{conteudo_excel}
"""

    salvar_log("prompt_enviado", prompt_final)

    try:
        resposta = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é o ELOS, especialista em conciliação bancária. Sempre responda exclusivamente em JSON estruturado."},
                {"role": "user", "content": prompt_final}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        salvar_log("resposta_bruta", resposta.dict(), extensao="json")
        conteudo_json = resposta.choices[0].message.content
        return json.loads(conteudo_json)

    except Exception as e:
        return {"erro": f"Falha ao processar conciliação: {str(e)}"}


def processar_em_chunks(df, nome_arquivo):
    """
    Divide a planilha em lotes de até 400 linhas, processa cada um via OpenAI
    e vai salvando incrementalmente no Excel.
    """
    lotes = dividir_em_lotes(df, max_linhas=50)
    resultado_final = {"dados": [], "resumo": [], "nao_conciliados": []}

    for i, lote in enumerate(lotes, start=1):
        print(f"🔄 Processando lote {i}/{len(lotes)} com {len(lote)} linhas...")
        resposta = processar_conciliacao(lote)

        if "erro" in resposta:
            print(f"❌ Erro no lote {i}: {resposta['erro']}")
            continue

        resultado_final["dados"].extend(resposta.get("dados", []))
        resultado_final["resumo"].extend(resposta.get("resumo", []))
        resultado_final["nao_conciliados"].extend(resposta.get("nao_conciliados", []))

        # Salva progresso no Excel a cada lote
        salvar_excel(resultado_final, nome_arquivo)

    return resultado_final
