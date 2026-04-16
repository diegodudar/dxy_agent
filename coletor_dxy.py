import requests
import datetime
import time
import statistics
import csv
import os
import sys


CSV_FILE = "dados/dxy_historico.csv"
LOG_FILE = "dados/log_coletor.txt"


TOKEN = "8635476074:AAHnoyXQ-_5592nadGYS-GCe4jmrw1cYrhM"
CHAT_ID = "-1003902562678"


# ===============================
# LOG
# ===============================

def log(msg):

    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    linha = f"[{agora}] {msg}"

    print(linha)

    os.makedirs("dados", exist_ok=True)

    with open(LOG_FILE, "a", encoding="utf-8") as f:

        f.write(linha + "\n")


# ===============================
# CLASSIFICA REGIME DXY
# ===============================

def classificar_regime(valor):

    if valor > 0.30:
        return "USD FORTE 🔴"

    elif valor < -0.30:
        return "USD FRACO 🟢"

    return "USD NEUTRO 🟡"


# ===============================
# VIÉS WDO
# ===============================

def interpretar_wdo(valor):

    if valor > 0.30:
        return "VIÉS WDO: BAIXA 📉"

    elif valor < -0.30:
        return "VIÉS WDO: ALTA 📈"

    return "VIÉS WDO: NEUTRO ⚖️"


# ===============================
# DETECTA INSTABILIDADE
# ===============================

def detectar_instabilidade(minimo, maximo):

    if abs(maximo - minimo) > 0.10:

        return "⚠️ Snapshot instável (alta dispersão intraminuto)"

    return ""


# ===============================
# ENVIO TELEGRAM
# ===============================

def enviar_telegram(media, minimo, maximo, desvio):

    agora = datetime.datetime.now().strftime("%H:%M:%S")

    regime = classificar_regime(media)

    vies = interpretar_wdo(media)

    alerta = detectar_instabilidade(minimo, maximo)

    mensagem = (
        f"📊 DXY {agora}\n"
        f"Valor médio: {media}%\n"
        f"Mín: {minimo}%\n"
        f"Máx: {maximo}%\n"
        f"Desvio: {desvio}\n"
        f"{regime}\n"
        f"{vies}"
    )

    if alerta:

        mensagem += f"\n{alerta}"

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {

        "chat_id": CHAT_ID,
        "text": mensagem

    }

    try:

        resposta = requests.post(url, data=payload, timeout=10)

        if resposta.status_code != 200:

            log(f"Erro Telegram HTTP {resposta.status_code}")

            log(resposta.text)

            return

        if not resposta.json().get("ok"):

            log("Erro Telegram API")

            log(resposta.json())

            return

        log("Mensagem Telegram enviada com sucesso")

    except Exception as e:

        log(f"Erro Telegram conexão: {e}")


# ===============================
# COLETA DXY
# ===============================

def coletar_valor():

    url = "https://br.investing.com/currencies/us-dollar-index"

    headers = {

        "User-Agent": "Mozilla/5.0",

        "Accept-Language": "pt-BR,pt;q=0.9"

    }

    r = requests.get(url, headers=headers, timeout=10)

    if r.status_code != 200:

        raise Exception("Erro acesso Investing")

    html = r.text

    marcador = "instrument-price-change-percent"

    pos = html.find(marcador)

    if pos == -1:

        raise Exception("Campo DXY não encontrado")

    trecho = html[pos:pos + 200]

    ini = trecho.find("(")

    fim = trecho.find("%")

    texto = trecho[ini + 1:fim]

    valor = float(

        texto.replace(",", ".")

        .replace("+", "")

        .replace("−", "-")

    )

    log(f"TEXTO BRUTO CAPTURADO: ({valor}%)")

    return valor


# ===============================
# ESPERA 08:40:01
# ===============================

def esperar_0840():

    log("Modo automático ativado")

    while True:

        agora = datetime.datetime.now()

        alvo = agora.replace(

            hour=8,

            minute=40,

            second=1,

            microsecond=0

        )

        if agora >= alvo:

            break

        restante = int((alvo - agora).total_seconds())

        log(f"Aguardando 08:40:01 ({restante}s)")

        time.sleep(min(restante, 5))


# ===============================
# COLETA 1 MINUTO
# ===============================

def coletar_minuto():

    valores = []

    log("Início da coleta do minuto atual")

    for i in range(12):

        inicio = time.time()

        try:

            valor = coletar_valor()

            valores.append(valor)

            log(f"Coleta {i+1}/12: {valor}")

        except Exception as e:

            log(f"Erro coleta: {e}")

        tempo_execucao = time.time() - inicio

        if tempo_execucao < 5:

            time.sleep(5 - tempo_execucao)

    if len(valores) < 3:

        raise Exception("Nenhum valor coletado")

    media = round(statistics.mean(valores), 4)

    minimo = round(min(valores), 4)

    maximo = round(max(valores), 4)

    desvio = round(statistics.pstdev(valores), 4)

    agora = datetime.datetime.now()

    linha = [

        agora.strftime("%Y-%m-%d"),

        agora.strftime("%H:%M:%S"),

        media,

        minimo,

        maximo,

        desvio

    ]

    os.makedirs("dados", exist_ok=True)

    arquivo_existe = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        if not arquivo_existe:

            writer.writerow(

                ["data", "hora", "dxy_mean", "dxy_min", "dxy_max", "dxy_std"]

            )

        writer.writerow(linha)

    log(f"Média do minuto: {media}")

    enviar_telegram(media, minimo, maximo, desvio)

    log("Processo finalizado")


# ===============================
# EXECUÇÃO
# ===============================

if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1].lower() == "auto":

        esperar_0840()

    else:

        log("Modo manual ativado")

    coletar_minuto()
