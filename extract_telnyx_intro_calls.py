#!/usr/bin/env python3
"""
Telnyx Intro Call Data Extraction for Business Context Analysis
Extract 140+ additional Telnyx intro call transcripts to reach 200+ total records
"""

import sqlite3
import subprocess
import json
import os
import sys
import re
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Set

# Set the API key
os.environ['FELLOW_API_KEY'] = "c2e66647b10bfbc93b85cc1b05b8bc519bc61d849a09f5ac8f767fbad927dcc4"

# Target months with verified intro call counts (from Feb to Sep 2026)
TARGET_MONTHS = [
    ("2026-02", 37),  # Feb 2026
    ("2026-08", 35),  # Aug 2026
    ("2026-01", 30),  # Jan 2026
    ("2026-09", 29),  # Sep 2026
    ("2026-05", 23),  # May 2026
    ("2026-06", 21),  # Jun 2026
    ("2026-03", 19),  # Mar 2026
    ("2026-04", 16),  # Apr 2026
    ("2026-07", 5),   # Jul 2026
]

def run_fellow_command(command, retries=3):
    """Run Fellow skill command with rate limiting and retries"""
    fellow_script = "/Users/niamhcollins/clawd/skills/fellow/skills/fellow/fellow.sh"
    
    for attempt in range(retries):
        try:
            # Rate limiting - small delay between API calls
            time.sleep(0.5)
            
            result = subprocess.run(
                [fellow_script] + command.split(), 
                capture_output=True, 
                text=True,
                env=os.environ.copy(),
                timeout=30  # 30 second timeout
            )
            
            if result.returncode == 0:
                return result.stdout, None
            else:
                error_msg = result.stderr or f"Command failed with code {result.returncode}"
                if attempt < retries - 1:
                    print(f"   🔄 Retry {attempt + 1}/{retries} after error: {error_msg}")
                    time.sleep(2)  # Wait before retry
                    continue
                return None, error_msg
                
        except subprocess.TimeoutExpired:
            if attempt < retries - 1:
                print(f"   ⏱️  Timeout, retrying {attempt + 1}/{retries}")
                time.sleep(2)
                continue
            return None, "Command timeout"
        except Exception as e:
            if attempt < retries - 1:
                print(f"   ❌ Error, retrying {attempt + 1}/{retries}: {e}")
                time.sleep(2)
                continue
            return None, str(e)
    
    return None, "All retries failed"

def load_existing_meeting_ids() -> Set[str]:
    """Load existing meeting IDs to avoid duplicates"""
    try:
        conn = sqlite3.connect("data/fellow_training_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT meeting_id FROM training_data WHERE meeting_title LIKE 'Telnyx Intro Call%'")
        existing_ids = {row[0] for row in cursor.fetchall()}
        conn.close()
        print(f"📋 Found {len(existing_ids)} existing Telnyx intro call records")
        return existing_ids
    except Exception as e:
        print(f"❌ Error loading existing meeting IDs: {e}")
        return set()

def get_meetings_for_month(year_month: str, expected_count: int) -> List[Tuple[str, str, str, str]]:
    """Get Telnyx intro call meetings for a specific month"""
    print(f"\n🗓️  Processing {year_month} (expected: {expected_count} intro calls)")
    
    # Get all meetings with a larger limit (Fellow API doesn't support month filtering)
    meetings_output, error = run_fellow_command(f"meetings --limit 1000")
    
    if error or not meetings_output:
        print(f"❌ Error getting meetings: {error}")
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
                
                # Filter for Telnyx intro calls and specific month
                if title and "Telnyx Intro Call" in title and date.startswith(year_month):
                    meeting_data.append((recording_id, title, date, duration))
    
    print(f"   📊 Found {len(meeting_data)} Telnyx intro calls in {year_month}")
    return meeting_data

def validate_transcript_quality(transcript: str) -> bool:
    """Validate transcript content quality"""
    if not transcript or len(transcript.strip()) < 200:
        return False
    
    # Check for meaningful content (not just timestamps or system messages)
    content_lines = [line.strip() for line in transcript.split('\n') 
                    if line.strip() and not line.strip().startswith('[') and not line.strip().startswith('#')]
    
    if len(content_lines) < 10:
        return False
    
    # Check for conversation elements
    conversation_indicators = [':', 'said', 'asked', 'replied', 'mentioned', 'discussed']
    has_conversation = any(indicator in transcript.lower() for indicator in conversation_indicators)
    
    return has_conversation

