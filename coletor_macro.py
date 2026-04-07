import requests
from bs4 import BeautifulSoup
import time
import datetime
import csv
import os
import re
import statistics

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-BR,pt;q=0.9"
}

CSV_FILE = "dados/macro_0840.csv"


INDICADORES = {
    "dxy": "https://br.investing.com/currencies/us-dollar-index",
    "vix": "https://br.investing.com/indices/volatility-s-p-500",
    "us10y": "https://br.investing.com/rates-bonds/u.s.-10-year-bond-yield",
    "nasdaq": "https://br.investing.com/indices/nq-100-futures"
}


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


def coletar_percentual(url):

    r = requests.get(url, headers=HEADERS, timeout=10)

    soup = BeautifulSoup(r.text, "html.parser")

    percent = soup.select_one('[data-test="instrument-price-change-percent"]')

    if percent is None:
        raise Exception("Mudança no HTML detectada")

    return limpar_valor(percent.text)


def coletar_valor_absoluto(url):

    r = requests.get(url, headers=HEADERS, timeout=10)

    soup = BeautifulSoup(r.text, "html.parser")

    valor = soup.select_one('[data-test="instrument-price-last"]')

    if valor is None:
        raise Exception("Mudança no HTML detectada")

    return limpar_valor(valor.text)


def coletar_dxy():

    valores = []

    for _ in range(12):

        inicio = time.time()

        try:
            valor = coletar_percentual(INDICADORES["dxy"])
            valores.append(valor)

            print("DXY:", valor)

        except Exception as e:
            print("Erro DXY:", e)

        tempo = time.time() - inicio

        if tempo < 5:
            time.sleep(5 - tempo)

    if not valores:
        raise Exception("Falha total na coleta DXY")

    return {
        "mean": round(statistics.mean(valores), 4),
        "min": round(min(valores), 4),
        "max": round(max(valores), 4),
        "std": round(statistics.pstdev(valores), 4)
    }


def ja_coletado_hoje():

    if not os.path.exists(CSV_FILE):
        return False

    hoje = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    with open(CSV_FILE, encoding="utf-8") as f:
        return hoje in f.read()


def salvar_csv(dados):

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

        writer.writerow(dados)


def main():

    if ja_coletado_hoje():
        print("Coleta já realizada hoje")
        return

    hoje = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    print("Coletando DXY minuto 08:40")

    dxy = coletar_dxy()

    print("Coletando VIX")
    vix = coletar_percentual(INDICADORES["vix"])

    print("Coletando US10Y")
    us10y = coletar_valor_absoluto(INDICADORES["us10y"])

    print("Coletando Nasdaq Futures")
    nasdaq = coletar_valor_absoluto(INDICADORES["nasdaq"])

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


if __name__ == "__main__":
    main()
