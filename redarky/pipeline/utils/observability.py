import socket
from datetime import UTC, datetime

from pipeline.utils.logger import log


def log_runtime_environment() -> None:

    log.info(
        "runtime.environment",
        hostname=socket.gethostname(),
        timestamp=datetime.now(UTC).isoformat(),
    )