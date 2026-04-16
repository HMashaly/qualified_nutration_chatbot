from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class Watcher:
    def __init__(self, directory_to_watch):
        self.directory_to_watch = directory_to_watch
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

class Handler(FileSystemEventHandler):
    @staticmethod
    def on_modified(event):
        if event.is_directory:
            return
        print(f"File modified: {event.src_path}")

    @staticmethod
    def on_created(event):
        print(f"File created: {event.src_path}")

    @staticmethod
    def on_deleted(event):
        print(f"File deleted: {event.src_path}")

if __name__ == "__main__":
    path = "/Users/h/Turing/RAG/qualified_nutration"  # Replace with your directory
    watcher = Watcher(path)
    watcher.run()