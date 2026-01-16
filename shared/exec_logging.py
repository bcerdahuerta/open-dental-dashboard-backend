"""
ExecutionLogger

Centralized logger for pipeline steps. Handles structured logging for execution
to Firestore or any other storage. Recommended for audit trail, reporting, and debugging.
"""

from datetime import datetime
from typing import Any, Optional

class ExecutionLogger:
    def __init__(self, client: str, clinic: str, firestore_client: Any):
        """
        :param client: Name of the client/clinic
        :param clinic: Clinic identifier
        :param firestore_client: Instance of Firestore (or None for dev)
        """
        self.client = client
        self.clinic = clinic
        self.firestore = firestore_client

    def log_execution(
        self,
        context: dict,
        step: str,
        field: Optional[str] = None,
        old: Optional[Any] = None,
        new: Optional[Any] = None,
        status: Optional[str] = None,
        details: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """
        Log a single step, change, skip, or error in the pipeline.

        :param context: Execution context (should include execution_id, sheet_row, patnum, etc)
        :param step: Name of the step (e.g., 'update_benefits')
        :param field: Field name if relevant
        :param old: Previous value (OD)
        :param new: New value (form)
        :param status: 'updated', 'skipped', 'error', 'done', etc.
        :param details: Additional info (rule applied, reason, etc)
        :param error: Error message if any
        """
        log_doc = {
            "execution_id": context.get("execution_id"),
            "client": self.client,
            "clinic": self.clinic,
            "sheet_row": context.get("sheet_row"),
            "patnum": context.get("patnum"),
            "step": step,
            "field": field,
            "old_value": old,
            "new_value": new,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }
        # Store in Firestore or print for debugging
        if self.firestore:
            self.firestore.collection("executions").add(log_doc)
        else:
            print("EXECUTION LOG:", log_doc)

    def start_execution(self) -> str:
        """
        Start a new execution batch and return a unique execution_id.
        """
        execution_id = f"exec_{datetime.utcnow().isoformat()}"
        # Optionally, write a batch summary to Firestore
        return execution_id

    def get_batch_date(self):
        """
        Returns the current batch date (date part only).
        """
        return datetime.utcnow().date()
