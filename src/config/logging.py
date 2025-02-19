import logging
import logging.config
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time


def configure_logger(log_path, debug_mode=True):
    """Configures logging"""
    handlers = ['console'] # Always use console logging
    # if not debug_mode:
    #     handlers.append('file')
    handlers.append('file')

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,  # Prevents disabling third-party loggers

        # Define formatters
        'formatters': {
            'default': {
                'format': '%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },

        # Define handlers (console and rotating file)
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': 'ext://sys.stdout'  # Logs to console
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': log_path,
                'maxBytes': 1024,  # 1KB max size
                'backupCount': 3  # Keep last 3 log files
            }
        },

        # Define loggers
        'loggers': {
            'default': {
                'level': 'DEBUG',
                'handlers': handlers,
                'propagate': False
            }
        }
    })

    return logging.getLogger("default")  


def configure_sql_logger(sql_log_path):
    """Configures logging for SQLAlchemy queries."""

    sql_logger = logging.getLogger("sqlalchemy.engine")
    sql_logger.setLevel(logging.INFO)

    # Standard SQL log file
    sql_file_handler = logging.handlers.RotatingFileHandler(
        sql_log_path, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    sql_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
    sql_file_handler.setFormatter(sql_formatter)
    sql_logger.addHandler(sql_file_handler)

    # Separate log file for slow queries (execution time > 1s)
    slow_query_logger = logging.getLogger("sqlalchemy.slow_queries")
    slow_query_logger.setLevel(logging.WARNING)

    slow_query_handler = logging.FileHandler(sql_log_path)
    slow_query_handler.setFormatter(sql_formatter)
    slow_query_logger.addHandler(slow_query_handler)

    # Log SQL Query Execution Time
    @event.listens_for(Engine, "before_cursor_execute")
    def before_execute(conn, cursor, statement, parameters, context, executemany):
        """Logs query start time."""
        conn.info.setdefault("query_start_time", []).append(time.time())

    @event.listens_for(Engine, "after_cursor_execute")
    def after_execute(conn, cursor, statement, parameters, context, executemany):
        """Logs query execution time, and filters slow queries."""
        start_time = conn.info["query_start_time"].pop(-1)
        total_time = time.time() - start_time
        log_message = f"SQL Query: {statement} | Params: {parameters} | Execution Time: {total_time:.5f}s"

        sql_logger.info(log_message)

        # Log slow queries separately (if execution time > 1s)
        if total_time > 1:
            slow_query_logger.warning(log_message)

    return sql_logger