def extract_meeting_data(recording_id: str, title: str, date: str, duration: str) -> Tuple[str, str, str, bool]:
    """Extract transcript, summary, and action items for a meeting"""
    print(f"   📥 Extracting data for {recording_id}")
    
    # Get transcript
    transcript_output, transcript_error = run_fellow_command(f"transcript {recording_id}")
    if transcript_error or not validate_transcript_quality(transcript_output):
        print(f"   ❌ Invalid/missing transcript")
        return None, None, None, False
    
    # Get AI summary  
    summary_output, _ = run_fellow_command(f"summary {recording_id}")
    if not summary_output:
        summary_output = ""
    
    # Get action items
    action_items_output, _ = run_fellow_command(f"action-items --title \"{title}\"")
    if not action_items_output:
        action_items_output = ""
    
    print(f"   ✅ Extracted {len(transcript_output)} chars transcript, {len(summary_output)} chars summary")
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

def report_progress(extracted_count: int, total_target: int, current_total: int):
    """Report extraction progress"""
    print(f"\n📊 PROGRESS REPORT")
    print(f"   🎯 Extracted this session: {extracted_count}")
    print(f"   📈 Current database total: {current_total}")
    print(f"   🎖️  Progress to 200+: {current_total}/200+ ({current_total/200*100:.1f}%)")
    print(f"   🚀 Remaining needed: {max(0, 200 - current_total)}")
    print("-" * 50)

def main():
    print("🚀 TELNYX INTRO CALL EXTRACTION")
    print("Target: Extract 140+ additional calls to reach 200+ total")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect("data/fellow_training_data.db")
    cursor = conn.cursor()
    
    # Get current state
    cursor.execute("SELECT COUNT(*) FROM training_data WHERE meeting_title LIKE 'Telnyx Intro Call%'")
    initial_count = cursor.fetchone()[0]
    print(f"📊 Starting with {initial_count} existing intro calls")
    
    # Load existing meeting IDs
    existing_ids = load_existing_meeting_ids()
    
    extracted_this_session = 0
    target_extraction = 200 - initial_count
    
    print(f"🎯 Need to extract {target_extraction} more calls to reach 200+")
    
    # Process each month systematically
    for month, expected_count in TARGET_MONTHS:
        if extracted_this_session >= target_extraction:
            print(f"🎉 Target reached! Extracted {extracted_this_session} calls")
            break
        
        print(f"\n{'='*50}")
        meetings_for_month = get_meetings_for_month(month, expected_count)
        
        if not meetings_for_month:
            print(f"⏭️  No meetings found for {month}, skipping")
            continue
        
        month_extracted = 0
        
        for recording_id, title, date, duration in meetings_for_month:
            # Skip if already processed
            if recording_id in existing_ids:
                print(f"   ⏭️  {recording_id} already processed, skipping")
                continue
            
            print(f"\n🎯 Processing: {title}")
            print(f"   📅 Date: {date} | ⏱️  Duration: {duration}")
            
            # Extract meeting data
            transcript, summary, action_items, success = extract_meeting_data(
                recording_id, title, date, duration
            )
            
            if not success:
                continue
            
            # Insert into database
            if insert_meeting_data(conn, cursor, recording_id, title, transcript,
                                 summary, action_items, date, duration):
                extracted_this_session += 1
                month_extracted += 1
                existing_ids.add(recording_id)  # Track to avoid duplicates
                
                print(f"   ✅ Successfully added to database")
                
                # Progress reporting every 20-30 extractions
                if extracted_this_session % 25 == 0:
                    cursor.execute("SELECT COUNT(*) FROM training_data WHERE meeting_title LIKE 'Telnyx Intro Call%'")
                    current_total = cursor.fetchone()[0]
                    report_progress(extracted_this_session, target_extraction, current_total)
                
                # Check if we've reached our target
                if initial_count + extracted_this_session >= 200:
                    print(f"\n🎉 TARGET ACHIEVED! Reached 200+ intro calls!")
                    break
            
            # Rate limiting between extractions
            time.sleep(1)
        
        print(f"📈 Extracted {month_extracted} calls from {month}")
    
    # Final report
    cursor.execute("SELECT COUNT(*) FROM training_data WHERE meeting_title LIKE 'Telnyx Intro Call%'")
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
        'months_processed': [month for month, _ in TARGET_MONTHS]
    }
    
    with open('data/telnyx_extraction_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    conn.close()

if __name__ == "__main__":
    main()