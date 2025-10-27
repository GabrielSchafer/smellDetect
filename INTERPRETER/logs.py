from datetime import datetime
import json


class Logger:
    def __init__(self):
        self.logs = []

    def _log(self, level, message):
        self.logs.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "level": level.upper(),
            "message": message
        })

    def info(self, message):
        self._log("INFO", message)

    def warning(self, message):
        self._log("WARNING", message)

    def error(self, message):
        self._log("ERROR", message)

    def success(self, message):
        self._log("SUCCESS", message)

    def get_logs(self):
        return self.logs
