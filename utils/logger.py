import logging
import sys

class Logger:
    def __init__(self, name: str = "trading-bot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # capture everything

        # prevent duplicate handlers
        if not self.logger.handlers:
            # STDOUT handler (INFO)
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setLevel(logging.INFO)
            stdout_fmt = logging.Formatter("[%(levelname)s] %(message)s")
            stdout_handler.setFormatter(stdout_fmt)

            # STDERR handler (WARNING)
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(logging.WARNING)
            stderr_fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
            stderr_handler.setFormatter(stderr_fmt)

            # File handler (DEBUG)
            file_handler = logging.FileHandler("trading_bot.log")
            file_handler.setLevel(logging.DEBUG)
            file_fmt = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
            file_handler.setFormatter(file_fmt)

            self.logger.addHandler(stdout_handler)
            self.logger.addHandler(stderr_handler)
            self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger