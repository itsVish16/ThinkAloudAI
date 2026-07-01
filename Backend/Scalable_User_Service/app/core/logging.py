import logging
import sys

import structlog


def datadog_trace_injection(logger, log_method, event_dict):
    try:
        import ddtrace

        span = ddtrace.tracer.current_span()
        if span:
            event_dict["dd.trace_id"] = str(span.trace_id)
            event_dict["dd.span_id"] = str(span.span_id)
            event_dict["dd.env"] = ddtrace.config.env or ""
            event_dict["dd.service"] = ddtrace.config.service or ""
            event_dict["dd.version"] = ddtrace.config.version or ""
    except ImportError:
        pass
    return event_dict


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            datadog_trace_injection,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    return structlog.get_logger(name)
