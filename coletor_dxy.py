import requests
from bs4 import BeautifulSoup
import datetime
import time
import statistics
import csv
import os
import re

CSV_FILE = "dados/dxy_historico.csv"


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


def coletar_valor():

    url_investing = "https://br.investing.com/currencies/us-dollar-index"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    try:

        r = requests.get(url_investing, headers=headers, timeout=15)

        if r.status_code == 200:

            soup = BeautifulSoup(r.text, "html.parser")

            seletores = [
                '[data-test="instrument-price-change-percent"]',
                '[class*="priceChangePercent"]',
                '[class*="change-percent"]'
            ]

            for seletor in seletores:

                campo = soup.select_one(seletor)

                if campo:

                    texto = campo.text.strip()

                    return limpar_valor(texto)

        else:

            print(f"Investing bloqueou (HTTP {r.status_code})")

    except Exception as e:

        print("Erro Investing:", e)

    print("Fallback → Yahoo Finance")

    url_yahoo = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1m&range=15m"

    r = requests.get(url_yahoo, timeout=10)

    data = r.json()

    closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]

    closes = [v for v in closes if v is not None]

    primeiro = closes[0]
    ultimo = closes[-1]

    variacao_pct = ((ultimo - primeiro) / primeiro) * 100

    return round(variacao_pct, 4)


def coletar_minuto():

    valores = []

    print("Iniciando coleta do minuto 08:40")

    for i in range(12):

        inicio = time.time()

        try:

            valor = coletar_valor()

            valores.append(valor)

            print(f"Coleta {i+1}/12:", valor)

        except Exception as e:

            print("Erro coleta:", e)

        tempo_execucao = time.time() - inicio

        if tempo_execucao < 5:
            time.sleep(5 - tempo_execucao)

    if not valores:

        raise Exception("Nenhum valor coletado")

    media = round(statistics.mean(valores), 4)
    minimo = round(min(valores), 4)
    maximo = round(max(valores), 4)
    desvio = round(statistics.pstdev(valores), 4)

    hoje = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    linha = [hoje, "08:40:00", media, minimo, maximo, desvio]

    os.makedirs("dados", exist_ok=True)

    arquivo_existe = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        if not arquivo_existe:

            writer.writerow(
                ["data", "hora", "dxy_mean", "dxy_min", "dxy_max", "dxy_std"]
            )

        writer.writerow(linha)

    print("Registro salvo:", linha)


if __name__ == "__main__":
    coletar_minuto()
