#!/usr/bin/env python3
"""
Date-Range Based Telnyx Intro Call Extraction
Uses --since and --until parameters to access meetings from specific months
"""

import sqlite3
import subprocess
import json
import os
import time
from datetime import datetime
from typing import List, Tuple, Set

# Set the API key
os.environ['FELLOW_API_KEY'] = "c2e66647b10bfbc93b85cc1b05b8bc519bc61d849a09f5ac8f767fbad927dcc4"

# Target months with verified intro call counts (dates are 2025)
TARGET_MONTHS = [
    ("2025-02-01", "2025-02-28", "Feb 2025", 37),
    ("2025-08-01", "2025-08-31", "Aug 2025", 35),
    ("2025-01-01", "2025-01-31", "Jan 2025", 30), 
    ("2025-09-01", "2025-09-30", "Sep 2025", 29),
    ("2025-05-01", "2025-05-31", "May 2025", 23),
    ("2025-06-01", "2025-06-30", "Jun 2025", 21),
    ("2025-03-01", "2025-03-31", "Mar 2025", 19),
    ("2025-04-01", "2025-04-30", "Apr 2025", 16),
    ("2025-07-01", "2025-07-31", "Jul 2025", 5),
    # Also add some additional months to find more calls
    ("2025-10-01", "2025-10-31", "Oct 2025", 0),
    ("2025-11-01", "2025-11-30", "Nov 2025", 0),
    ("2025-12-01", "2025-12-31", "Dec 2025", 0),
]

def run_fellow_command(command, retries=2):
    """Run Fellow skill command with retries"""
    fellow_script = "/Users/niamhcollins/clawd/skills/fellow/skills/fellow/fellow.sh"
    
    for attempt in range(retries):
        try:
            # Rate limiting
            time.sleep(0.5)
            
            result = subprocess.run(
                [fellow_script] + command, 
                capture_output=True, 
                text=True,
                env=os.environ.copy(),
                timeout=60
            )
            
            if result.returncode == 0:
                return result.stdout, None
            else:
                error_msg = result.stderr or f"Command failed with code {result.returncode}"
                if attempt < retries - 1:
                    print(f"   🔄 Retry {attempt + 1}/{retries} after error: {error_msg}")
                    time.sleep(3)
                    continue
                return None, error_msg
                
        except subprocess.TimeoutExpired:
            if attempt < retries - 1:
                print(f"   ⏱️  Timeout, retrying {attempt + 1}/{retries}")
                time.sleep(3)
                continue
            return None, "Command timeout"
        except Exception as e:
            if attempt < retries - 1:
                print(f"   ❌ Error, retrying {attempt + 1}/{retries}: {e}")
                time.sleep(3)
                continue
            return None, str(e)
    
    return None, "All retries failed"

def load_existing_meeting_ids() -> Set[str]:
    """Load existing meeting IDs to avoid duplicates"""
    try:
        conn = sqlite3.connect("data/fellow_training_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT meeting_id FROM training_data WHERE meeting_title LIKE 'Telnyx%Intro Call%'")
        existing_ids = {row[0] for row in cursor.fetchall()}
        conn.close()
        return existing_ids
    except Exception as e:
        print(f"❌ Error loading existing meeting IDs: {e}")
        return set()

def get_meetings_for_date_range(start_date: str, end_date: str, month_name: str, expected_count: int) -> List[Tuple[str, str, str, str]]:
    """Get Telnyx intro call meetings for a specific date range"""
    print(f"\n📅 Processing {month_name} ({start_date} to {end_date})")
    print(f"   🎯 Expected: {expected_count} intro calls")
    
    # Get meetings for the specific date range
    meetings_output, error = run_fellow_command([
        'meetings', '--since', start_date, '--until', end_date, '--limit', '50'
    ])
    
    if error:
        print(f"❌ Error getting meetings for {month_name}: {error}")
        return []
    
    # Check if the response indicates no meetings
    if "_No meetings found._" in meetings_output:
        print(f"📋 No meetings found for {month_name}")
        return []
    
    meeting_data = []
    lines = meetings_output.split('\n')
    
    for line in lines:
        if '|' in line and 'Recording ID' not in line and line.count('|') >= 5:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6 and parts[5]:  # Recording ID column
                recording_id = parts[5]
                title = parts[2] if len(parts) > 2 else "Unknown"
                date = parts[3] if len(parts) > 3 else "Unknown"
                duration = parts[4] if len(parts) > 4 else "Unknown"
                
                # Filter for Telnyx intro calls (flexible matching)
                if title and ("Telnyx Intro Call" in title or ("Telnyx" in title and "Intro Call" in title)):
                    meeting_data.append((recording_id, title, date, duration))
    
    print(f"   📊 Found {len(meeting_data)} Telnyx intro calls in {month_name}")
    return meeting_data

def validate_transcript_quality(transcript: str) -> bool:
    """Validate transcript content quality"""
    if not transcript or len(transcript.strip()) < 200:
        return False
    
    # Check for meaningful content (include timestamped content but exclude headers)
    content_lines = [line.strip() for line in transcript.split('\n') 
                    if line.strip() and not line.strip().startswith('##') and not line.strip().startswith('|')]
    
    # Count lines that look like actual conversation (contain colons for speaker names)
    conversation_lines = [line for line in content_lines if ':' in line]
    
    if len(conversation_lines) < 5:
        return False
    
    return True

