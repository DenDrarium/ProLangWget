import http.client
import os
import sys
import threading
import time
import urllib.parse

# Глобальные переменные для отслеживания состояния загрузки
downloaded_bytes = 0
download_complete = False
download_failed = False
lock = threading.Lock()  # Блокировка для синхронизации потоков

def is_valid_url(url):
    try:
        parsed = urllib.parse.urlparse(url)
        return all([parsed.scheme in ["http", "https"], parsed.hostname])
    except Exception:
        return False

def download_file(url, filename):
    
    global downloaded_bytes, download_complete, download_failed

    # Парсинг URL
    parsed_url = urllib.parse.urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
    path = parsed_url.path or "/"

    # Установка соединения
    connection = (
        http.client.HTTPSConnection(host, port)
        if parsed_url.scheme == "https"
        else http.client.HTTPConnection(host, port)
    )
    connection.request("GET", path)
    response = connection.getresponse()

    if response.status != 200:
        print(f"Ошибка загрузки: {response.status} {response.reason}")
        download_complete = True
        download_failed = True
        return

    # Загрузка файла с обновлением количества загруженных данных
    with open(filename, "wb") as file:
        while chunk := response.read(1024):
            file.write(chunk)
            with lock:
                downloaded_bytes += len(chunk)

    # Уведомление о завершении загрузки
    with lock:
        download_complete = True

def monitor_progress():
    
    global downloaded_bytes, download_complete, download_failed

    while True:
        with lock:
            if download_complete:
                break
            print(f"Скачано: {downloaded_bytes} байт")
        time.sleep(1)

    # Финальный вывод
    with lock:
        if download_failed:
            print("Загрузка завершена с ошибкой.")
        else:
            print(f"Загрузка завершена. Всего скачано: {downloaded_bytes} байт")

def main():

    if len(sys.argv) != 2:
        print("Использование: python wget.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    
    # Проверка, что аргумент является ссылкой
    if not is_valid_url(url):
        print("Ошибка: введенный аргумент не является корректным URL.")
        sys.exit(1)

    # Получение URL и имени файла  
    parsed_url = urllib.parse.urlparse(url)
    filename = os.path.basename(parsed_url.path) or (parsed_url.hostname)

    # Создание и запуск потоков
    download_thread = threading.Thread(target=download_file, args=(url, filename))
    monitor_thread = threading.Thread(target=monitor_progress)

    download_thread.start()
    monitor_thread.start()

    # Ожидание завершения потоков
    download_thread.join()
    monitor_thread.join()

if __name__ == "__main__":
    main()
