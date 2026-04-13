import requests
import datetime
import time
import statistics
import csv
import os
import random
import string


CSV_FILE = "dados/dxy_historico.csv"


# ===============================
# GERAR SESSION TOKEN TVC
# ===============================

def gerar_session():

    letters = string.ascii_lowercase
    return "qs_" + "".join(random.choice(letters) for _ in range(12))


# ===============================
# COLETA DXY REAL DO INVESTING
# ===============================

def coletar_valor():

    session = gerar_session()

    url = "https://tvc4.forexpros.com/"

    payload = (
        f'{{"m":"quote_add_symbols","p":["{session}","indices:USDOLLAR"]}}'
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "text/plain"
    }

    r = requests.post(url, data=payload, headers=headers, timeout=10)

    if r.status_code != 200:
        raise Exception("Erro acesso Investing TVC session")

    texto = r.text

    if '"chp":' not in texto:
        raise Exception("Percentual DXY não encontrado")

    valor = texto.split('"chp":')[1].split(",")[0]

    return round(float(valor), 4)


# ===============================
# SINCRONIZAÇÃO LOCAL 08:40
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
# COLETA INTRAMINUTO
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


if __name__ == "__main__":
    coletar_minuto()
