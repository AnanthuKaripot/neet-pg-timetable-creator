from datetime import datetime, timedelta
from models import get_all_subjects_revision, create_rev_timetable_entry, insert_rev_timetable_slots

def generate_revision_timetable(start_date, end_date, selected_slots, daily_hours):
    """
    start_date: datetime (Inclusive)
    end_date: datetime (Inclusive)
    selected_slots: list of "HH:MM-HH:MM" for Weekdays.
    daily_hours: int (User input for weekdays).
    
    Logic:
    - Saturdays: Full day Revision. (What slots? Prompt says "full time_slot of that day".
      Does it mean 24h? Or reasonable day? Or ALL selected slots?
      "full time_slot of that day" usually refers to the "selected slots" but maybe ALL of them?
      Actually prompt says "time_slots(checkbox with deactivated 'okay' button...)" -> slots user picked.
      But "full time_slot" might mean user picked X slots, but on Sat/Sun we use maximize?
      "Assign all Saturdays... for weekly revision(full time_slot of that day)"
      "Assign all Sundays... for weekly grand test(full time_slot of that day)"
      AND later: "keep in mind that don't fill Saturdays and sundays (full time_slots of saturday and Sunday are for)..."
      
      Interpretation:
      On Sat/Sun, the app does NOT schedule specific subjects from the list. 
      Saturdays are marked "Weekly Revision".
      Sundays are marked "Grand Test".
      The "Hours" calculation for subjects ONLY uses Mon-Fri.
      
      Revision Hours Calculation:
      revision_days_count = Total days in revision period.
      saturdays_count = count.
      sundays_count = count.
      effective_days = revision_days_count - saturday - sunday.
      revision_hours_total = effective_days * daily_hours.
    """

    # 1. Map Days
    calendar_structure = []
    
    current_date = start_date
    effective_study_hours_avail = 0
    
    # We need to know specific slots for M-F. 
    # For Sat/Sun, since they are "block booked", we can just store the day-type, 
    # but the DB expects slots. We should probably fill the SAME selected slots 
    # with "Weekly Revision" or "Grand Test".
    
    while current_date <= end_date:
        wd = current_date.weekday()
        day_struct = {'date': current_date, 'slots': [], 'type': 'NORMAL'}
        
        if wd == 5: # Saturday
            day_struct['type'] = 'REV_SAT'
        elif wd == 6: # Sunday
            day_struct['type'] = 'GT_SUN'
        else:
            effective_study_hours_avail += daily_hours 
        
        calendar_structure.append(day_struct)
        current_date += timedelta(days=1)
        
    # 2. Calculate Subject Hours
    subjects_list = get_all_subjects_revision()
    total_weight = sum(s['weightage'] for s in subjects_list)
    
    # Calculate hours per subject
    # Logic: subject_rev_time = revision_hours * revision_percentage
    # revision_hours here is effective_study_hours_avail
    
    subject_queue = []
    
    calc_map = {}
    total_allocated = 0
    
    for sub in subjects_list:
        raw = (sub['weightage'] / total_weight) * effective_study_hours_avail
        hrs = round(raw)
        calc_map[sub['subject_name']] = hrs
        total_allocated += hrs
        
    # Adjust rounding
    diff = effective_study_hours_avail - total_allocated
    if diff != 0:
        # crude adjustment
        ks = list(calc_map.keys())
        for i in range(abs(diff)):
            if diff > 0: calc_map[ks[i%len(ks)]] += 1
            else: 
                if calc_map[ks[i%len(ks)]] > 0: calc_map[ks[i%len(ks)]] -= 1

    # 3. Build Queue with 4-hour buffers
    # "after one subject give 4 hours... for subject revision"
    # This implies: [Sub A * hours] -> [Buffer * 4] -> [Sub B * hours]...
    # BUT wait, does this 4 hours come out of `effective_study_hours_avail`?
    # The formula `subject_rev_time = revision_hours * revision_weighage` 
    # uses the TOTAL available time. If we insert buffers, we exceed time.
    # Interpretation: The Prompt logic might be flawed or I need to Subtract buffers first.
    # "in backend no_of_days = ... . And we create slots accordint to this total time"
    # Prompt says: "Assign subject_rev_hours... after one subject give 4 hours... for subject revision".
    
    # If I just insert 4 hours, I will run out of days.
    # Maybe the "4 hours" are PART OF the subject's allocated time? 
    # "give 4 hours... for subject revision" sounds like a specific activity.
    # Alternatives:
    # A) Subtract (19 subjects * 4 hours = 76 hours) from Total Available first. Then distribute rest.
    # B) Just append it and overflow (users DATE will be exceeded? No, we work within date).
    
    # Given "logic - in backend ... equations that generate time needed", 
    # and the specific formula provided: `revision_hours = (days - sat - sun) * daily_hours`
    # AND `subject_rev_time = revision_hours * revision_weighage`.
    # This formula allocates 100% of the time to Subjects.
    # If I add valid "4 hour buffers" on top, it breaks the math.
    
    # Decision: I will Subtract the total buffer time from `revision_hours` BEFORE calculating subject split.
    # If `revision_hours` is too low to support buffers, we might zero them or reduce.
    
    num_subjects = len(subjects_list)
    total_buffer_needed = num_subjects * 4
    
    available_for_subjects = effective_study_hours_avail - total_buffer_needed
    
    if available_for_subjects < 0:
        # Edge case: Very short revision period. 
        # Fallback: Ignore buffer or reduce it.
        # Let's try to scale down buffer? Or just ignore calculation and fill until full?
        # Let's stick to the prompt's Allocation Formula strictness first?
        # Re-reading prompt: "after one subject give 4 hours... for subject revision"
        # It comes AFTER the allocation description.
        # Let's assume the user wants the allocation formula to determine "Teaching/Reading Time", 
        # and the 4 hours is "Self Revision". 
        # I will use the "Subtract first" method to ensure fit.
        pass
    else:
        # Recalculate based on reduced time
        total_allocated = 0
        for sub in subjects_list:
            raw = (sub['weightage'] / total_weight) * available_for_subjects
            hrs = round(raw)
            calc_map[sub['subject_name']] = hrs
            total_allocated += hrs
            
        # Adjust rounding on the 'available_for_subjects'
        diff = available_for_subjects - total_allocated
        # ... adjust ...
        if diff != 0:
            ks = list(calc_map.keys())
            for i in range(abs(diff)):
                if diff > 0: calc_map[ks[i%len(ks)]] += 1
                else: 
                     if calc_map[ks[i%len(ks)]] > 0: calc_map[ks[i%len(ks)]] -= 1

    # Build the final Flat Queue
    # Order: As per list? Prompt lists groups (Pre/Para/Clin).
    # We will iterate `subjects_list` (which is ordered by DB insert order).
    
    for sub in subjects_list:
        s_name = sub['subject_name']
        hrs = calc_map.get(s_name, 0)
        
        # Add Subject Slots
        for _ in range(hrs):
            subject_queue.append(s_name)
            
        # Add 4 Buffer Slots (if we had space, or if we force it? 
        # If we subtracted, we have space. 
        # If negative available, we skip this step or the previous step produced 0 hours).
        if available_for_subjects >= 0:
            for _ in range(4):
                subject_queue.append(f"{s_name} (Subject Test)")

    # 4. Fill Calendar
    
    final_output_slots = []
    
    queue_idx = 0
    total_q = len(subject_queue)
    
    for day in calendar_structure:
        d_str = day['date'].strftime('%Y-%m-%d')
        d_type = day['type']
        
        # For M-F, we use selected_slots
        # For Sat/Sun, prompt says "full time_slot".
        # We will assume that means "The same set of slots as selected", but ALL filled with the special event.
        # Because we don't have "other" slots defined. 
        # Unless "full time_slot" means 24 hours? Unlikely for a study plan.
        # I'll stick to `selected_slots`.
        
        if d_type == 'REV_SAT':
            for s_time in selected_slots:
                start_t, end_t = s_time.split('-')
                final_output_slots.append({
                    'date': d_str,
                    'start_time': start_t,
                    'end_time': end_t,
                    'subject': 'Weekly Revision (Saturday)'
                })
        elif d_type == 'GT_SUN':
             for s_time in selected_slots:
                start_t, end_t = s_time.split('-')
                final_output_slots.append({
                    'date': d_str,
                    'start_time': start_t,
                    'end_time': end_t,
                    'subject': 'Grand Test (Sunday)'
                })
        else:
            # Normal Day
            for s_time in selected_slots:
                start_t, end_t = s_time.split('-')
                
                subj_content = "Free/Buffer"
                if queue_idx < total_q:
                    subj_content = subject_queue[queue_idx]
                    queue_idx += 1
                
                final_output_slots.append({
                    'date': d_str,
                    'start_time': start_t,
                    'end_time': end_t,
                    'subject': subj_content
                })

    # Save
    rev_id = create_rev_timetable_entry("Generated Revision", "Standard Revision")
    insert_rev_timetable_slots(final_output_slots, rev_id)
    
    return rev_id
