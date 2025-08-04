"""
Audit Manager - Specialized SQLite manager for audit logging and monitoring

Handles audit trail logging, security monitoring, and system event tracking
as part of the refactored SQLite metadata architecture.
"""

import json
from datetime import datetime
from typing import Any, Optional

from src.utils.logger import get_logger

from .base_manager import BaseSQLiteManager

logger = get_logger(__name__)


class AuditManager(BaseSQLiteManager):
    """Specialized manager for audit logging and system monitoring operations."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize audit manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default.
        """
        super().__init__(db_path)
        logger.info(f"Audit manager initialized: {self.db_path}")

    def log_action(
        self,
        action: str,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
    ) -> bool:
        """Log an audit event.

        Args:
            action: Action performed (e.g., 'CREATE', 'UPDATE', 'DELETE', 'ACCESS')
            resource_type: Type of resource affected (e.g., 'dataset', 'user', 'config')
            user_id: User who performed the action (optional)
            resource_id: ID of the affected resource (optional)
            details: Additional details as JSON (optional)
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)
            success: Whether the action was successful
            error_message: Error message if action failed (optional)
            execution_time_ms: Execution time in milliseconds (optional)

        Returns:
            True if logged successfully, False otherwise
        """
        try:
            # Validate required fields
            if not action or not resource_type:
                logger.error("Action and resource_type are required for audit logging")
                return False

            # Prepare details JSON
            details_json = json.dumps(details) if details else None

            # Insert audit log entry
            query = """
                INSERT INTO audit_log (
                    user_id, action, resource_type, resource_id, details_json,
                    ip_address, user_agent, success, error_message,
                    execution_time_ms, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """

            affected_rows = self.execute_update(
                query,
                (
                    user_id,
                    action,
                    resource_type,
                    resource_id,
                    details_json,
                    ip_address,
                    user_agent,
                    success,
                    error_message,
                    execution_time_ms,
                ),
            )

            if affected_rows > 0:
                logger.debug(f"Audit log entry created: {action} on {resource_type}")
                return True
            else:
                logger.warning(
                    f"Audit log entry had no effect: {action} on {resource_type}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to create audit log entry: {e}")
            return False

    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Retrieve audit logs with optional filtering.

        Args:
            user_id: Filter by user ID (optional)
            action: Filter by action (optional)
            resource_type: Filter by resource type (optional)
            resource_id: Filter by resource ID (optional)
            success: Filter by success status (optional)
            start_time: Filter by start time (optional)
            end_time: Filter by end time (optional)
            limit: Maximum number of results
            offset: Results offset for pagination

        Returns:
            List of audit log dictionaries
        """
        try:
            # Build dynamic query
            query_parts = ["SELECT * FROM audit_log WHERE 1=1"]
            params = []

            if user_id:
                query_parts.append("AND user_id = ?")
                params.append(user_id)

            if action:
                query_parts.append("AND action = ?")
                params.append(action)

            if resource_type:
                query_parts.append("AND resource_type = ?")
                params.append(resource_type)

            if resource_id:
                query_parts.append("AND resource_id = ?")
                params.append(resource_id)

            if success is not None:
                query_parts.append("AND success = ?")
                params.append(success)

            if start_time:
                query_parts.append("AND timestamp >= ?")
                params.append(start_time)

            if end_time:
                query_parts.append("AND timestamp <= ?")
                params.append(end_time)

            # Order by timestamp descending (most recent first)
            query_parts.append("ORDER BY timestamp DESC")

            if limit:
                query_parts.append(f"LIMIT {limit}")
                if offset > 0:
                    query_parts.append(f"OFFSET {offset}")

            query = " ".join(query_parts)
            results = self.execute_query(query, tuple(params))

            # Process results
            audit_logs = []
            for row in results:
                log_entry = dict(row)

                # Parse details JSON
                if log_entry.get("details_json"):
                    try:
                        log_entry["details"] = json.loads(log_entry["details_json"])
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Invalid details JSON in audit log {log_entry['id']}"
                        )
                        log_entry["details"] = {}
                    # Remove the raw JSON field
                    del log_entry["details_json"]
                else:
                    log_entry["details"] = {}

                # Convert SQLite integer to boolean
                if "success" in log_entry:
                    log_entry["success"] = bool(log_entry["success"])

                audit_logs.append(log_entry)

            logger.debug(f"Retrieved {len(audit_logs)} audit log entries")
            return audit_logs

        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return []

    def get_audit_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Get audit statistics for a time period.

        Args:
            start_time: Start time for statistics (optional)
            end_time: End time for statistics (optional)

        Returns:
            Dictionary with audit statistics
        """
        try:
            # Build time filter
            time_filter = ""
            params = []

            if start_time:
                time_filter += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                time_filter += " AND timestamp <= ?"
                params.append(end_time)

            query = f"""
                SELECT
                    COUNT(*) as total_events,
                    COUNT(CASE WHEN success = 1 THEN 1 END) as successful_events,
                    COUNT(CASE WHEN success = 0 THEN 1 END) as failed_events,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT action) as unique_actions,
                    COUNT(DISTINCT resource_type) as unique_resource_types,
                    AVG(execution_time_ms) as avg_execution_time,
                    MAX(timestamp) as last_event_time,
                    MIN(timestamp) as first_event_time
                FROM audit_log
                WHERE 1=1{time_filter}
            """

            results = self.execute_query(query, tuple(params))

            if results:
                stats = dict(results[0])
                logger.debug("Audit statistics retrieved")
                return stats
            else:
                return {}

        except Exception as e:
            logger.error(f"Failed to get audit statistics: {e}")
            return {}

    def get_action_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """Get summary of actions performed.

        Args:
            start_time: Start time for summary (optional)
            end_time: End time for summary (optional)

        Returns:
            List of action summary dictionaries
        """
        try:
            # Build time filter
            time_filter = ""
            params = []

            if start_time:
                time_filter += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                time_filter += " AND timestamp <= ?"
                params.append(end_time)

            query = f"""
                SELECT
                    action,
                    resource_type,
                    COUNT(*) as event_count,
                    COUNT(CASE WHEN success = 1 THEN 1 END) as success_count,
                    COUNT(CASE WHEN success = 0 THEN 1 END) as failure_count,
                    AVG(execution_time_ms) as avg_execution_time,
                    MAX(timestamp) as last_occurrence
                FROM audit_log
                WHERE 1=1{time_filter}
                GROUP BY action, resource_type
                ORDER BY event_count DESC
            """

            results = self.execute_query(query, tuple(params))
            summary = [dict(row) for row in results]

            logger.debug(f"Retrieved action summary with {len(summary)} entries")
            return summary

        except Exception as e:
            logger.error(f"Failed to get action summary: {e}")
            return []

    def get_user_activity(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = 50,
    ) -> list[dict[str, Any]]:
        """Get activity summary for a specific user.

        Args:
            user_id: User identifier
            start_time: Start time for activity (optional)
            end_time: End time for activity (optional)
            limit: Maximum number of results

        Returns:
            List of user activity dictionaries
        """
        try:
            # Build time filter
            time_filter = ""
            params = [user_id]

            if start_time:
                time_filter += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                time_filter += " AND timestamp <= ?"
                params.append(end_time)

            query = f"""
                SELECT action, resource_type, resource_id, success, timestamp, error_message
                FROM audit_log
                WHERE user_id = ?{time_filter}
                ORDER BY timestamp DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            results = self.execute_query(query, tuple(params))
            activity = [dict(row) for row in results]

            logger.debug(
                f"Retrieved {len(activity)} activity entries for user {user_id}"
            )
            return activity

        except Exception as e:
            logger.error(f"Failed to get user activity for {user_id}: {e}")
            return []

    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Clean up old audit logs to manage database size.

        Args:
            days_to_keep: Number of days of logs to retain

        Returns:
            Number of logs deleted
        """
        try:
            query = f"""
                DELETE FROM audit_log
                WHERE timestamp < datetime('now', '-{days_to_keep} days')
            """

            affected_rows = self.execute_update(query)
            logger.info(
                f"Cleaned up {affected_rows} old audit logs (kept {days_to_keep} days)"
            )
            return affected_rows

        except Exception as e:
            logger.error(f"Failed to cleanup old audit logs: {e}")
            return 0

    def get_security_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = 100,
    ) -> list[dict[str, Any]]:
        """Get security-related audit events.

        Args:
            start_time: Start time for events (optional)
            end_time: End time for events (optional)
            limit: Maximum number of results

        Returns:
            List of security event dictionaries
        """
        try:
            # Define security-related actions
            security_actions = [
                "LOGIN",
                "LOGOUT",
                "AUTH_FAIL",
                "ACCESS_DENIED",
                "PASSWORD_CHANGE",
            ]

            # Build time filter
            time_filter = ""
            params = security_actions[:]

            if start_time:
                time_filter += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                time_filter += " AND timestamp <= ?"
                params.append(end_time)

            placeholders = ",".join("?" * len(security_actions))
            query = f"""
                SELECT * FROM audit_log
                WHERE action IN ({placeholders})
                OR success = 0{time_filter}
                ORDER BY timestamp DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            results = self.execute_query(query, tuple(params))

            # Process results
            events = []
            for row in results:
                event = dict(row)

                # Parse details JSON
                if event.get("details_json"):
                    try:
                        event["details"] = json.loads(event["details_json"])
                    except json.JSONDecodeError:
                        event["details"] = {}
                    del event["details_json"]
                else:
                    event["details"] = {}

                events.append(event)

            logger.debug(f"Retrieved {len(events)} security events")
            return events

        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            return []


# Factory function for easy instantiation
def get_audit_manager(db_path: Optional[str] = None) -> AuditManager:
    """Get an audit manager instance.

    Args:
        db_path: Path to SQLite database. If None, uses default.

    Returns:
        AuditManager instance
    """
    return AuditManager(db_path)
