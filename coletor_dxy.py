import requests
from bs4 import BeautifulSoup
import time
import datetime
import statistics
import csv
import os
import re

from logger import log

URL = "https://br.investing.com/currencies/us-dollar-index"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-BR,pt;q=0.9"
}

CSV_FILE = "dados/dxy_historico.csv"


def limpar_valor(texto):

    texto = texto.strip()

    texto = texto.replace("−", "-")

    negativo = "-" in texto

    numero = re.search(r"\d+[.,]\d+", texto)

    if not numero:
        raise ValueError(f"Não foi possível extrair número de: {texto}")

    valor = numero.group(0)

    valor = valor.replace(",", ".")

    valor = float(valor)

    if negativo:
        valor = -valor

    return valor


def validar_valor(valor):

    if valor > 5 or valor < -5:
        raise ValueError(f"Valor fora do range esperado: {valor}")

    return True


def coletar_valor():

    import requests
    from bs4 import BeautifulSoup

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

            print("Investing bloqueou (HTTP {})".format(r.status_code))

    except Exception as e:

        print("Falha Investing:", e)

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

def esperar_segundo_zero():

    log("Sincronizando com o segundo 00")

    while True:

        agora = datetime.datetime.now()

        if agora.second == 0:
            break

        time.sleep(0.2)


def coletar_minuto():

    valores = []

    esperar_segundo_zero()

    log("Inicio da coleta sincronizada 08:40")

    for i in range(12):

        inicio = time.time()

        try:

            valor = coletar_valor()

            valores.append(valor)

            log(f"Coleta {i+1}/12: {valor}")

        except Exception as e:

            log(f"Erro na coleta {i+1}: {e}")

        tempo_execucao = time.time() - inicio

        tempo_espera = 5 - tempo_execucao

        if tempo_espera > 0:
            time.sleep(tempo_espera)

    if len(valores) == 0:

        log("Nenhum valor coletado")

        return

    media = round(statistics.mean(valores), 4)

    if abs(media) > 5:

        log("ALERTA: média fora do esperado — coleta ignorada")

        return

    hoje = datetime.datetime.now().strftime("%Y-%m-%d")

    linha = [hoje, "08:40:00", media]

    os.makedirs("dados", exist_ok=True)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow(linha)

    log(f"Média do minuto: {media}")


if __name__ == "__main__":
    coletar_minuto()
