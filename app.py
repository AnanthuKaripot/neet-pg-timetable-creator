from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, date, timedelta
import sqlite3
import models
from logic_main import generate_main_timetable
from logic_revision import generate_revision_timetable
from models import get_db_connection, TIMETABLE_DB, REV_TIMETABLE_DB

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    # 1. Extract Inputs
    from_date_str = request.form['from_date']
    to_date_str = request.form['to_date']
    revision_days = int(request.form.get('revision_days', 0))
    daily_hours = int(request.form['daily_hours'])
    selected_slots = request.form.getlist('time_slots') 
    # Checkbox name="time_slots", returns list
    
    gt_freq = request.form.get('grant_test_frequency', 'once_weekly')
    method = request.form.get('method', 'subject_completion_wise')
    
    # Simple validation
    if not from_date_str or not to_date_str:
        return "Dates required", 400
        
    start_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    
    total_days = (end_date - start_date).days + 1
    
    main_timetable_id = None
    rev_timetable_id = None
    
    # 2. Logic Dispatch
    # Logic: "if no_of_days_norev < 60 days then revision_days = no_of_days = no_of_days_norev"
    # AND "pyq_based which is triggered only when days are more than 60"
    
    if total_days <= 60:
        # ONLY Revision Timetable
        # Revision runs from from_date to to_date
        # Logic says: "if no_of_days_norev < 60 ... no_of_days = no_of_days_norev - revision_days" ??
        # Wait, prompt: "if no_of_days_norev <= 60... then no_of_days = no_of_days_norev"
        # "else ... no_of_days = no_of_days_norev - revision_days"
        # AND "we have two timetables... pyq_based ... triggered only when days > 60"
        # "then the revison timetable which occurs if days <= 60 ... OR in < 60 within the dates specified"
        
        # Scenario A: <= 60 days. 
        # Main Timetable: Skipped.
        # Revision Timetable: Covers entire period? dates specified.
        # Yes.
        
        rev_timetable_id = generate_revision_timetable(start_date, end_date, selected_slots, daily_hours)
        
    else:
        # Scenario B: > 60 days.
        # Main Period: Start -> (Start + (Total - RevDays) - 1)
        # Revision Period: (Start + (Total - RevDays)) -> (End - 1)
        # Prompt: "revision_date_start = from_date + no_of_days" (where no_of_days is the REDUCED main days)
        # "Revision_date_end = to_date - 1"
        
        main_days_count = total_days - revision_days
        
        main_end = start_date + timedelta(days=main_days_count - 1)
        rev_start = main_end + timedelta(days=1)
        rev_end = end_date # Prompt says "to_date - 1". Usually implicit if to_date is exam day.
                           # Let's check prompt "to_date(calendar) ... Revision_date_end = to_date - 1"
                           # So actual schedule ends day before to_date? 
                           # I will follow "to_date - 1" literally.
        rev_end_actual = end_date - timedelta(days=1)
        
        # Generate Main
        main_timetable_id = generate_main_timetable(start_date, main_end, selected_slots, gt_freq, method, revision_days)
        
        # Generate Revision
        rev_timetable_id = generate_revision_timetable(rev_start, rev_end_actual, selected_slots, daily_hours)

    # 3. Retrieve Data for Display
    
    # Process for Matrix View
    def process_data_matrix(timetable_id, is_revision=False):
        if not timetable_id:
            return {'days': [], 'summary': {}}
            
        table = 'TimetableSlots'
        id_col = 'timetable_id' if not is_revision else 'rev_timetable_id'
        
        with get_db_connection(models.TIMETABLE_DB if not is_revision else models.REV_TIMETABLE_DB) as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {table} WHERE {id_col} = ? ORDER BY slot_date, start_time", (timetable_id,))
            rows = cur.fetchall()
            
            # Summary
            counts = {}
            for r in rows:
                s = r['subject']
                # Clean up subject name for summary if needed (e.g. remove " (Subject Test)")
                # But for now keep distinct
                if s not in counts: counts[s] = 0
                counts[s] += 1
            
            sorted_summary = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))
            
            # Matrix Transformation
            # List of Day Objects:
            # {
            #    'date_display': 'YYYY-MM-DD (Day)',
            #   'is_special': Bool,
            #   'special_label': 'Grand Test',
            #   'slots': { 'start_time-end_time': 'Subject' }
            # }
            
            matrix_days = []
            current_date = None
            current_day_obj = None
            
            for r in rows:
                r_dict = dict(r)
                d_str = r_dict['slot_date']
                
                if d_str != current_date:
                    if current_day_obj:
                        matrix_days.append(current_day_obj)
                    
                    dt = datetime.strptime(d_str, '%Y-%m-%d')
                    day_name = dt.strftime('%A')
                    friendly_date = f"{d_str} ({day_name})"
                    
                    current_day_obj = {
                        'date_display': friendly_date,
                        'is_special': False,
                        'special_label': '',
                        'slots_map': {}
                    }
                    current_date = d_str
                
                # Check for Special Events (GT / Weekly Revision) that span row
                subj = r_dict['subject']
                time_key = f"{r_dict['start_time']}-{r_dict['end_time']}"
                
                # Check logic for merging
                # If subject contains "Grand Test" or "Weekly Revision", typically it's the whole day
                # EXCEPT if it is a specific slot in a mixed day?
                # current logic: GT days are fully GT (except maybe mixed 1-5pm logic which was replaced by full GT in revision?)
                # In Main Timetable: GT is only 1-5pm on Sundays.
                # In Revision: GT is ALL DAY.
                
                if is_revision:
                    if "Grand Test" in subj:
                        current_day_obj['is_special'] = True
                        current_day_obj['special_label'] = "Grand Test"
                    elif "Weekly Revision" in subj:
                        current_day_obj['is_special'] = True
                        current_day_obj['special_label'] = "Weekly Revision"
                
                current_day_obj['slots_map'][time_key] = subj
                
            if current_day_obj:
                matrix_days.append(current_day_obj)
                
            return {'days': matrix_days, 'summary': sorted_summary}

    main_data = process_data_matrix(main_timetable_id, is_revision=False)
    rev_data = process_data_matrix(rev_timetable_id, is_revision=True)
    
    # Calculate Duration Stats
    stats = {}
    total_d = (end_date - start_date).days + 1
    stats['total_days'] = total_d
    
    if total_days <= 60:
         stats['main_days'] = 0
         stats['rev_days'] = total_d
    else:
         stats['main_days'] = (main_end - start_date).days + 1
         stats['rev_days'] = (rev_end_actual - rev_start).days + 1 
         # Note: rev_end_actual is inclusive.

    # We need to pass the "Selected Slots" to the template to render columns
    # But wait, request.form.getlist('time_slots') is what user submitted.
    # We should normalize them.
    # Selected slots format: "HH:MM-HH:MM" (e.g. 04:00-05:00)
    # This matches the dictionary keys in slots_map.
    cols = sorted(selected_slots) 

    MOTIVATIONAL_QUOTES = [
        "Believe you can and you're halfway there.",
        "Your only limit is your mind.",
        "Push yourself, because no one else is going to do it for you.",
        "Great things never come from comfort zones.",
        "Dream it. Wish it. Do it.",
        "Success doesn’t just find you. You have to go out and get it.",
        "The harder you work for something, the greater you’ll feel when you achieve it.",
        "Dream bigger. Do bigger.",
        "Don’t stop when you’re tired. Stop when you’re done.",
        "Wake up with determination. Go to bed with satisfaction.",
        "Do something today that your future self will thank you for.",
        "Little things make big days.",
        "It’s going to be hard, but hard does not mean impossible.",
        "Don’t wait for opportunity. Create it.",
        "Sometimes we’re tested not to show our weaknesses, but to discover our strengths.",
        "The key to success is to focus on goals, not obstacles.",
        "Dream it. Believe it. Build it.",
        "Motivation is what gets you started. Habit is what keeps you going.",
        "A little progress each day adds up to big results.",
        "There is no substitute for hard work.",
        "What you do today can improve all your tomorrows.",
        "Set a goal that makes you want to jump out of bed in the morning.",
        "You don’t have to be great to start, but you have to start to be great.",
        "Success is what happens after you have survived all your mistakes.",
        "Reviewing is the key to retention.",
        "Consistancy is the only cheat code.",
        "The pain you feel today will be the strength you feel tomorrow.",
        "Focus on the process, not just the outcome.",
        "Every pro was once an amateur.",
        "Your potential is endless."
    ]

    return render_template('timetable.html', main=main_data, rev=rev_data, stats=stats, time_cols=cols, quotes=MOTIVATIONAL_QUOTES)

if __name__ == '__main__':
    app.run()
