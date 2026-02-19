"""
Test script for Shift Handover System

This script demonstrates:
1. Previous shift must complete reports before new shift activates
2. Current shift determination based on handover status
3. Shift transition blocking mechanism

Usage:
    python test_shift_handover.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from shift_operations import get_current_shift_type


def get_shift_schedule():
    """Return shift schedule information"""
    return {
        'A': {'name': 'Morning Shift', 'time': '08:00 - 16:00', 'number': 1},
        'B': {'name': 'Evening Shift', 'time': '16:00 - 00:00', 'number': 2},
        'C': {'name': 'Night Shift', 'time': '00:00 - 08:00', 'number': 3}
    }


def get_time_based_shift(hour):
    """Get shift based on time only (no handover check)"""
    if 8 <= hour < 16:
        return 'A'
    elif 16 <= hour < 24:
        return 'B'
    else:
        return 'C'


def test_shift_handover():
    """Test shift handover mechanism"""
    
    db = DatabaseManager()
    
    print("=" * 70)
    print("🔄 SHIFT HANDOVER SYSTEM TEST")
    print("=" * 70)
    print()
    
    current_time = datetime.now()
    current_hour = current_time.hour
    current_date = current_time.strftime('%Y-%m-%d')
    
    schedule = get_shift_schedule()
    
    print(f"⏰ Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Current Date: {current_date}")
    print()
    
    # Get time-based shift (what it SHOULD be)
    time_based = get_time_based_shift(current_hour)
    print(f"📊 Time-Based Shift: {time_based} - {schedule[time_based]['name']} ({schedule[time_based]['time']})")
    
    # Get actual active shift (considering handover)
    actual_shift = get_current_shift_type(db)
    print(f"✅ Actual Active Shift: {actual_shift} - {schedule[actual_shift]['name']}")
    print()
    
    if time_based != actual_shift:
        print("⚠️" + "=" * 68)
        print("⚠️  HANDOVER PENDING - Previous shift still active!")
        print("⚠️" + "=" * 68)
        print(f"   Previous shift ({actual_shift}) has not completed handover reports.")
        print(f"   New shift ({time_based}) cannot activate until handover is complete.")
        print()
    else:
        print("✅" + "=" * 68)
        print("✅  HANDOVER COMPLETE - Shift transition successful!")
        print("✅" + "=" * 68)
        print()
    
    # Show shift employee status
    print("-" * 70)
    print("📋 SHIFT EMPLOYEE STATUS")
    print("-" * 70)
    
    for shift_type in ['A', 'B', 'C']:
        shift_info = schedule[shift_type]
        print(f"\n🔸 Shift {shift_type} - {shift_info['name']} ({shift_info['time']})")
        
        # Get employees in this shift
        employees = db.execute_query("""
            SELECT telegram_user_id, employee_name, department
            FROM tbl_employee_shifts
            WHERE shift_type = %s
              AND is_active = 1
            ORDER BY department, employee_name
        """, (shift_type,))
        
        if not employees:
            print(f"   No employees assigned")
            continue
        
        print(f"   {len(employees)} employee(s) assigned")
        
        # Check report submission status
        submitted_count = 0
        pending_count = 0
        
        for emp in employees:
            telegram_id = str(emp[0])
            emp_name = emp[1]
            dept = emp[2]
            
            # Check if report submitted
            has_report = db.execute_query("""
                SELECT COUNT(*) 
                FROM tbl_shift_reports
                WHERE telegram_user_id = %s
                  AND shift_number = %s
                  AND report_date = %s
            """, (telegram_id, shift_info['number'], current_date))
            
            if has_report and has_report[0][0] > 0:
                status_icon = "✅"
                status_text = "SUBMITTED"
                submitted_count += 1
            else:
                status_icon = "⏳"
                status_text = "PENDING"
                pending_count += 1
            
            print(f"   {status_icon} {emp_name:20} ({dept:12}) - Report: {status_text}")
        
        print(f"   Summary: {submitted_count} submitted, {pending_count} pending")
        
        # Show if this shift can hand over
        if shift_type == actual_shift:
            print(f"   🟢 Currently ACTIVE")
            if pending_count > 0:
                print(f"   ⚠️ Cannot hand over - {pending_count} report(s) pending")
            else:
                print(f"   ✅ Ready to hand over")
    
    print()
    print("=" * 70)
    print("📝 HANDOVER RULES")
    print("=" * 70)
    print("1. New shift CANNOT activate until previous shift submits ALL reports")
    print("2. Previous shift remains ACTIVE until handover is complete")
    print("3. Shift transition time:")
    print("   - A → B: 16:00")
    print("   - B → C: 00:00")
    print("   - C → A: 08:00")
    print("4. All employees from previous shift must submit reports")
    print()
    
    db.close_connection()


def simulate_handover_scenario():
    """Simulate a shift handover scenario"""
    
    db = DatabaseManager()
    
    print("\n" + "=" * 70)
    print("🎭 HANDOVER SCENARIO SIMULATION")
    print("=" * 70)
    print()
    
    # Simulate different times
    test_times = [
        ("07:30", "Before shift A starts"),
        ("08:00", "Shift A should start"),
        ("08:30", "During shift A"),
        ("15:30", "Before shift B starts"),
        ("16:00", "Shift B should start"),
        ("16:30", "During shift B"),
        ("23:30", "Before shift C starts"),
        ("00:00", "Shift C should start"),
        ("00:30", "During shift C"),
    ]
    
    for time_str, description in test_times:
        hour, minute = map(int, time_str.split(':'))
        test_time = datetime.now().replace(hour=hour, minute=minute, second=0)
        
        time_based = get_time_based_shift(hour)
        actual_shift = get_current_shift_type(db, test_time)
        
        status = "✅ OK" if time_based == actual_shift else "⚠️ BLOCKED"
        
        print(f"{time_str} - {description:25} | Expected: {time_based} | Actual: {actual_shift} | {status}")
    
    print()
    db.close_connection()


if __name__ == "__main__":
    try:
        test_shift_handover()
        
        choice = input("\nRun handover scenario simulation? (y/n): ").strip().lower()
        if choice == 'y':
            simulate_handover_scenario()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
