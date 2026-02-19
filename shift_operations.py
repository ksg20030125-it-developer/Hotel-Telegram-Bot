# ==================== SHIFT-BASED OPERATIONS FUNCTIONS ====================

def get_current_shift_type(db, current_time=None):
    """
    Determine which shift (A/B/C/D) is currently active based on database settings and handover status
    
    Shift Schedule: Loaded from tbl_reception_shift (active record)
    
    Handover Rule:
    - New shift cannot be activated until previous shift submits their report
    - If previous shift report is pending, previous shift remains active
    
    Returns:
        str: 'A', 'B', 'C', or 'D'
    """
    from datetime import datetime, timedelta
    
    if current_time is None:
        current_time = datetime.now()
    
    hour = current_time.hour
    minute = current_time.minute
    current_time_minutes = hour * 60 + minute  # Convert to minutes since midnight
    current_date = current_time.strftime('%Y-%m-%d')
    
    # Get shift settings from database
    try:
        from database import get_shift_settings
        settings = get_shift_settings(db)
        
        if not settings:
            print("⚠️ No active shift settings found in database, using default 3-shift schedule")
            # Fallback to default 3-shift schedule
            return _get_default_shift_type(hour)
        
        # Always use 3-shift configuration (A, B, C)
        shift_count = 3
        
        # Build shift schedule from database settings
        shifts = []
        shift_map = {1: 'A', 2: 'B', 3: 'C'}
        
        for i in range(1, shift_count + 1):
            start_time = settings.get(f'shift_{i}_start')
            end_time = settings.get(f'shift_{i}_end')
            
            if start_time and end_time:
                # Convert time strings to minutes
                start_hour, start_min = map(int, start_time.split(':'))
                end_hour, end_min = map(int, end_time.split(':'))
                
                start_minutes = start_hour * 60 + start_min
                end_minutes = end_hour * 60 + end_min
                
                # Handle overnight shifts (end time < start time means crosses midnight)
                if end_minutes <= start_minutes:
                    end_minutes += 24 * 60  # Add 24 hours
                
                shifts.append({
                    'number': i,
                    'type': shift_map[i],
                    'start_minutes': start_minutes,
                    'end_minutes': end_minutes,
                    'start_time': start_time,
                    'end_time': end_time
                })
        
        # Determine current shift based on time
        time_based_shift = None
        shift_number = None
        
        # Check if current time falls within any shift
        # Handle case where current time might be after midnight
        current_time_check = current_time_minutes
        
        for shift in shifts:
            start = shift['start_minutes']
            end = shift['end_minutes']
            
            # Normal shift (within same day)
            if end <= 24 * 60:
                if start <= current_time_check < end:
                    time_based_shift = shift['type']
                    shift_number = shift['number']
                    break
            else:
                # Overnight shift
                if current_time_check >= start or current_time_check < (end - 24 * 60):
                    time_based_shift = shift['type']
                    shift_number = shift['number']
                    break
        
        if not time_based_shift:
            print(f"⚠️ No shift found for current time {hour:02d}:{minute:02d}")
            return 'A'  # Fallback
        
        # Determine previous shift
        prev_shift_number = shift_number - 1 if shift_number > 1 else shift_count
        previous_shift = shift_map[prev_shift_number]
        
        # For shifts that start after midnight, check previous day's reports
        check_date = current_date
        if shifts[shift_number - 1]['start_minutes'] < 12 * 60:  # Starts before noon
            if hour < 12:  # We're in morning, might need to check yesterday
                check_date = (current_time - timedelta(days=1)).strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"⚠️ Error loading shift settings from database: {e}")
        return _get_default_shift_type(hour)
    
    # Check if previous shift has submitted their report
    try:
        prev_shift_employees = db.execute_query("""
            SELECT employee_id, employee_name
            FROM tbl_employee_shifts
            WHERE shift_type = %s
              AND department IN ('Reception', 'Restaurant')
              AND is_active = 1
        """, (previous_shift,))
        
        if prev_shift_employees:
            # Check if ALL employees from previous shift submitted their reports
            all_submitted = True
            pending_employees = []
            
            for emp in prev_shift_employees:
                emp_id = str(emp[0])
                emp_name = emp[1]
                
                # Check if this employee submitted shift report
                has_report = db.execute_query("""
                    SELECT COUNT(*) 
                    FROM tbl_shift_reports
                    WHERE employee_id = %s
                      AND shift_number = %s
                      AND shift_date = %s
                """, (emp_id, prev_shift_number, check_date))
                
                if has_report and has_report[0][0] == 0:
                    all_submitted = False
                    pending_employees.append(emp_name)
            
            # If not all previous shift employees submitted reports, keep previous shift active
            if not all_submitted:
                print(f"⚠️ Handover pending: Previous shift {previous_shift} (#{prev_shift_number}) has {len(pending_employees)} employee(s) who haven't submitted reports")
                print(f"   Pending: {', '.join(pending_employees[:3])}{'...' if len(pending_employees) > 3 else ''}")
                print(f"   Keeping shift {previous_shift} active until handover complete")
                return previous_shift
            else:
                print(f"✅ Handover complete: All previous shift {previous_shift} (#{prev_shift_number}) employees submitted reports")
                print(f"   Activating new shift {time_based_shift} (#{shift_number})")
    
    except Exception as e:
        print(f"⚠️ Error checking shift handover status: {e}")
        # On error, fall back to time-based shift
    
    return time_based_shift


