import argparse

import watchdog.events
import watchdog.observers
import time
from helper_functions import parse_pou_file, change_pou_description


class EditTimeAnalysisWatchDog(watchdog.events.PatternMatchingEventHandler):
    def __init__(self):
        watchdog.events.PatternMatchingEventHandler.__init__(self, patterns=['*.pou'],
                                                             ignore_directories=True, case_sensitive=False)

    def on_modified(self, event):
        program = parse_pou_file(event.src_path)
        print(program.report_as_text())



def getWatchDogHandler(source_path):
    event_handler = EditTimeAnalysisWatchDog()
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, path=source_path, recursive=True)
    observer.start()
    return observer

argParser = argparse.ArgumentParser()
argParser.add_argument("--base-path", action="store", required=True)

def main():
    args = argParser.parse_args()
    observer = getWatchDogHandler(args.base_path)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