def extract_meeting_data(recording_id: str, title: str) -> Tuple[str, str, str, bool]:
    """Extract transcript, summary, and action items for a meeting"""
    # Get transcript
    transcript_output, transcript_error = run_fellow_command(['transcript', recording_id])
    if transcript_error or not validate_transcript_quality(transcript_output):
        return None, None, None, False
    
    # Get AI summary  
    summary_output, _ = run_fellow_command(['summary', recording_id])
    if not summary_output:
        summary_output = ""
    
    # Get action items (simplified call to avoid issues)
    action_items_output, _ = run_fellow_command(['action-items', '--title', title])
    if not action_items_output:
        action_items_output = ""
    
    return transcript_output, summary_output, action_items_output, True

def insert_meeting_data(conn, cursor, recording_id: str, title: str, transcript: str, 
                       summary: str, action_items: str, date: str, duration: str) -> bool:
    """Insert meeting data into database"""
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO training_data 
            (meeting_id, meeting_title, transcript, ai_summary, action_items, 
             date, duration, qualification_score, is_qualified, voice_ai_indicators, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            recording_id, title, transcript, summary, action_items, 
            date, duration, 1.0, True, "telnyx_intro_call", datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"   ❌ Error inserting {recording_id}: {e}")
        return False

def main():
    print("🚀 DATE-RANGE TELNYX INTRO CALL EXTRACTION")
    print("Target: Extract calls from specific months to reach 200+ total")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect("data/fellow_training_data.db")
    cursor = conn.cursor()
    
    # Get current state
    cursor.execute("SELECT COUNT(*) FROM training_data WHERE meeting_title LIKE 'Telnyx%Intro Call%'")
    initial_count = cursor.fetchone()[0]
    print(f"📊 Starting with {initial_count} existing intro calls")
    
    # Load existing meeting IDs
    existing_ids = load_existing_meeting_ids()
    print(f"📋 Loaded {len(existing_ids)} existing meeting IDs for duplicate checking")
    
    extracted_this_session = 0
    target_needed = max(0, 200 - initial_count)
    
    print(f"🎯 Need to extract {target_needed} more calls to reach 200+")
    
    # Process each month systematically
    for start_date, end_date, month_name, expected_count in TARGET_MONTHS:
        # Check if we've reached our target
        current_total = initial_count + extracted_this_session
        if current_total >= 200:
            print(f"\n🎉 TARGET ACHIEVED! Reached {current_total} intro calls!")
            break
        
        print(f"\n{'='*60}")
        meetings_for_month = get_meetings_for_date_range(start_date, end_date, month_name, expected_count)
        
        if not meetings_for_month:
            print(f"⏭️  No new meetings found for {month_name}, skipping")
            continue
        
        month_extracted = 0
        
        for i, (recording_id, title, date, duration) in enumerate(meetings_for_month, 1):
            # Skip if already processed
            if recording_id in existing_ids:
                print(f"⏭️  [{i:2d}/{len(meetings_for_month)}] {recording_id} already processed")
                continue
            
            print(f"\n🎯 [{i:2d}/{len(meetings_for_month)}] Processing: {title}")
            print(f"   📅 Date: {date} | ⏱️  Duration: {duration} | ID: {recording_id}")
            
            # Extract meeting data
            transcript, summary, action_items, success = extract_meeting_data(recording_id, title)
            
            if not success:
                print(f"   ❌ Failed to extract valid data")
                continue
            
            # Insert into database
            if insert_meeting_data(conn, cursor, recording_id, title, transcript,
                                 summary, action_items, date, duration):
                extracted_this_session += 1
                month_extracted += 1
                existing_ids.add(recording_id)  # Track to avoid duplicates
                
                current_total = initial_count + extracted_this_session
                print(f"   ✅ Successfully added to database")
                print(f"   📊 Progress: {current_total}/200+ ({current_total/200*100:.1f}%)")
                
                # Progress reporting every 25 extractions
                if extracted_this_session % 25 == 0:
                    print(f"\n📊 PROGRESS REPORT - Extracted {extracted_this_session} calls this session")
                    print(f"   📈 Total intro calls: {current_total}")
                    print(f"   🎖️  Progress: {current_total}/200+ ({current_total/200*100:.1f}%)")
                    print(f"   🚀 Remaining needed: {max(0, 200 - current_total)}")
                    print("-" * 50)
                
                # Check if we've reached our target
                if current_total >= 200:
                    print(f"\n🎉 TARGET ACHIEVED! Reached {current_total} intro calls!")
                    break
            
            # Rate limiting between extractions
            time.sleep(1)
        
        print(f"\n📈 Month Summary - {month_name}: Extracted {month_extracted} new calls")
        
        # Break if target reached
        if initial_count + extracted_this_session >= 200:
            break
    
    # Final report
    cursor.execute("SELECT COUNT(*) FROM training_data WHERE meeting_title LIKE 'Telnyx%Intro Call%'")
    final_count = cursor.fetchone()[0]
    
    print(f"\n🎉 EXTRACTION COMPLETE!")
    print(f"📊 Extracted this session: {extracted_this_session}")
    print(f"📈 Initial count: {initial_count}")
    print(f"🎯 Final count: {final_count}")
    print(f"🚀 Total growth: +{final_count - initial_count}")
    print(f"🎖️  Target status: {'✅ ACHIEVED' if final_count >= 200 else '⏳ IN PROGRESS'}")
    print(f"💾 Database: data/fellow_training_data.db")
    
    # Save results
    results = {
        'extraction_date': datetime.now().isoformat(),
        'extracted_this_session': extracted_this_session,
        'initial_count': initial_count,
        'final_count': final_count,
        'target_achieved': final_count >= 200,
        'months_processed': [month_name for _, _, month_name, _ in TARGET_MONTHS]
    }
    
    with open('data/date_range_extraction_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    conn.close()

if __name__ == "__main__":
    main()