def _get_default_shift_type(hour):
    """Fallback default 3-shift schedule if database settings not available"""
    if 8 <= hour < 16:
        return 'A'
    elif 16 <= hour < 24:
        return 'B'
    else:  # 0 <= hour < 8
        return 'C'


def get_on_shift_employees(db, department, current_time=None):
    """
    Get list of employees currently on shift for a department
    
    Args:
        db: DatabaseManager instance
        department: Department name ('Reception' or 'Restaurant')
        current_time: Optional datetime for testing
        
    Returns:
        list: List of employee dictionaries with keys:
            - employee_id (TEXT format like 'REC001', 'REST001')
            - telegram_user_id
            - name
            - shift_type
            - department
    """
    try:
        current_shift = get_current_shift_type(db, current_time)
        
        result = db.execute_query("""
            SELECT employee_id, telegram_user_id, employee_name, shift_type, department
            FROM tbl_employee_shifts
            WHERE department = %s
              AND shift_type = %s
              AND is_active = 1
        """, (department, current_shift))
        
        employees = []
        if result:
            for row in result:
                employees.append({
                    'employee_id': row[0],
                    'telegram_user_id': row[1],
                    'name': row[2],
                    'shift_type': row[3],
                    'department': row[4]
                })
        
        return employees
        
    except Exception as e:
        print(f"❌ Error getting on-shift employees: {e}")
        return []


def is_employee_on_shift(db, telegram_user_id, current_time=None):
    """
    Check if a specific employee is currently on shift
    
    Args:
        db: DatabaseManager instance
        telegram_user_id: Employee's Telegram user ID
        current_time: Optional datetime for testing
        
    Returns:
        dict: {
            'on_shift': bool,
            'shift_type': str or None,
            'department': str or None
        }
    """
    try:
        current_shift = get_current_shift_type(db, current_time)
        
        result = db.execute_query("""
            SELECT shift_type, department
            FROM tbl_employee_shifts
            WHERE telegram_user_id = %s
              AND shift_type = %s
              AND is_active = 1
        """, (telegram_user_id, current_shift))
        
        if result and len(result) > 0:
            return {
                'on_shift': True,
                'shift_type': result[0][0],
                'department': result[0][1]
            }
        else:
            return {
                'on_shift': False,
                'shift_type': None,
                'department': None
            }
            
    except Exception as e:
        print(f"❌ Error checking employee shift status: {e}")
        return {
            'on_shift': False,
            'shift_type': None,
            'department': None
        }


def get_all_department_employees(db, department):
    """
    Get all employees in a department regardless of shift
    
    Args:
        db: DatabaseManager instance
        department: Department name
        
    Returns:
        list: List of employee dictionaries
    """
    try:
        result = db.execute_query("""
            SELECT DISTINCT employee_id, telegram_user_id, employee_name, shift_type, department
            FROM tbl_employee_shifts
            WHERE department = %s
              AND is_active = 1
        """, (department,))
        
        employees = []
        if result:
            for row in result:
                employees.append({
                    'employee_id': row[0],
                    'telegram_user_id': row[1],
                    'name': row[2],
                    'shift_type': row[3],
                    'department': row[4]
                })
        
        return employees
        
    except Exception as e:
        print(f"❌ Error getting department employees: {e}")
        return []


