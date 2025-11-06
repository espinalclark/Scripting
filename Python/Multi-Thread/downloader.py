# downloader.py
import requests, threading, os

class MultiThreadDownloader:
    def __init__(self, url, progreso_var=None, num_hilos=4):
        self.url = url
        self.progreso_var = progreso_var
        self.num_hilos = num_hilos
        os.makedirs("data", exist_ok=True)
        self.filename = os.path.join("data", os.path.basename(url))

    def start(self):
        response = requests.head(self.url)
        total = int(response.headers.get('content-length', 0))
        rango = total // self.num_hilos if total > 0 else 0
        threads = []
        open(self.filename, "wb").close()  # crea archivo vacío

        for i in range(self.num_hilos):
            inicio = i * rango
            fin = None if i == self.num_hilos - 1 else (inicio + rango - 1)
            hilo = threading.Thread(target=self.descargar, args=(inicio, fin, total))
            threads.append(hilo)
            hilo.start()

        for hilo in threads:
            hilo.join()
        return self.filename

    def descargar(self, inicio, fin, total):
        headers = {"Range": f"bytes={inicio}-{fin}" if fin else f"bytes={inicio}-"}
        r = requests.get(self.url, headers=headers, stream=True)
        with open(self.filename, "r+b") as f:
            f.seek(inicio)
            descargado = 0
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    descargado += len(chunk)
                    if self.progreso_var and total > 0:
                        progreso = (os.path.getsize(self.filename) / total) * 100
                        self.progreso_var.set(progreso)

