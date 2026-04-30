import logging
import json
import sys
from datetime import datetime
import contextvars

from .config import settings

request_id_var = contextvars.ContextVar("request_id", default=None)

class JSONFormatter(logging.Formatter):
    """Custom formatter to output structured JSON logs."""
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": settings.APP_NAME,
            "message": record.getMessage(),
        }
        
        # Inject Request ID if it exists in the current context
        req_id = request_id_var.get()
        if req_id:
            log_record["request_id"] = req_id
            
        # Include exception details if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logging():
    """Configures the root logger to output JSON to stdout."""
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)
    
    # Clear any existing default handlers (prevents duplicate or plain-text logs)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    # Add stdout stream handler for Docker compatibility
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

def get_logger(name: str):
    """Get a configured logger instance."""
    return logging.getLogger(name)
