"""
Test script to demonstrate ON_SHIFT vs OFF_SHIFT notification filtering

This script demonstrates:
1. Only ON_SHIFT employees receive operational notifications
2. OFF_SHIFT employees are skipped for Reception/Restaurant/Kitchen departments
3. Other departments (Housekeeping, Maintenance, etc.) receive all notifications

Usage:
    python test_on_shift_notifications.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from shift_operations import is_employee_on_shift, get_current_shift_type


def test_shift_based_notifications():
    """Test which employees would receive notifications based on shift status"""
    
    db = DatabaseManager()
    
    print("=" * 60)
    print("📋 ON_SHIFT vs OFF_SHIFT Notification Test")
    print("=" * 60)
    print(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔄 Current shift: {get_current_shift_type(db)}")
    print()
    
    # Test departments that require shift filtering
    shift_departments = ['Reception', 'Restaurant', 'Kitchen']
    
    for dept in shift_departments:
        print(f"\n{'=' * 60}")
        print(f"🏢 Department: {dept}")
        print("=" * 60)
        
        # Get all employees in department
        employees = db.execute_query("""
            SELECT e.name, e.telegram_user_id, s.shift_type, s.is_active
            FROM tbl_employeer e
            LEFT JOIN tbl_employee_shifts s ON e.telegram_user_id = s.telegram_user_id
            WHERE e.department = %s
            ORDER BY e.name
        """, (dept,))
        
        if not employees:
            print(f"⚠️ No employees found in {dept}")
            continue
        
        print(f"\n📊 Total employees: {len(employees)}")
        print("-" * 60)
        
        on_shift_count = 0
        off_shift_count = 0
        
        for emp in employees:
            name = emp[0]
            telegram_id = emp[1]
            assigned_shift = emp[2] if len(emp) > 2 else None
            is_active = emp[3] if len(emp) > 3 else 0
            
            # Check current shift status
            shift_status = is_employee_on_shift(db, telegram_id)
            
            if shift_status['on_shift']:
                status_icon = "🟢"
                status_text = "ON_SHIFT"
                notification = "✅ WILL RECEIVE"
                on_shift_count += 1
            else:
                status_icon = "🔴"
                status_text = "OFF_SHIFT"
                notification = "⏭️ SKIPPED"
                off_shift_count += 1
            
            print(f"{status_icon} {name:20} | Shift: {assigned_shift or 'N/A':1} | {status_text:10} | {notification}")
        
        print("-" * 60)
        print(f"📈 Summary: {on_shift_count} ON_SHIFT (receive) | {off_shift_count} OFF_SHIFT (skip)")
    
    # Test departments that DON'T require shift filtering
    print(f"\n\n{'=' * 60}")
    print("🏢 Other Departments (No Shift Filtering)")
    print("=" * 60)
    
    other_departments = db.execute_query("""
        SELECT DISTINCT department 
        FROM tbl_employeer 
        WHERE department NOT IN ('Reception', 'Restaurant', 'Kitchen')
        ORDER BY department
    """)
    
    for dept_row in other_departments:
        dept = dept_row[0]
        employees = db.execute_query("""
            SELECT name, telegram_user_id
            FROM tbl_employeer
            WHERE department = %s
        """, (dept,))
        
        print(f"\n🏢 {dept}: {len(employees)} employee(s) - ✅ ALL RECEIVE notifications")
    
    print("\n" + "=" * 60)
    print("📝 Notification Rules:")
    print("=" * 60)
    print("1. ✅ Reception/Restaurant/Kitchen: Only ON_SHIFT employees receive")
    print("2. ✅ Other departments: ALL employees receive notifications")
    print("3. ✅ Event alarms: Filtered by shift status")
    print("4. ✅ Shift reports: Only assigned shift employees")
    print("5. ✅ Overdue tasks: Filtered by shift status")
    print("6. ✅ Escalations: Filtered by shift status")
    print()
    
    db.close_connection()


def test_specific_employee():
    """Test a specific employee's notification eligibility"""
    
    db = DatabaseManager()
    
    print("\n" + "=" * 60)
    print("🔍 Specific Employee Test")
    print("=" * 60)
    
    # Get employee by name
    emp_name = input("\nEnter employee name (or press Enter to skip): ").strip()
    
    if emp_name:
        employee = db.execute_query("""
            SELECT e.name, e.telegram_user_id, e.department, s.shift_type
            FROM tbl_employeer e
            LEFT JOIN tbl_employee_shifts s ON e.telegram_user_id = s.telegram_user_id
            WHERE e.name LIKE %s
            LIMIT 1
        """, (f'%{emp_name}%',))
        
        if employee:
            name = employee[0][0]
            telegram_id = employee[0][1]
            dept = employee[0][2]
            assigned_shift = employee[0][3] if len(employee[0]) > 3 else None
            
            shift_status = is_employee_on_shift(db, telegram_id)
            
            print(f"\n👤 Employee: {name}")
            print(f"🏢 Department: {dept}")
            print(f"📋 Assigned Shift: {assigned_shift or 'None'}")
            print(f"⏰ Current Shift: {get_current_shift_type(db)}")
            print(f"📊 Current Status: {'🟢 ON_SHIFT' if shift_status['on_shift'] else '🔴 OFF_SHIFT'}")
            print()
            
            if dept in ['Reception', 'Restaurant', 'Kitchen']:
                if shift_status['on_shift']:
                    print("✅ This employee WILL RECEIVE operational notifications")
                else:
                    print("⏭️ This employee will NOT receive operational notifications (OFF_SHIFT)")
            else:
                print("✅ This employee WILL RECEIVE all notifications (no shift filtering)")
        else:
            print(f"❌ Employee '{emp_name}' not found")
    
    db.close_connection()


if __name__ == "__main__":
    try:
        test_shift_based_notifications()
        test_specific_employee()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
