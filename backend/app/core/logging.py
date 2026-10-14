import logging
import sys


def configure_logging(env: str = "dev") -> None:
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.INFO if env == "prod" else logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Never log secrets; reduce noise
    for noisy_logger in ("uvicorn.access", "httpx"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
