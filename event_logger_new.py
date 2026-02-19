"""
Event Logger for Hotel Management Bot
Records all actions and events in PostgreSQL tbl_action_history (append-only audit logs)

All audit logs are persisted in PostgreSQL with:
- who: telegram_user_id, employee_name, employee_id, department
- what: action_type, action_detail (JSONB)
- when: timestamp
- which entity: entity_type, entity_id
- before/after state: before_state, after_state (JSONB)

NO JSON FILES - All logs stored in PostgreSQL only.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import threading


class EventLogger:
    """
    Logs all hotel management events to PostgreSQL tbl_action_history
    
    Events include:
    - Task creation, assignment, completion, confirmation
    - Employee actions (check-in, check-out, reports)
    - Admin actions (approvals, settings changes)
    - System events (errors, notifications)
    
    All logs are stored in PostgreSQL only (no JSON files).
    """
    
    # Event categories (entity types)
    CATEGORY_TASK = "task"
    CATEGORY_EMPLOYEE = "employee"
    CATEGORY_ADMIN = "admin"
    CATEGORY_EVENT = "event"
    CATEGORY_FINANCE = "finance"
    CATEGORY_SYSTEM = "system"
    CATEGORY_SHIFT = "shift"
    CATEGORY_NOTIFICATION = "notification"
    CATEGORY_MENU = "menu_item"
    CATEGORY_INVENTORY = "inventory"
    
    # Event actions
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_ASSIGN = "assign"
    ACTION_ACCEPT = "accept"
    ACTION_COMPLETE = "complete"
    ACTION_CONFIRM = "confirm"
    ACTION_REJECT = "reject"
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_VIEW = "view"
    ACTION_SEND = "send"
    ACTION_RECEIVE = "receive"
    ACTION_ERROR = "error"
    ACTION_CHECKIN = "check_in"
    ACTION_CHECKOUT = "check_out"
    
    def __init__(self, db=None):
        """
        Initialize the event logger
        
        Args:
            db: DatabaseManager instance (optional, will be set later if not provided)
        """
        self._db = db
        self._lock = threading.Lock()
    
    def set_db(self, db):
        """Set the database connection"""
        self._db = db
    
    def _get_db(self):
        """Get database connection"""
        return self._db
    
    def _log_to_db(self, user_id: Any, user_name: str, action: str,
                   entity_type: str = None, entity_id: Any = None,
                   action_detail: Dict = None, before_state: Dict = None, 
                   after_state: Dict = None, employee_id: str = "", 
                   department: str = "") -> bool:
        """
        Log event to PostgreSQL database
        
        Args:
            user_id: Telegram user ID who performed the action
            user_name: Name of the user
            action: Action type (create, update, delete, etc.)
            entity_type: Type of entity affected
            entity_id: ID of the affected entity
            action_detail: Additional details about the action
            before_state: State before the action
            after_state: State after the action
            employee_id: Employee ID
            department: Department name
            
        Returns:
            Success status
        """
        db = self._get_db()
        if db is None:
            print("EventLogger: No database connection available")
            return False
        
        try:
            from database import log_audit
            return log_audit(
                db, 
                telegram_user_id=user_id if user_id else 0,
                employee_name=user_name or "System",
                action_type=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id else None,
                action_detail=action_detail,
                before_state=before_state,
                after_state=after_state,
                employee_id=employee_id,
                department=department
            )
        except Exception as e:
            print(f"EventLogger: Error logging to database: {e}")
            return False
    
    def log_event(self, 
                  category: str,
                  action: str,
                  user_id: Any = None,
                  user_name: str = None,
                  target_type: str = None,
                  target_id: Any = None,
                  description: str = None,
                  details: Dict = None,
                  before_state: Dict = None,
                  after_state: Dict = None,
                  employee_id: str = "",
                  department: str = "",
                  result: str = "success") -> Dict:
        """
        Log an event to PostgreSQL
        
        Args:
            category: Event category (task, employee, admin, etc.) - maps to entity_type
            action: Action type (create, update, delete, etc.)
            user_id: ID of the user performing the action
            user_name: Name of the user
            target_type: Type of target (task, employee, event, etc.)
            target_id: ID of the target
            description: Human-readable description
            details: Additional details dictionary
            before_state: State before the action
            after_state: State after the action
            employee_id: Employee ID of the actor
            department: Department of the actor
            result: Result of the action (success, failure, pending)
            
        Returns:
            The created event dictionary
        """
        # Build action_detail including description and other details
        action_detail = details.copy() if details else {}
        if description:
            action_detail['description'] = description
        action_detail['result'] = result
        
        # Determine entity_type - prefer target_type, fall back to category
        entity_type = target_type or category
        
        with self._lock:
            success = self._log_to_db(
                user_id=user_id,
                user_name=user_name,
                action=action,
                entity_type=entity_type,
                entity_id=target_id,
                action_detail=action_detail,
                before_state=before_state,
                after_state=after_state,
                employee_id=employee_id,
                department=department
            )
        
        # Return event dict for compatibility
        return {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "action": action,
            "user_id": user_id,
            "user_name": user_name,
            "target_type": target_type,
            "target_id": target_id,
            "description": description,
            "details": details,
            "result": result,
            "logged_to_db": success
        }
    
    # Convenience methods for common events
    
    def log_task_created(self, user_id, user_name: str, task_id: int, 
                         task_description: str, assignee: str = None, 
                         department: str = None, priority: str = None,
                         employee_id: str = ""):
        """Log task creation event"""
        return self.log_event(
            category=self.CATEGORY_TASK,
            action=self.ACTION_CREATE,
            user_id=user_id,
            user_name=user_name,
            target_type="task",
            target_id=task_id,
            description=f"Task #{task_id} created",
            details={
                "task_description": task_description,
                "assignee": assignee,
                "priority": priority
            },
            after_state={
                "task_id": task_id,
                "description": task_description,
                "assignee": assignee,
                "department": department,
                "priority": priority,
                "status": "pending"
            },
            employee_id=employee_id,
            department=department or ""
        )
    
    def log_task_assigned(self, user_id, user_name: str, task_id: int,
                          assignee_id: str, assignee_name: str,
                          department: str = "", employee_id: str = ""):
        """Log task assignment event"""
        return self.log_event(
            category=self.CATEGORY_TASK,
            action=self.ACTION_ASSIGN,
            user_id=user_id,
            user_name=user_name,
            target_type="task",
            target_id=task_id,
            description=f"Task #{task_id} assigned to {assignee_name}",
            details={
                "assignee_id": assignee_id,
                "assignee_name": assignee_name
            },
            after_state={
                "assignee_id": assignee_id,
                "assignee_name": assignee_name
            },
            employee_id=employee_id,
            department=department
        )
    
    def log_task_accepted(self, user_id, user_name: str, task_id: int,
                          department: str = "", employee_id: str = "",
                          before_status: str = "pending"):
        """Log task acceptance event"""
        return self.log_event(
            category=self.CATEGORY_TASK,
            action=self.ACTION_ACCEPT,
            user_id=user_id,
            user_name=user_name,
            target_type="task",
            target_id=task_id,
            description=f"Task #{task_id} accepted by {user_name}",
            before_state={"status": before_status},
            after_state={"status": "accepted", "accepted_by": user_name},
            employee_id=employee_id,
            department=department
        )
    
    def log_task_completed(self, user_id, user_name: str, task_id: int,
                           report_notes: str = None, has_attachment: bool = False,
                           department: str = "", employee_id: str = "",
                           before_status: str = "in_progress"):
        """Log task completion event"""
        return self.log_event(
            category=self.CATEGORY_TASK,
            action=self.ACTION_COMPLETE,
            user_id=user_id,
            user_name=user_name,
            target_type="task",
            target_id=task_id,
            description=f"Task #{task_id} completed by {user_name}",
            details={
                "report_notes": report_notes,
                "has_attachment": has_attachment
            },
            before_state={"status": before_status},
            after_state={
                "status": "completed",
                "completed_by": user_name,
                "report_notes": report_notes
            },
            employee_id=employee_id,
            department=department
        )
    
    def log_task_confirmed(self, admin_id, admin_name: str, task_id: int,
                           employee_name: str, department: str = "",
                           employee_id: str = ""):
        """Log task confirmation by admin"""
        return self.log_event(
            category=self.CATEGORY_TASK,
            action=self.ACTION_CONFIRM,
            user_id=admin_id,
            user_name=admin_name,
            target_type="task",
            target_id=task_id,
            description=f"Task #{task_id} confirmed by admin {admin_name}",
            details={"completed_by": employee_name},
            before_state={"status": "completed"},
            after_state={"status": "confirmed", "confirmed_by": admin_name},
            employee_id=employee_id,
            department=department
        )
    
    def log_employee_login(self, user_id, user_name: str, department: str,
                           employee_id: str = ""):
        """Log employee login/start command"""
        return self.log_event(
            category=self.CATEGORY_EMPLOYEE,
            action=self.ACTION_LOGIN,
            user_id=user_id,
            user_name=user_name,
            target_type="session",
            description=f"{user_name} logged in",
            details={"department": department},
            after_state={"logged_in": True, "login_time": datetime.now().isoformat()},
            employee_id=employee_id,
            department=department
        )
    
    def log_shift_check_in(self, user_id, user_name: str, department: str,
                           check_in_time: str, employee_id: str = ""):
        """Log shift check-in"""
        return self.log_event(
            category=self.CATEGORY_SHIFT,
            action=self.ACTION_CHECKIN,
            user_id=user_id,
            user_name=user_name,
            target_type="shift",
            description=f"{user_name} checked in at {check_in_time}",
            after_state={
                "check_in_time": check_in_time,
                "status": "checked_in"
            },
            employee_id=employee_id,
            department=department
        )
    
    def log_shift_check_out(self, user_id, user_name: str, department: str,
                            check_out_time: str, employee_id: str = "",
                            check_in_time: str = None):
        """Log shift check-out"""
        return self.log_event(
            category=self.CATEGORY_SHIFT,
            action=self.ACTION_CHECKOUT,
            user_id=user_id,
            user_name=user_name,
            target_type="shift",
            description=f"{user_name} checked out at {check_out_time}",
            before_state={
                "check_in_time": check_in_time,
                "status": "checked_in"
            } if check_in_time else None,
            after_state={
                "check_out_time": check_out_time,
                "status": "checked_out"
            },
            employee_id=employee_id,
            department=department
        )
    
    def log_shift_report_submitted(self, user_id, user_name: str, 
                                   shift_type: str, department: str,
                                   report_data: Dict = None,
                                   employee_id: str = ""):
        """Log shift report submission"""
        return self.log_event(
            category=self.CATEGORY_SHIFT,
            action=self.ACTION_CREATE,
            user_id=user_id,
            user_name=user_name,
            target_type="shift_report",
            description=f"Shift report submitted by {user_name}",
            details={
                "shift_type": shift_type,
                "report_summary": report_data
            },
            after_state=report_data,
            employee_id=employee_id,
            department=department
        )
    
    def log_menu_status_change(self, user_id, user_name: str, item_id: int,
                               item_name: str, old_status: str, new_status: str,
                               department: str = "", employee_id: str = ""):
        """Log menu item status change"""
        return self.log_event(
            category=self.CATEGORY_MENU,
            action=self.ACTION_UPDATE,
            user_id=user_id,
            user_name=user_name,
            target_type="menu_item",
            target_id=item_id,
            description=f"Menu item #{item_id} '{item_name}' status changed",
            before_state={"status": old_status},
            after_state={"status": new_status},
            employee_id=employee_id,
            department=department
        )
    
    def log_inventory_update(self, user_id, user_name: str, item_id: int,
                             item_name: str, old_stock: float, new_stock: float,
                             unit: str = "", department: str = "", 
                             employee_id: str = ""):
        """Log inventory stock update"""
        return self.log_event(
            category=self.CATEGORY_INVENTORY,
            action=self.ACTION_UPDATE,
            user_id=user_id,
            user_name=user_name,
            target_type="inventory",
            target_id=item_id,
            description=f"Inventory #{item_id} '{item_name}' updated: {old_stock} → {new_stock}{unit}",
            before_state={"stock": old_stock, "unit": unit},
            after_state={"stock": new_stock, "unit": unit},
            employee_id=employee_id,
            department=department
        )
    
    def log_event_created(self, user_id, user_name: str, event_id: int,
                          event_name: str, event_type: str, event_date: str,
                          department: str = "", employee_id: str = ""):
        """Log hotel event creation"""
        return self.log_event(
            category=self.CATEGORY_EVENT,
            action=self.ACTION_CREATE,
            user_id=user_id,
            user_name=user_name,
            target_type="hotel_event",
            target_id=event_id,
            description=f"Event '{event_name}' created",
            details={
                "event_name": event_name,
                "event_type": event_type,
                "event_date": event_date
            },
            after_state={
                "event_id": event_id,
                "name": event_name,
                "type": event_type,
                "date": event_date,
                "status": "created"
            },
            employee_id=employee_id,
            department=department
        )
    
    def log_event_updated(self, user_id, user_name: str, event_id: int,
                          changes: Dict, before_state: Dict = None,
                          department: str = "", employee_id: str = ""):
        """Log hotel event update"""
        return self.log_event(
            category=self.CATEGORY_EVENT,
            action=self.ACTION_UPDATE,
            user_id=user_id,
            user_name=user_name,
            target_type="hotel_event",
            target_id=event_id,
            description=f"Event #{event_id} updated",
            details={"changes": changes},
            before_state=before_state,
            after_state=changes,
            employee_id=employee_id,
            department=department
        )
    
    def log_financial_transaction(self, user_id, user_name: str,
                                  transaction_type: str, amount: float,
                                  category: str, description: str = None,
                                  department: str = "", employee_id: str = ""):
        """Log financial transaction"""
        return self.log_event(
            category=self.CATEGORY_FINANCE,
            action=self.ACTION_CREATE,
            user_id=user_id,
            user_name=user_name,
            target_type="transaction",
            description=f"Financial transaction: {transaction_type} {amount}",
            details={
                "transaction_type": transaction_type,
                "amount": amount,
                "category": category,
                "description": description
            },
            after_state={
                "transaction_type": transaction_type,
                "amount": amount,
                "category": category
            },
            employee_id=employee_id,
            department=department
        )
    
    def log_admin_action(self, admin_id, admin_name: str, action: str,
                         target_type: str, target_id: Any = None,
                         description: str = None, details: Dict = None,
                         before_state: Dict = None, after_state: Dict = None,
                         department: str = "", employee_id: str = ""):
        """Log admin action"""
        return self.log_event(
            category=self.CATEGORY_ADMIN,
            action=action,
            user_id=admin_id,
            user_name=admin_name,
            target_type=target_type,
            target_id=target_id,
            description=description or f"Admin action: {action}",
            details=details,
            before_state=before_state,
            after_state=after_state,
            employee_id=employee_id,
            department=department
        )
    
    def log_notification_sent(self, recipient_id, recipient_name: str,
                              notification_type: str, message_preview: str = None,
                              department: str = ""):
        """Log notification sent"""
        return self.log_event(
            category=self.CATEGORY_NOTIFICATION,
            action=self.ACTION_SEND,
            user_id=0,  # System action
            user_name="System",
            target_type="notification",
            target_id=recipient_id,
            description=f"Notification sent to {recipient_name}",
            details={
                "recipient_id": recipient_id,
                "recipient_name": recipient_name,
                "notification_type": notification_type,
                "message_preview": message_preview[:100] if message_preview else None
            },
            after_state={
                "sent": True,
                "notification_type": notification_type
            },
            department=department
        )
    
    def log_error(self, error_type: str, error_message: str,
                  user_id: Any = None, context: Dict = None):
        """Log system error"""
        return self.log_event(
            category=self.CATEGORY_SYSTEM,
            action=self.ACTION_ERROR,
            user_id=user_id,
            user_name="System",
            target_type="error",
            description=f"Error: {error_type}",
            details={
                "error_type": error_type,
                "error_message": error_message,
                "context": context
            },
            result="failure"
        )
    
    # Query methods - now query PostgreSQL via database functions
    
    def get_events_by_date(self, date: str) -> List[Dict]:
        """
        Get all events for a specific date from PostgreSQL
        
        Args:
            date: Date string (YYYY-MM-DD)
            
        Returns:
            List of events
        """
        db = self._get_db()
        if db is None:
            return []
        
        try:
            from database import get_action_history_by_date
            return get_action_history_by_date(db, date)
        except Exception as e:
            print(f"EventLogger: Error getting events by date: {e}")
            return []
    
    def get_events_by_user(self, user_id: Any, date: str = None) -> List[Dict]:
        """
        Get all events by a specific user
        
        Args:
            user_id: User ID
            date: Optional date filter
            
        Returns:
            List of events
        """
        events = self.get_events_by_date(date) if date else []
        return [e for e in events if e.get("telegram_user_id") == user_id]
    
    def get_events_by_category(self, category: str, date: str = None) -> List[Dict]:
        """
        Get all events of a specific category/entity_type
        
        Args:
            category: Event category (entity_type)
            date: Optional date filter
            
        Returns:
            List of events
        """
        events = self.get_events_by_date(date) if date else []
        return [e for e in events if e.get("entity_type") == category]
    
    def get_daily_summary(self, date: str = None) -> Dict:
        """
        Get summary for a specific date from PostgreSQL
        
        Args:
            date: Date string (YYYY-MM-DD)
            
        Returns:
            Summary dictionary
        """
        db = self._get_db()
        if db is None:
            return {"total_events": 0, "by_category": {}, "by_action": {}, "by_user": {}}
        
        try:
            from database import get_action_statistics
            stats = get_action_statistics(db, date)
            return {
                "total_events": stats.get('total', 0),
                "by_type": stats.get('by_type', []),
                "by_user": stats.get('by_user', [])
            }
        except Exception as e:
            print(f"EventLogger: Error getting daily summary: {e}")
            return {"total_events": 0, "by_category": {}, "by_action": {}, "by_user": {}}
    
    def get_recent_events(self, count: int = 50, date: str = None) -> List[Dict]:
        """
        Get most recent events
        
        Args:
            count: Number of events to return
            date: Optional date filter
            
        Returns:
            List of recent events
        """
        db = self._get_db()
        if db is None:
            return []
        
        try:
            from database import get_action_history_by_date
            return get_action_history_by_date(db, date, limit=count)
        except Exception as e:
            print(f"EventLogger: Error getting recent events: {e}")
            return []


# Singleton instance
_event_logger = None


def get_event_logger(db=None) -> EventLogger:
    """Get or create the EventLogger singleton"""
    global _event_logger
    if _event_logger is None:
        _event_logger = EventLogger(db)
        print("Event logger initialized (PostgreSQL only)")
    elif db is not None and _event_logger._db is None:
        _event_logger.set_db(db)
    return _event_logger
