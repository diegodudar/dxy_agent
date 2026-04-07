import datetime
import os

LOG_FILE = "dados/log.txt"

def log(msg):

    os.makedirs("dados", exist_ok=True)

    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    linha = f"[{agora}] {msg}"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linha + "\n")

    print(linha)