def get_shift_status_summary(db, department=None):
    """
    Get current shift status summary
    
    Args:
        db: DatabaseManager instance
        department: Optional department filter
        
    Returns:
        dict: Summary with current shift info and employee counts
    """
    from datetime import datetime
    
    try:
        current_time = datetime.now()
        current_shift = get_current_shift_type(db, current_time)
        
        # Build query based on department filter
        if department:
            query = """
                SELECT department, shift_type, COUNT(*) as count
                FROM tbl_employee_shifts
                WHERE is_active = 1 AND department = %s
                GROUP BY department, shift_type
            """
            params = (department,)
        else:
            query = """
                SELECT department, shift_type, COUNT(*) as count
                FROM tbl_employee_shifts
                WHERE is_active = 1
                GROUP BY department, shift_type
            """
            params = ()
        
        result = db.execute_query(query, params)
        
        # Organize by department and shift
        summary = {
            'current_shift': current_shift,
            'current_time': current_time.strftime('%H:%M'),
            'departments': {}
        }
        
        if result:
            for row in result:
                dept = row[0]
                shift = row[1]
                count = row[2]
                
                if dept not in summary['departments']:
                    summary['departments'][dept] = {
                        'A': 0,
                        'B': 0,
                        'C': 0,
                        'on_shift_count': 0,
                        'off_shift_count': 0
                    }
                
                summary['departments'][dept][shift] = count
                
                if shift == current_shift:
                    summary['departments'][dept]['on_shift_count'] = count
                else:
                    summary['departments'][dept]['off_shift_count'] += count
        
        return summary
        
    except Exception as e:
        print(f"❌ Error getting shift status summary: {e}")
        return {
            'current_shift': None,
            'current_time': None,
            'departments': {}
        }


def assign_shift_to_employee(db, employee_id, telegram_user_id, shift_type, department, employee_name):
    """
    Assign or update shift for an employee
    
    Args:
        db: DatabaseManager instance
        employee_id: Employee ID (TEXT format like 'REC001', 'EMP00001')
        telegram_user_id: Telegram user ID
        shift_type: 'A', 'B', or 'C'
        department: Department name
        employee_name: Employee name
        
    Returns:
        bool: Success status
    """
    try:
        # Check if employee already has a shift assignment
        result = db.execute_query("""
            SELECT id FROM tbl_employee_shifts
            WHERE employee_id = %s AND is_active = 1
        """, (employee_id,))
        
        if result and len(result) > 0:
            # Update existing assignment
            db.execute_query("""
                UPDATE tbl_employee_shifts
                SET shift_type = %s,
                    department = %s,
                    telegram_user_id = %s,
                    employee_name = %s
                WHERE employee_id = %s AND is_active = 1
            """, (shift_type, department, telegram_user_id, employee_name, employee_id))
        else:
            # Insert new assignment
            db.execute_query("""
                INSERT INTO tbl_employee_shifts (
                    employee_id, telegram_user_id, employee_name,
                    shift_type, department, is_active
                ) VALUES (%s, %s, %s, %s, %s, 1)
            """, (employee_id, telegram_user_id, employee_name, shift_type, department))
        
        return True
        
    except Exception as e:
        print(f"❌ Error assigning shift: {e}")
        return False


def remove_shift_from_employee(db, employee_id):
    """
    Remove shift assignment from an employee
    
    Args:
        db: DatabaseManager instance
        employee_id: Employee ID (TEXT format)
        
    Returns:
        bool: Success status
    """
    try:
        db.execute_query("""
            UPDATE tbl_employee_shifts
            SET is_active = 0
            WHERE employee_id = %s
        """, (employee_id,))
        
        return True
        
    except Exception as e:
        print(f"❌ Error removing shift: {e}")
        return False


def get_employee_shift_info(db, employee_id):
    """
    Get current shift information for an employee
    
    Args:
        db: DatabaseManager instance
        employee_id: Employee ID (TEXT format)
        
    Returns:
        dict or None: Employee shift info
    """
    try:
        result = db.execute_query("""
            SELECT employee_id, telegram_user_id, employee_name, 
                   shift_type, department, is_active
            FROM tbl_employee_shifts
            WHERE employee_id = %s AND is_active = 1
        """, (employee_id,))
        
        if result and len(result) > 0:
            row = result[0]
            return {
                'employee_id': row[0],
                'telegram_user_id': row[1],
                'name': row[2],
                'shift_type': row[3],
                'department': row[4],
                'is_active': row[5]
            }
        
        return None
        
    except Exception as e:
        print(f"❌ Error getting employee shift info: {e}")
        return None


# Define shift configurations for extensibility
SHIFT_CONFIGS = {
    '3-shift': {
        'A': {'name': 'Morning', 'start': '08:00', 'end': '16:00', 'icon': '🌅'},
        'B': {'name': 'Evening', 'start': '16:00', 'end': '00:00', 'icon': '🌆'},
        'C': {'name': 'Night', 'start': '00:00', 'end': '08:00', 'icon': '🌙'}
    }
    # Future: Can add '2-shift', '4-shift' configurations here
}

# Current active configuration
ACTIVE_SHIFT_CONFIG = '3-shift'


