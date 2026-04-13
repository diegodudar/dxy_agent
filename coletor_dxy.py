import requests
import datetime
import time
import statistics
import csv
import os


CSV_FILE = "dados/dxy_historico.csv"


# ===============================
# SINCRONIZAÇÃO LOCAL 08:40:00
# ===============================

def esperar_inicio_0840():

    if os.getenv("GITHUB_ACTIONS") == "true":
        print("Execução no GitHub Actions detectada → pulando sincronização")
        return

    print("Sincronizando com 08:40:00")

    while True:

        agora = datetime.datetime.utcnow()
        hora_br = agora - datetime.timedelta(hours=3)

        if (
            hora_br.hour == 8
            and hora_br.minute == 40
            and hora_br.second == 0
        ):
            print("Coleta iniciada em 08:40:00")
            return

        time.sleep(0.25)


# ===============================
# COLETA DXY (FONTE PRIMÁRIA ICE)
# ===============================

def coletar_valor():

    url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=DX-Y.NYB"

    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=10)

    if r.status_code != 200:
        raise Exception("Erro acesso feed DXY")

    data = r.json()

    result = data["quoteResponse"]["result"]

    if not result:
        raise Exception("Feed DXY vazio")

    change_percent = result[0]["regularMarketChangePercent"]

    return round(change_percent, 4)


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
