import logging
from logging.handlers import RotatingFileHandler
import json
import os
from datetime import datetime, timezone
import uuid

try:
    from google.cloud import firestore
except ImportError:
    firestore = None

class DentalRobotLogger:
    """
    Structured logger for dental automation pipelines.
    Writes logs to Firestore (per clinic) or local rotating file, depending on environment.
    """

    def __init__(
        self,
        client_uid,
        clinic_uid,
        pipeline,
        execution_id=None,
        logs_dir="./dr_logs",
        max_bytes=5 * 1024 * 1024,
        backup_count=5,
        log_to_console=True
    ):
        """
        Initialize the logger.
        :param client_uid: UID of the client (str, required)
        :param clinic_uid: UID of the clinic (str, required)
        :param pipeline: Pipeline name ("install", "extraction", "writeback", etc.)
        :param execution_id: Optional execution ID (str)
        :param logs_dir: Directory for local logs (default: ./dr_logs)
        :param max_bytes: Max size in bytes for each log file before rotating (default: 5MB)
        :param backup_count: Number of rotated log files to keep
        :param log_to_console: Whether to log to console as well
        """
        self.client_uid = client_uid
        self.clinic_uid = clinic_uid
        self.pipeline = pipeline
        self.execution_id = execution_id

        # Detect if Firestore logging is enabled
        self.use_firestore = bool(os.environ.get("USE_FIRESTORE_LOGGER", "0") == "1" and firestore is not None)
        self.firestore_client = None

        if self.use_firestore:
            try:
                self.firestore_client = firestore.Client()
                print("[DentalRobotLogger] Logging to Firestore.")
            except Exception as e:
                print(f"[DentalRobotLogger] Firestore init failed, fallback to local log. Reason: {e}")
                self.use_firestore = False

        if not self.use_firestore:
            # Local rotating file logger (by clinic and pipeline)
            os.makedirs(logs_dir, exist_ok=True)
            logger_name = f"{client_uid}.{clinic_uid}.{pipeline}.file"
            self.file_logger = logging.getLogger(logger_name)
            self.file_logger.setLevel(logging.DEBUG)
            self.file_logger.propagate = False

            file_log_path = os.path.join(logs_dir, f"{client_uid}_{clinic_uid}_{pipeline}.log")
            if not self.file_logger.handlers:
                file_handler = RotatingFileHandler(file_log_path, maxBytes=max_bytes, backupCount=backup_count)
                file_handler.setFormatter(logging.Formatter('%(message)s'))
                self.file_logger.addHandler(file_handler)

        # Console logger (optional)
        self.console_logger = None
        if log_to_console:
            self.console_logger = logging.getLogger(f"{client_uid}.{clinic_uid}.{pipeline}.console")
            self.console_logger.setLevel(logging.DEBUG)
            self.console_logger.propagate = False
            if not self.console_logger.handlers:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
                self.console_logger.addHandler(console_handler)

    def _log(self, level, message, save_log, extra_context=None):
        """
        Internal logging method. Depending on environment, logs to local file or Firestore.
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        log_id = str(uuid.uuid4())
        log_entry = {
            "log_id": log_id,
            "client_uid": self.client_uid,
            "clinic_uid": self.clinic_uid,
            "pipeline": self.pipeline,
            "execution_id": self.execution_id,
            "level": level,
            "timestamp": now_utc,
            "message": message,
            "extra_context": extra_context or {}
        }

        json_message = json.dumps(log_entry, ensure_ascii=False)

        # Save log according to environment
        if save_log:
            if self.use_firestore:
                try:
                    doc_ref = (
                        self.firestore_client.collection("clients")
                        .document(self.client_uid)
                        .collection("clinics")
                        .document(self.clinic_uid)
                        .collection("logs")
                        .document(log_id)
                    )
                    doc_ref.set(log_entry)
                except Exception as e:
                    fallback_msg = f"[DentalRobotLogger] ERROR logging to Firestore: {e}. Log: {json_message}"
                    print(fallback_msg)
                    self._log_local(level, json_message)
            else:
                self._log_local(level, json_message)

        # Always log to console if enabled
        if self.console_logger:
            self.console_logger.log(getattr(logging, level), message)

    def _log_local(self, level, json_message):
        """
        Local log file fallback.
        """
        if hasattr(self, "file_logger"):
            self.file_logger.log(getattr(logging, level), json_message)
        else:
            print(f"[DentalRobotLogger] [FALLBACK LOCAL LOG] {json_message}")

    def info(self, message, save_log=False, extra_context=None):
        self._log("INFO", message, save_log, extra_context)

    def debug(self, message, save_log=False, extra_context=None):
        self._log("DEBUG", message, save_log, extra_context)

    def warning(self, message, save_log=False, extra_context=None):
        self._log("WARNING", message, save_log, extra_context)

    def error(self, message, save_log=False, extra_context=None):
        self._log("ERROR", message, save_log, extra_context)

    def critical(self, message, save_log=False, extra_context=None):
        self._log("CRITICAL", message, save_log, extra_context)
