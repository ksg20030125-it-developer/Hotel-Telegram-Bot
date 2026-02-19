"""
Templates for Hotel Management Bot
Event templates, shift report templates, and input step definitions
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


# Event Templates with default tasks
EVENT_TEMPLATES = {
    'wedding': {
        'name': {'en': '💒 Wedding', 'sr': '💒 Svadba'},
        'default_tasks': [
            {'department': 'Reception', 'task': 'Prepare welcome drinks', 'days_before': 0},
            {'department': 'Reception', 'task': 'Coordinate guest arrivals', 'days_before': 0},
            {'department': 'Housekeeping', 'task': 'Deep clean event hall', 'days_before': 1},
            {'department': 'Housekeeping', 'task': 'Set up decorations', 'days_before': 0},
            {'department': 'Kitchen', 'task': 'Prepare wedding menu', 'days_before': 1},
            {'department': 'Kitchen', 'task': 'Prepare wedding cake', 'days_before': 0},
            {'department': 'Maintenance', 'task': 'Check sound system', 'days_before': 1},
            {'department': 'Maintenance', 'task': 'Set up lighting', 'days_before': 0},
        ]
    },
    'conference': {
        'name': {'en': '🎤 Conference', 'sr': '🎤 Konferencija'},
        'default_tasks': [
            {'department': 'Reception', 'task': 'Prepare registration desk', 'days_before': 0},
            {'department': 'Reception', 'task': 'Print name badges', 'days_before': 1},
            {'department': 'Housekeeping', 'task': 'Set up conference room', 'days_before': 1},
            {'department': 'Housekeeping', 'task': 'Arrange seating', 'days_before': 0},
            {'department': 'Kitchen', 'task': 'Prepare coffee service', 'days_before': 0},
            {'department': 'Kitchen', 'task': 'Prepare lunch buffet', 'days_before': 0},
            {'department': 'Maintenance', 'task': 'Test projector and screen', 'days_before': 1},
            {'department': 'Maintenance', 'task': 'Check Wi-Fi connectivity', 'days_before': 1},
        ]
    },
    'birthday': {
        'name': {'en': '🎂 Birthday Party', 'sr': '🎂 Rođendan'},
        'default_tasks': [
            {'department': 'Reception', 'task': 'Welcome guests', 'days_before': 0},
            {'department': 'Housekeeping', 'task': 'Decorate party room', 'days_before': 0},
            {'department': 'Housekeeping', 'task': 'Set up balloon decorations', 'days_before': 0},
            {'department': 'Kitchen', 'task': 'Prepare birthday cake', 'days_before': 0},
            {'department': 'Kitchen', 'task': 'Prepare party snacks', 'days_before': 0},
            {'department': 'Maintenance', 'task': 'Set up music system', 'days_before': 0},
        ]
    },
    'corporate': {
        'name': {'en': '💼 Corporate Event', 'sr': '💼 Korporativni događaj'},
        'default_tasks': [
            {'department': 'Reception', 'task': 'Prepare VIP welcome', 'days_before': 0},
            {'department': 'Reception', 'task': 'Coordinate parking', 'days_before': 0},
            {'department': 'Housekeeping', 'task': 'Set up meeting room', 'days_before': 1},
            {'department': 'Housekeeping', 'task': 'Prepare presentation materials', 'days_before': 1},
            {'department': 'Kitchen', 'task': 'Prepare executive lunch', 'days_before': 0},
            {'department': 'Kitchen', 'task': 'Prepare refreshments', 'days_before': 0},
            {'department': 'Maintenance', 'task': 'Check AV equipment', 'days_before': 1},
        ]
    },
    'gala': {
        'name': {'en': '🎭 Gala Dinner', 'sr': '🎭 Gala večera'},
        'default_tasks': [
            {'department': 'Reception', 'task': 'Coordinate red carpet arrival', 'days_before': 0},
            {'department': 'Reception', 'task': 'Manage guest list', 'days_before': 1},
            {'department': 'Housekeeping', 'task': 'Set up formal dining', 'days_before': 1},
            {'department': 'Housekeeping', 'task': 'Polish silverware', 'days_before': 1},
            {'department': 'Kitchen', 'task': 'Prepare gourmet menu', 'days_before': 1},
            {'department': 'Kitchen', 'task': 'Coordinate wine service', 'days_before': 0},
            {'department': 'Maintenance', 'task': 'Set up stage lighting', 'days_before': 1},
            {'department': 'Maintenance', 'task': 'Test microphones', 'days_before': 0},
        ]
    },
    'custom': {
        'name': {'en': '📋 Custom Event', 'sr': '📋 Prilagođeni događaj'},
        'default_tasks': []
    }
}


# Event input steps
EVENT_INPUT_STEPS = {
    1: {
        'field': 'event_name',
        'title': {'en': 'Event Name', 'sr': 'Naziv događaja'},
        'prompt': {'en': 'Enter the name of the event:', 'sr': 'Unesite naziv događaja:'}
    },
    2: {
        'field': 'description',
        'title': {'en': 'Description', 'sr': 'Opis'},
        'prompt': {'en': 'Enter a description for the event:', 'sr': 'Unesite opis događaja:'}
    },
    3: {
        'field': 'event_date',
        'title': {'en': 'Event Date', 'sr': 'Datum događaja'},
        'prompt': {'en': 'Select the event date from the calendar:', 'sr': 'Izaberite datum događaja iz kalendara:'},
        'type': 'calendar'
    },
    4: {
        'field': 'event_time',
        'title': {'en': 'Event Time', 'sr': 'Vreme događaja'},
        'prompt': {'en': 'Enter the event time (HH:MM format, e.g., 14:30):', 'sr': 'Unesite vreme događaja (HH:MM format, npr. 14:30):'}
    },
    5: {
        'field': 'guest_count',
        'title': {'en': 'Expected Guests', 'sr': 'Očekivani gosti'},
        'prompt': {'en': 'Enter the expected number of guests:', 'sr': 'Unesite očekivani broj gostiju:'}
    },
    6: {
        'field': 'location',
        'title': {'en': 'Location', 'sr': 'Lokacija'},
        'prompt': {'en': 'Enter the event location (e.g., Main Hall, Garden):', 'sr': 'Unesite lokaciju događaja (npr. Glavna sala, Bašta):'}
    },
    7: {
        'field': 'notes',
        'title': {'en': 'Additional Notes', 'sr': 'Dodatne napomene'},
        'prompt': {'en': 'Enter any additional notes (or type "skip" to skip):', 'sr': 'Unesite dodatne napomene (ili ukucajte "skip" da preskočite):'}
    }
}


# Reception shift report template
RECEPTION_SHIFT_REPORT_STEPS = {
    1: {
        'field': 'reservations_arrivals',
        'title': {'en': 'Reservations & Arrivals', 'sr': 'Rezervacije i dolasci'},
        'prompt': {'en': 'Enter: reservations,arrivals (example: 15,8)\nOr just reservations count:', 'sr': 'Unesite: rezervacije,dolasci (primer: 15,8)\nIli samo broj rezervacija:'},
        'type': 'text',
        'hint': {'en': 'You can enter both values separated by comma, or just reservations', 'sr': 'Mozete uneti obe vrednosti odvojene zarezom, ili samo rezervacije'}
    },
    2: {
        'field': 'cash_amount',
        'title': {'en': 'Cash Report', 'sr': 'Izvestaj o gotovini'},
        'prompt': {'en': 'Total cash amount collected (enter amount):', 'sr': 'Ukupan iznos gotovine (unesite iznos):'},
        'type': 'number'
    },
    3: {
        'field': 'cash_photo',
        'title': {'en': 'Cash & POS Report Photos', 'sr': 'Fotografije gotovine i POS izvestaja'},
        'prompt': {'en': 'Upload photo of cash + POS report:', 'sr': 'Otpremite fotografiju gotovine + POS izvestaja:'},
        'type': 'photo',
        'hint': {'en': 'Single photo with both cash register and POS report visible', 'sr': 'Jedna fotografija sa oba izvestaja vidljiva'}
    },
    4: {
        'field': 'hotel_register_photo',
        'title': {'en': 'Hotel Register', 'sr': 'Hotelska knjiga'},
        'prompt': {'en': 'Upload photo of hotel register (guest book):', 'sr': 'Otpremite fotografiju hotelske knjige:'},
        'type': 'photo'
    },
    5: {
        'field': 'store_stock_notes',
        'title': {'en': 'Store & Restaurant Status', 'sr': 'Status prodavnice i restorana'},
        'prompt': {'en': 'Store stock issues? Restaurant cash confirmed?\n(type "ok" if all good):', 'sr': 'Problemi sa zalihama? Potvrda gotovine restorana?\n(ukucajte "ok" ako je sve u redu):'},
        'type': 'text'
    },
    6: {
        'field': 'key_tool_notes',
        'title': {'en': 'Keys & Tools Log', 'sr': 'Evidencija kljuceva i alata'},
        'prompt': {'en': 'Keys/tools issued or returned?\n(type "ok" if none):', 'sr': 'Izdati/vraceni kljucevi ili alati?\n(ukucajte "ok" ako nema):'},
        'type': 'text'
    },
    7: {
        'field': 'additional_notes',
        'title': {'en': 'Additional Notes', 'sr': 'Dodatne napomene'},
        'prompt': {'en': 'Any other notes for next shift?\n(type "ok" if none):', 'sr': 'Druge napomene za sledecu smenu?\n(ukucajte "ok" ako nema):'},
        'type': 'text'
    }
}

# Restaurant shift report template
RESTAURANT_SHIFT_REPORT_STEPS = {
    1: {
        'field': 'guests_served',
        'title': {'en': 'Guests Served', 'sr': 'Usluzeni gosti'},
        'prompt': {'en': 'Total number of guests served during your shift:', 'sr': 'Ukupan broj usluzenih gostiju tokom smene:'},
        'type': 'number'
    },
    2: {
        'field': 'cash_sales',
        'title': {'en': 'Cash Sales', 'sr': 'Gotovinska prodaja'},
        'prompt': {'en': 'Total cash sales amount:', 'sr': 'Ukupan iznos gotovinske prodaje:'},
        'type': 'number'
    },
    3: {
        'field': 'card_sales',
        'title': {'en': 'Card Sales', 'sr': 'Kartična prodaja'},
        'prompt': {'en': 'Total card payment sales amount:', 'sr': 'Ukupan iznos prodaje karticama:'},
        'type': 'number'
    },
    4: {
        'field': 'food_waste',
        'title': {'en': 'Food Waste Report', 'sr': 'Izvestaj o otpadu hrane'},
        'prompt': {'en': 'Any significant food waste? Describe items (or type "none"):', 'sr': 'Znacajan otpad hrane? Opišite stavke (ili ukucajte "nema"):'},
        'type': 'text'
    },
    5: {
        'field': 'inventory_issues',
        'title': {'en': 'Inventory Issues', 'sr': 'Problemi sa zalihama'},
        'prompt': {'en': 'Any low stock or inventory issues? (type "none" if none):', 'sr': 'Nizak nivo zaliha ili problemi? (ukucajte "nema" ako nema):'},
        'type': 'text'
    },
    6: {
        'field': 'equipment_issues',
        'title': {'en': 'Equipment Status', 'sr': 'Status opreme'},
        'prompt': {'en': 'Any equipment problems or maintenance needed? (type "none" if none):', 'sr': 'Problemi sa opremom ili potrebno odrzavanje? (ukucajte "nema" ako nema):'},
        'type': 'text'
    },
    7: {
        'field': 'notes',
        'title': {'en': 'Additional Notes', 'sr': 'Dodatne napomene'},
        'prompt': {'en': 'Any other notes for the next shift? (type "none" if none):', 'sr': 'Druge napomene za sledecu smenu? (ukucajte "nema" ako nema):'},
        'type': 'text'
    }
}


def get_event_template(event_type: str) -> Dict[str, Any]:
    """
    Get event template by type
    
    Args:
        event_type: Event type key
        
    Returns:
        Event template dictionary
    """
    return EVENT_TEMPLATES.get(event_type, EVENT_TEMPLATES['custom'])


def get_event_input_step(lang: str, step: int) -> Dict[str, str]:
    """
    Get event input step information
    
    Args:
        lang: Language code
        step: Step number (1-7)
        
    Returns:
        Dictionary with title and prompt for the step
    """
    step_info = EVENT_INPUT_STEPS.get(step, EVENT_INPUT_STEPS[1])
    return {
        'field': step_info['field'],
        'title': step_info['title'].get(lang, step_info['title']['en']),
        'prompt': step_info['prompt'].get(lang, step_info['prompt']['en']),
        'type': step_info.get('type', 'text')
    }


def get_shift_report_input_template(lang: str, step: int, department: str = 'Reception') -> Dict[str, str]:
    """
    Get shift report input step information based on department
    
    Args:
        lang: Language code
        step: Step number
        department: Department name ('Reception' or 'Restaurant')
        
    Returns:
        Dictionary with title and prompt for the step
    """
    # Select the appropriate template based on department
    if department == 'Restaurant':
        template = RESTAURANT_SHIFT_REPORT_STEPS
    else:
        template = RECEPTION_SHIFT_REPORT_STEPS
    
    step_info = template.get(step, template.get(1))
    return {
        'field': step_info['field'],
        'title': step_info['title'].get(lang, step_info['title']['en']),
        'prompt': step_info['prompt'].get(lang, step_info['prompt']['en']),
        'type': step_info.get('type', 'text'),
        'hint': step_info.get('hint', {}).get(lang, step_info.get('hint', {}).get('en', '')) if step_info.get('hint') else ''
    }


def auto_assign_event_tasks(db, event_id: int, event_type: str, event_date: str) -> List[int]:
    """
    Automatically create tasks for an event based on template
    
    Args:
        db: Database manager instance
        event_id: Event ID
        event_type: Event type key
        event_date: Event date string (YYYY-MM-DD)
        
    Returns:
        List of created task IDs
    """
    template = get_event_template(event_type)
    created_task_ids = []
    
    if not template.get('default_tasks'):
        return created_task_ids
    
    try:
        event_date_obj = datetime.strptime(event_date, '%Y-%m-%d')
        
        for task_template in template['default_tasks']:
            department = task_template['department']
            task_desc = task_template['task']
            days_before = task_template.get('days_before', 0)
            
            # Calculate task due date
            task_date = event_date_obj - timedelta(days=days_before)
            task_date_str = task_date.strftime('%Y-%m-%d')
            
            # Get employees from department for assignment
            try:
                db.cursor.execute("""
                    SELECT id, name FROM tbl_employeer 
                    WHERE department = %s 
                    ORDER BY RANDOM() 
                    LIMIT 1
                """, (department,))
                employee = db.cursor.fetchone()
                
                assignee_id = employee['id'] if employee else None
                assignee_name = employee['name'] if employee else 'Unassigned'
            except:
                assignee_id = None
                assignee_name = 'Unassigned'
            
            # Create the task
            try:
                db.cursor.execute("""
                    INSERT INTO tbl_hotel_event_tasks 
                    (event_id, task_description, department, assigned_to, assigned_name, 
                     due_date, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 'Pending', %s)
                    RETURNING id
                """, (event_id, task_desc, department, assignee_id, assignee_name, 
                      task_date_str, datetime.now()))
                
                result = db.cursor.fetchone()
                if result:
                    created_task_ids.append(result['id'])
                
                db.connection.commit()
            except Exception as e:
                print(f"Error creating event task: {e}")
                db.connection.rollback()
        
        print(f"✅ Auto-assigned {len(created_task_ids)} tasks for event {event_id}")
        
    except Exception as e:
        print(f"Error in auto_assign_event_tasks: {e}")
    
    return created_task_ids


def format_event_summary(event: Dict, lang: str = 'en') -> str:
    """
    Format event details for display
    
    Args:
        event: Event dictionary
        lang: Language code
        
    Returns:
        Formatted event summary string
    """
    labels = {
        'en': {
            'name': 'Event Name',
            'type': 'Type',
            'date': 'Date',
            'time': 'Time',
            'location': 'Location',
            'guests': 'Expected Guests',
            'status': 'Status',
            'notes': 'Notes'
        },
        'sr': {
            'name': 'Naziv događaja',
            'type': 'Tip',
            'date': 'Datum',
            'time': 'Vreme',
            'location': 'Lokacija',
            'guests': 'Očekivani gosti',
            'status': 'Status',
            'notes': 'Napomene'
        }
    }
    
    l = labels.get(lang, labels['en'])
    
    summary = f"""📋 <b>{l['name']}:</b> {event.get('event_name', 'N/A')}
