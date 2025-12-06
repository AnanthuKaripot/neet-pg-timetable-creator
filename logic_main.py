from datetime import datetime, timedelta
import math
import random
from models import get_all_subjects_pyq, create_timetable_entry, insert_timetable_slots

def generate_time_slots(start_time_str, end_time_str):
    # This might be useful if we needed to autogenerate slots, 
    # but the user selects specific slots.
    pass

def calculate_hours_per_subject(available_hours, subjects):
    total_weightage = sum(s['weightage'] for s in subjects)
    
    subject_hours = {}
    for s in subjects:
        # Calculate raw hours
        hours = (s['weightage'] / total_weightage) * available_hours
        # Rounding logic could be complex, for now simple round
        subject_hours[s['subject_name']] = round(hours)
    
    # Adjust for rounding errors to match available_hours exactly
    allocated_hours = sum(subject_hours.values())
    diff = available_hours - allocated_hours
    
    # Simple fix just add/sub from the heaviest subject or distribute
    # We will just add to the first few subjects
    if diff != 0:
        keys = list(subject_hours.keys())
        for i in range(abs(diff)):
            if diff > 0:
                subject_hours[keys[i % len(keys)]] += 1
            else:
                if subject_hours[keys[i % len(keys)]] > 0:
                     subject_hours[keys[i % len(keys)]] -= 1
                
    return subject_hours

def get_slots_for_day(date_obj, selected_slots, gt_freq, is_gt_day):
    """
    Returns a list of (start, end) tuples for the day based on rules.
    gt_freq: 'once_weekly' or 'twice_weekly'
    """
    
    final_slots = []
    
    # selected_slots example: ["04:00-05:00", "05:00-06:00", ...]
    # We need to parse them into start and end times
    
    # Check if this is a GT day and we need to reserve slots
    is_sunday = date_obj.weekday() == 6
    
    limit_gt_slots = False
    
    if is_gt_day:
        # Reserve 1-2pm, 2-3pm, 3-4pm, 4-5pm for GT
        # Meaning these slots, if selected by user, are now assigned to "Grand Test"
        # and NOT available for studying subjects.
        # Wait, the prompt says "Reserve slot ... for gt".
        pass

    day_slots = []
    
    gt_reserved_times = ["13:00-14:00", "14:00-15:00", "15:00-16:00", "16:00-17:00"]
    # 1-2pm is 13:00-14:00
    
    normalized_slots = []
    for s in selected_slots:
        # format: "4-5am" or "1-2pm" or "12-1pm"
        # We need a standard format for comparison. 
        # Let's assume the input sends standard strings or we normalize them in App.
        # For now assuming input is like "04:00-05:00" for simplicity in backend,
        # frontend will map.
        normalized_slots.append(s)

    for slot in normalized_slots:
        # Check collision with GT
        # For now, let's just assume we label the slot subject as 'Grand Test' if it matches
        if is_gt_day and slot in gt_reserved_times:
             day_slots.append({'time': slot, 'type': 'GT'})
        else:
             day_slots.append({'time': slot, 'type': 'STUDY'})
             
    return day_slots

