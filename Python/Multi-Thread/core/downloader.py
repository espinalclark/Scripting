# core/downloader.py
import os
import threading
import requests
from queue import Queue, Empty
from time import sleep

CHUNK = 8192

class SegmentWorker(threading.Thread):
    def __init__(self, url, start, end, part_path, progress_queue, headers=None, timeout=30):
        super().__init__(daemon=True)
        self.url = url
        self.start = start
        self.end = end
        self.part_path = part_path
        self.progress_queue = progress_queue
        self.headers = headers or {}
        self.timeout = timeout
        self._stop_event = threading.Event()

    def run(self):
        h = self.headers.copy()
        h['Range'] = f'bytes={self.start}-{self.end}'
        try:
            with requests.get(self.url, headers=h, stream=True, timeout=self.timeout) as r:
                r.raise_for_status()
                with open(self.part_path, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(CHUNK):
                        if self._stop_event.is_set():
                            return
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            # notify GUI: (part_path, downloaded)
                            self.progress_queue.put(('progress', self.part_path, downloaded))
        except Exception as e:
            self.progress_queue.put(('error', self.part_path, str(e)))

    def stop(self):
        self._stop_event.set()

class SegmentedDownloader:
    def __init__(self, url, dest_path, parts=4, progress_queue=None, headers=None):
        self.url = url
        self.dest_path = dest_path
        self.parts = max(1, parts)
        self.progress_queue = progress_queue or Queue()
        self.headers = headers or {}
        self.workers = []
        self.part_files = []
        self.total_size = None
        self._stop = False

    def _get_size(self):
        r = requests.head(self.url, allow_redirects=True, timeout=10)
        r.raise_for_status()
        size = r.headers.get('Content-Length')
        accept_ranges = r.headers.get('Accept-Ranges', 'none')
        return int(size) if size else None, accept_ranges != 'none'

    def start(self):
        size, supports_range = self._get_size()
        self.total_size = size
        if size is None or not supports_range or self.parts == 1:
            # fallback single-threaded
            self._single_thread()
            return

        part_size = size // self.parts
        for i in range(self.parts):
            start = i * part_size
            end = (start + part_size - 1) if i < self.parts - 1 else size - 1
            part_path = f"{self.dest_path}.part{i}"
            self.part_files.append(part_path)
            w = SegmentWorker(self.url, start, end, part_path, self.progress_queue, headers=self.headers)
            self.workers.append(w)
            w.start()

        # monitor in a separate thread
        monitor = threading.Thread(target=self._monitor, daemon=True)
        monitor.start()

    def _single_thread(self):
        try:
            with requests.get(self.url, stream=True, headers=self.headers) as r:
                r.raise_for_status()
                with open(self.dest_path, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(CHUNK):
                        if self._stop: break
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            self.progress_queue.put(('progress', self.dest_path, downloaded))
            self.progress_queue.put(('done', self.dest_path, None))
        except Exception as e:
            self.progress_queue.put(('error', self.dest_path, str(e)))

    def _monitor(self):
        # simple monitor: waits for workers to finish, then merge
        for w in self.workers:
            w.join()
        if self._stop:
            self.progress_queue.put(('stopped', self.dest_path, None))
            return

        # merge
        with open(self.dest_path, 'wb') as out:
            for part in self.part_files:
                with open(part, 'rb') as pf:
                    while True:
                        chunk = pf.read(CHUNK)
                        if not chunk: break
                        out.write(chunk)
                os.remove(part)
        self.progress_queue.put(('done', self.dest_path, None))

    def stop(self):
        self._stop = True
        for w in self.workers:
            w.stop()

