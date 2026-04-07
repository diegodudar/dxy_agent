import datetime
import time

from coletor_dxy import coletar_minuto
from logger import log


def esperar_ate_0840():

    while True:

        agora = datetime.datetime.now()

        alvo = agora.replace(hour=8, minute=40, second=0, microsecond=0)

        if agora >= alvo:
            break

        segundos = int((alvo - agora).total_seconds())

        log(f"Aguardando 08:40 ({segundos}s)")

        time.sleep(15)


def main():

    log("Scheduler iniciado")

    esperar_ate_0840()

    coletar_minuto()

    log("Processo finalizado")


if __name__ == "__main__":
    main()