def get_available_shifts():
    """
    Get list of available shift types from active configuration
    
    Returns:
        list: List of shift type codes (e.g., ['A', 'B', 'C'])
    """
    return list(SHIFT_CONFIGS[ACTIVE_SHIFT_CONFIG].keys())


def get_shift_info(shift_type):
    """
    Get information about a specific shift type
    
    Args:
        shift_type: Shift code ('A', 'B', 'C', etc.)
        
    Returns:
        dict or None: Shift configuration
    """
    return SHIFT_CONFIGS[ACTIVE_SHIFT_CONFIG].get(shift_type)


def get_employees_in_department(db, department):
    """
    Get all employees from tbl_employeer by department
    
    Args:
        db: DatabaseManager instance
        department: Department name ('Reception', 'Restaurant', etc.)
        
    Returns:
        list: List of employee dictionaries with keys:
            - employee_id
            - telegram_user_id
            - name
            - work_role
            - department
    """
    try:
        result = db.execute_query("""
            SELECT employee_id, telegram_user_id, name, work_role, department
            FROM tbl_employeer
            WHERE department = %s
            ORDER BY name
        """, (department,))
        
        employees = []
        if result:
            for row in result:
                employees.append({
                    'employee_id': row[0],
                    'telegram_user_id': row[1],
                    'name': row[2],
                    'work_role': row[3],
                    'department': row[4]
                })
        
        return employees
        
    except Exception as e:
        print(f"❌ Error getting employees in department: {e}")
        return []


def get_employee_shift_info(db, employee_id):
    """
    Get shift assignment info for a specific employee
    
    Args:
        db: DatabaseManager instance
        employee_id: Employee ID (e.g., 'REC001', 'EMP00001')
        
    Returns:
        dict or None: Shift info with keys:
            - shift_type
            - department
            - is_active
    """
    try:
        result = db.execute_query("""
            SELECT shift_type, department, is_active
            FROM tbl_employee_shifts
            WHERE employee_id = %s
              AND is_active = 1
        """, (employee_id,))
        
        if result and len(result) > 0:
            return {
                'shift_type': result[0][0],
                'department': result[0][1],
                'is_active': result[0][2]
            }
        return None
        
    except Exception as e:
        print(f"❌ Error getting employee shift info: {e}")
        return None


def assign_shift_to_employee(db, employee_id, telegram_user_id, shift_type, department, employee_name):
    """
    Assign or update shift for an employee
    
    Args:
        db: DatabaseManager instance
        employee_id: Employee ID (TEXT)
        telegram_user_id: Telegram user ID
        shift_type: 'A', 'B', or 'C'
        department: Department name
        employee_name: Employee name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if assignment already exists
        existing = db.execute_query("""
            SELECT employee_id FROM tbl_employee_shifts
            WHERE employee_id = %s AND is_active = 1
        """, (employee_id,))
        
        if existing and len(existing) > 0:
            # Update existing assignment
            db.execute_query("""
                UPDATE tbl_employee_shifts
                SET shift_type = %s, department = %s, telegram_user_id = %s, employee_name = %s
                WHERE employee_id = %s AND is_active = 1
            """, (shift_type, department, telegram_user_id, employee_name, employee_id))
        else:
            # Insert new assignment
            db.execute_query("""
                INSERT INTO tbl_employee_shifts 
                (employee_id, telegram_user_id, employee_name, shift_type, department, is_active)
                VALUES (%s, %s, %s, %s, %s, 1)
            """, (employee_id, telegram_user_id, employee_name, shift_type, department))
        
        print(f"✅ Shift {shift_type} assigned to {employee_name} ({employee_id})")
        return True
        
    except Exception as e:
        print(f"❌ Error assigning shift: {e}")
        return False


def remove_shift_from_employee(db, employee_id):
    """
    Remove shift assignment from an employee
    
    Args:
        db: DatabaseManager instance
        employee_id: Employee ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db.execute_query("""
            UPDATE tbl_employee_shifts
            SET is_active = 0
            WHERE employee_id = %s
        """, (employee_id,))
        
        print(f"✅ Shift removed from employee {employee_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error removing shift: {e}")
        return False


# Export functions
__all__ = [
    'get_current_shift_type',
    'get_on_shift_employees',
    'is_employee_on_shift',
    'get_all_department_employees',
    'get_shift_status_summary',
    'assign_shift_to_employee',
    'remove_shift_from_employee',
    'get_employee_shift_info',
    'get_employees_in_department',
    'get_available_shifts',
    'get_shift_info',
    'SHIFT_CONFIGS',
    'ACTIVE_SHIFT_CONFIG'
]
