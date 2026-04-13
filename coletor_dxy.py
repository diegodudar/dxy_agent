import requests
import datetime
import time
import statistics
import csv
import os


CSV_FILE = "dados/dxy_historico.csv"


# ===============================
# SINCRONIZAÇÃO 08:40:00 (LOCAL)
# ===============================

def esperar_inicio_0840():

    if os.getenv("GITHUB_ACTIONS") == "true":
        print("Execução no GitHub Actions detectada → pulando sincronização")
        return

    print("Sincronizando com o segundo 00 de 08:40")

    while True:

        agora = datetime.datetime.utcnow()
        hora_brasil = agora - datetime.timedelta(hours=3)

        if (
            hora_brasil.hour == 8
            and hora_brasil.minute == 40
            and hora_brasil.second == 0
        ):
            print("Início da coleta sincronizada 08:40:00")
            return

        time.sleep(0.25)


# ===============================
# COLETA DXY VIA INVESTING (TVC)
# ===============================

def coletar_valor():

    url = (
        "https://tvc4.forexpros.com/"
        "1f7d9e2b0e0f4a6b9e0a9d8f5a4b3c2d/"
        "1700000000/1/1/8/symbols?symbol=indices:USDOLLAR"
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    r = requests.get(url, headers=headers, timeout=10)

    if r.status_code != 200:
        raise Exception(f"Erro Investing TVC HTTP {r.status_code}")

    data = r.json()

    if not data or "chp" not in data[0]:
        raise Exception("Campo changePercent não encontrado")

    return round(data[0]["chp"], 4)


# ===============================
# COLETA INTRAMINUTO 08:40
# ===============================

def coletar_minuto():

    esperar_inicio_0840()

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

    if len(valores) < 3:
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


# ===============================
# EXECUÇÃO
# ===============================

if __name__ == "__main__":
    coletar_minuto()
