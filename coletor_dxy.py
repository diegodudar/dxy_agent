import requestsimport requests
import datetime
import time
import statistics
import csv
import os

CSV_FILE = "dados/dxy_historico.csv"


def obter_close_anterior():

    url = "https://stooq.com/q/d/l/?s=usdollar&i=d"

    r = requests.get(url, timeout=10)

    if r.status_code != 200:
        raise Exception("Erro acesso histórico Stooq")

    linhas = r.text.strip().split("\n")

    if len(linhas) < 3:
        raise Exception("Histórico insuficiente Stooq")

    ontem = linhas[-2].split(",")

    if len(ontem) < 5:
        raise Exception("Formato histórico inesperado")

    return float(ontem[4])


def obter_close_atual():

    url = "https://stooq.com/q/l/?s=usdollar&i=d"

    r = requests.get(url, timeout=10)

    if r.status_code != 200:
        raise Exception("Erro snapshot Stooq")

    linhas = r.text.strip().split("\n")

    if len(linhas) < 2:
        raise Exception("Snapshot vazio")

    hoje = linhas[1].split(",")

    # última coluna sempre é Close
    close_atual = hoje[-1]

    if close_atual == "" or close_atual == "N/D":
        raise Exception("Close atual indisponível")

    return float(close_atual)


def coletar_valor():

    close_anterior = obter_close_anterior()
    close_atual = obter_close_atual()

    variacao = ((close_atual - close_anterior) / close_anterior) * 100

    return round(variacao, 4)


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
