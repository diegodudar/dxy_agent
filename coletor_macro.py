import requests
from bs4 import BeautifulSoup
import time
import datetime
import csv
import os
import re
import statistics


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}


CSV_FILE = "dados/macro_0840.csv"


INDICADORES = {
    "dxy": "https://br.investing.com/currencies/us-dollar-index",
    "vix": "https://br.investing.com/indices/volatility-s-p-500",
    "us10y": "https://br.investing.com/rates-bonds/u.s.-10-year-bond-yield",
    "nasdaq": "https://br.investing.com/indices/nq-100-futures"
}


# ===============================
# Parsing robusto de números
# ===============================

def limpar_valor(texto):

    texto = texto.strip().replace("−", "-")

    negativo = "-" in texto

    numero = re.search(r"\d+[.,]?\d*", texto)

    if not numero:
        raise ValueError(f"Falha parsing: {texto}")

    valor = float(numero.group(0).replace(",", "."))

    if negativo:
        valor = -valor

    return valor


# ===============================
# Seletores resilientes
# ===============================

def extrair_percentual(soup):

    seletores = [
        '[data-test="instrument-price-change-percent"]',
        '.instrument-price_change-percent',
        '[class*="change-percent"]'
    ]

    for seletor in seletores:

        campo = soup.select_one(seletor)

        if campo:
            return limpar_valor(campo.text)

    raise Exception("Mudança no HTML detectada (percentual)")


def extrair_valor_absoluto(soup):

    seletores = [
        '[data-test="instrument-price-last"]',
        '.instrument-price_last__KQzyA',
        '[class*="price-last"]'
    ]

    for seletor in seletores:

        campo = soup.select_one(seletor)

        if campo:
            return limpar_valor(campo.text)

    raise Exception("Mudança no HTML detectada (valor absoluto)")


# ===============================
# Request resiliente
# ===============================

def baixar_pagina(url):

    for tentativa in range(3):

        try:

            r = requests.get(url, headers=HEADERS, timeout=15)

            if r.status_code == 200:
                return BeautifulSoup(r.text, "html.parser")

        except Exception:
            pass

        time.sleep(2)

    raise Exception(f"Falha download página: {url}")


# ===============================
# Coleta percentual genérica
# ===============================

def coletar_percentual(url):

    soup = baixar_pagina(url)

    return extrair_percentual(soup)


# ===============================
# Coleta valor absoluto genérica
# ===============================

def coletar_valor(url):

    soup = baixar_pagina(url)

    return extrair_valor_absoluto(soup)


# ===============================
# Coleta intraminuto DXY
# ===============================

def coletar_dxy():

    valores = []

    print("Coletando DXY (12 amostras)")

    for tentativa in range(12):

        inicio = time.time()

        try:

            valor = coletar_percentual(INDICADORES["dxy"])

            valores.append(valor)

            print(f"DXY {tentativa+1}/12:", valor)

        except Exception as e:

            print("Erro DXY:", e)

        tempo = time.time() - inicio

        if tempo < 5:
            time.sleep(5 - tempo)

    if len(valores) < 3:

        raise Exception("Falha total na coleta DXY")

    return {
        "mean": round(statistics.mean(valores), 4),
        "min": round(min(valores), 4),
        "max": round(max(valores), 4),
        "std": round(statistics.pstdev(valores), 4)
    }


# ===============================
# Evitar duplicidade diária
# ===============================

def ja_coletado_hoje():

    if not os.path.exists(CSV_FILE):
        return False

    hoje = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    with open(CSV_FILE, encoding="utf-8") as f:

        return hoje in f.read()


# ===============================
# Salvar CSV
# ===============================

def salvar_csv(linha):

    os.makedirs("dados", exist_ok=True)

    arquivo_existe = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        if not arquivo_existe:

            writer.writerow([
                "data",
                "hora",
                "dxy_mean",
                "dxy_min",
                "dxy_max",
                "dxy_std",
                "vix",
                "us10y",
                "nasdaq"
            ])

        writer.writerow(linha)


# ===============================
# Execução principal
# ===============================

def main():

    if ja_coletado_hoje():

        print("Coleta já realizada hoje")

        return

    hoje = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    print("Iniciando snapshot macro 08:40")

    dxy = coletar_dxy()

    print("Coletando VIX")
    vix = coletar_percentual(INDICADORES["vix"])

    print("Coletando US10Y")
    us10y = coletar_valor(INDICADORES["us10y"])

    print("Coletando Nasdaq Futures")
    nasdaq = coletar_valor(INDICADORES["nasdaq"])

    linha = [
        hoje,
        "08:40:00",
        dxy["mean"],
        dxy["min"],
        dxy["max"],
        dxy["std"],
        vix,
        us10y,
        nasdaq
    ]

    salvar_csv(linha)

    print("Registro salvo:", linha)


# ===============================
# Entry point
# ===============================

if __name__ == "__main__":
    main()