def generate_main_timetable(start_date, end_date, selected_slots, gt_freq, method, revision_days):
    """
    start_date, end_date: datetime objects
    selected_slots: list of strings "HH:MM-HH:MM" (24h format preferred internally)
    gt_freq: 'once_weekly' or 'twice_weekly'
    method: 'subject_completion_wise' or 'mixed'
    revision_days: int
    """
    
    total_duration_days = (end_date - start_date).days + 1
    # logic_main now assumes 'start_date' and 'end_date' ARE the Main Phase duration.
    # The check for total > 60 is done in app.py.
    
    # We use end_date directly as the end of main phase.
    main_end_date = end_date
    
    # Calculate days for iteration
    # (Previously we calculated main_days from total - revision, but passed explicit dates)
    pass
    # 2. Calculate TOTAL available study hours
    # We need to iterate days to account for GTs
    
    daily_hours = len(selected_slots)
    total_study_hours = 0
    calendar_structure = [] # List of {date: date, slots: []}
                             # slots: [{'start': '...', 'end': '...', 'status': 'open'/'gt'}]
    
    gt_reserved_set = {"13:00-14:00", "14:00-15:00", "15:00-16:00", "16:00-17:00"}
    
    current_date = start_date
    gt_counter = 0
    
    while current_date <= main_end_date:
        is_sunday = current_date.weekday() == 6
        is_gt_day = False
        
        if is_sunday:
            if gt_freq == 'once_weekly':
                is_gt_day = True
            elif gt_freq == 'twice_weekly':
                # Alternate Sundays. Need to know which Sunday this is.
                # Assuming first Sunday is GT? Or Start counting?
                # Prompt: "reserve_time_slot ... on alternate Sundays"
                # Let's assume every 2nd Sunday? Or just Odd/Even index of Sundays?
                # "Alternate Sundays starting from first applicable?"
                # Let's stick to simplest: Alternate Sundays usually means every other. 
                # Let's count Sundays since start.
                days_since_start = (current_date - start_date).days
                # Find how many sundays passed.
                # This could be tricky. Let's just track it manually.
                 # Actually, simpler: if it's a Sunday, increment a sunday_counter.
                 # If counter % 2 != 0 (1st, 3rd...), it is GT day?
                 # Or use week number. 
                 # Let's use a global sunday tracker.
                pass 
                
        # To strictly follow "Alternate Sundays", we need a persistent counter or logic.
        # Let's recalculate in the loop.
        
        day_struct = {'date': current_date, 'slots': []}
        
        # Determine if GT day
        # For 'twice_weekly', prompt says "alternate Sundays". 
        # I'll default to: First Sunday is GT, next is not, etc.
        if is_sunday:
             # Calculate Sunday Index
             # ... getting sunday index in the range ...
             pass
    
        days_from_start = (current_date - start_date).days
        
        # Check GT condition
        is_this_day_gt = False
        if is_sunday:
             if gt_freq == 'once_weekly':
                 is_this_day_gt = True
             elif gt_freq == 'twice_weekly':
                 # Calculate if it's an "alternate" Sunday
                 # We need to count how many Sundays have occurred properly.
                 # Method: calculate number of Sundays from start_date up to current_date
                 sundays_count = 0
                 temp = start_date
                 while temp <= current_date:
                     if temp.weekday() == 6:
                         sundays_count += 1
                     temp += timedelta(days=1)
                 
                 # if sundays_count is 1, 3, 5... (Odd) -> GT
                 if sundays_count % 2 != 0:
                     is_this_day_gt = True
                 else:
                     is_this_day_gt = False
        
        day_study_hours = 0
        
        for slot_time in selected_slots:
            slot_entry = {'time': slot_time, 'subject': None}
            
            if is_this_day_gt and slot_time in gt_reserved_set:
                slot_entry['subject'] = 'Grand Test'
                # Do NOT increment study hour
            else:
                # Available for allocation
                slot_entry['subject'] = 'OPEN' 
                day_study_hours += 1
            
            day_struct['slots'].append(slot_entry)
            
        total_study_hours += day_study_hours
        calendar_structure.append(day_struct)
        current_date += timedelta(days=1)


    # 3. Allocating Subjects
    full_subjects_list = get_all_subjects_pyq()
    subject_hours_map = calculate_hours_per_subject(total_study_hours, full_subjects_list)
    
    # Flatten subjects into a list of "Hour units" to populate
    # e.g. ["Anatomy", "Anatomy", "Biochem"...]
    
    allocation_queue = []
    
    # Order matters for 'subject_completion_wise': use the order from DB (Pre/Para/Clin groups implicitly ordered by ID usually or list def)
    # The prompt defines list order. We should respect that.
    # subject_hours_map keys are subject names. We iterate `full_subjects_list` to preserve order.
    
    for subj in full_subjects_list:
        name = subj['subject_name']
        hours = subject_hours_map.get(name, 0)
        for _ in range(hours):
            allocation_queue.append(name)
            
    if method == 'mixed':
        # "Mixed: Randomly assign... if time allows use two slots continous"
        # Re-organize allocation_queue into blocks of 1 or 2
        # Then shuffle.
        
        # 1. Group into chunks
        chunks = []
        i = 0
        while i < len(allocation_queue):
            current_sub = allocation_queue[i]
            # Try to grab next
            if i + 1 < len(allocation_queue) and allocation_queue[i+1] == current_sub:
                chunks.append([current_sub, current_sub]) # 2 hour block
                i += 2
            else:
                chunks.append([current_sub]) # 1 hour block
                i += 1
        
        # 2. Shuffle chunks
        random.shuffle(chunks)
        
        # 3. Flatten back to queue
        allocation_queue = [item for sublist in chunks for item in sublist]


    # 4. Fill the calendar
    
    # Iterator for allocation
    queue_idx = 0
    total_slots_to_fill = len(allocation_queue)
    
    final_output_slots = []
    
    for day in calendar_structure:
        slots = day['slots']
        current_date_str = day['date'].strftime('%Y-%m-%d')
        
        # If 'mixed', we might want to respect the chunking continuity ON THE DAY too.
        # But our queue is already flattened chunks.
        # Problem: If a 2-hr chunk lands on a day boundary or a GT break, it splits.
        # However, the prompt says "if time allows use two slots...".
        # Mapping strict 2-hr blocks to a fixed grid with gaps (GTs) is complex packing.
        # Simple approach: Since we pre-shuffled chunks, just pouring them into open slots
        # preserves 2-hr sequences mostly, EXCEPT when a day ends or GT block intervenes.
        # That logic is acceptable for "if time allows".
        
        for s in slots:
            start_t, end_t = s['time'].split('-') 
            # Note: s['time'] assumed "HH:MM-HH:MM"
            
            if s['subject'] == 'Grand Test':
                final_output_slots.append({
                    'date': current_date_str,
                    'start_time': start_t,
                    'end_time': end_t,
                    'subject': 'Grand Test'
                })
            else:
                if queue_idx < total_slots_to_fill:
                    subj = allocation_queue[queue_idx]
                    final_output_slots.append({
                        'date': current_date_str,
                        'start_time': start_t,
                        'end_time': end_t,
                        'subject': subj
                    })
                    queue_idx += 1
                else:
                    # Spare slots (rounding excess available vs required)
                    final_output_slots.append({
                        'date': current_date_str,
                        'start_time': start_t,
                        'end_time': end_t,
                        'subject': 'Buffer/Free'
                    })

    # Save to DB
    timetable_id = create_timetable_entry("Generated Timetable", f"Method: {method}, GT: {gt_freq}")
    insert_timetable_slots(final_output_slots, timetable_id)
    
    return timetable_id

