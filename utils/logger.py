import datetime

def log(message, level):
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if level > 4 | level < 0:
        return

    with open("server.log", "a") as log_file:
        log_file.write(f"[{levels[level]}][{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] - {message} \n")