🎯 <b>{l['type']}:</b> {event.get('event_type', 'Custom')}
📅 <b>{l['date']}:</b> {event.get('event_date', 'N/A')}
🕐 <b>{l['time']}:</b> {event.get('event_time', 'N/A')}
📍 <b>{l['location']}:</b> {event.get('location', 'N/A')}
👥 <b>{l['guests']}:</b> {event.get('guest_count', 'N/A')}
📊 <b>{l['status']}:</b> {event.get('status', 'Scheduled')}"""
    
    if event.get('notes'):
        summary += f"\n📝 <b>{l['notes']}:</b> {event['notes']}"
    
    return summary


def format_shift_report_summary(report: Dict, lang: str = 'en') -> str:
    """
    Format shift report for display
    
    Args:
        report: Shift report dictionary
        lang: Language code
        
    Returns:
        Formatted shift report string
    """
    labels = {
        'en': {
            'arrivals': 'Guest Arrivals',
            'departures': 'Guest Departures',
            'incidents': 'Incidents',
            'maintenance': 'Maintenance Issues',
            'requests': 'Special Requests',
            'notes': 'Additional Notes'
        },
        'sr': {
            'arrivals': 'Dolasci gostiju',
            'departures': 'Odlasci gostiju',
            'incidents': 'Incidenti',
            'maintenance': 'Problemi sa održavanjem',
            'requests': 'Posebni zahtevi',
            'notes': 'Dodatne napomene'
        }
    }
    
    l = labels.get(lang, labels['en'])
    
    summary = f"""📊 <b>Shift Report Summary</b>

🛬 <b>{l['arrivals']}:</b> {report.get('guest_arrivals', 0)}
🛫 <b>{l['departures']}:</b> {report.get('guest_departures', 0)}
⚠️ <b>{l['incidents']}:</b> {report.get('incidents', 'None')}
🔧 <b>{l['maintenance']}:</b> {report.get('maintenance_issues', 'None')}
⭐ <b>{l['requests']}:</b> {report.get('special_requests', 'None')}
📝 <b>{l['notes']}:</b> {report.get('notes', 'None')}"""
    
    return summary
