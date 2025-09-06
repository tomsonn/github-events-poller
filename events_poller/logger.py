import logging
import structlog.stdlib


logging.basicConfig(level=logging.INFO)

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.stdlib.get_logger("events-poller")
