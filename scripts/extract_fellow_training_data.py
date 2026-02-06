#!/usr/bin/env python3
"""
Fellow.ai Data Extraction for ML Training
Extract real transcripts and AI summaries using Fellow skill
"""

import sqlite3
import subprocess
import json
import os
import sys
import re
from datetime import datetime

# Set the API key
os.environ['FELLOW_API_KEY'] = "c2e66647b10bfbc93b85cc1b05b8bc519bc61d849a09f5ac8f767fbad927dcc4"

def run_fellow_command(command):
    """Run Fellow skill command and return output"""
    fellow_script = "/Users/niamhcollins/clawd/skills/fellow/skills/fellow/fellow.sh"
    try:
        result = subprocess.run(
            [fellow_script] + command.split(), 
            capture_output=True, 
            text=True,
            env=os.environ.copy()
        )
        return result.stdout, result.stderr
    except Exception as e:
        print(f"Error running Fellow command: {e}")
        return None, str(e)

def create_training_database():
    """Create the training database with proper schema"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/fellow_training_data.db")
    
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT UNIQUE,
            meeting_title TEXT,
            transcript TEXT,
            ai_summary TEXT,
            action_items TEXT,
            date TEXT,
            duration TEXT,
            qualification_score REAL,
            is_qualified BOOLEAN,
            voice_ai_indicators TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def extract_meeting_ids():
    """Get meeting IDs from Fellow.ai"""
    print("🔄 Getting recent meetings from Fellow.ai...")
    
    meetings_output, error = run_fellow_command("meetings --limit 50")
    if error or not meetings_output:
        print(f"Error getting meetings: {error}")
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
                meeting_data.append((recording_id, title, date, duration))
    
    return meeting_data

def score_voice_ai_prospect(transcript, summary="", action_items=""):
    """Advanced Voice AI qualification scoring"""
    
    # Combine all text for analysis
    all_text = f"{transcript} {summary} {action_items}".lower()
    
    # Voice AI keywords with weights
    voice_ai_keywords = {
        "voice ai": 3.0,
        "ai agent": 2.5,
        "voice agent": 2.5,
        "phone ai": 2.0,
        "speech ai": 2.0,
        "conversation ai": 2.0,
        "voice bot": 2.0,
        "ivr": 1.5,
        "voice assistant": 2.0,
        "phone automation": 2.0,
        "call center ai": 2.5,
        "inbound ai": 2.0
    }
    
    # Integration keywords
    integration_keywords = {
        "api": 1.0,
        "integration": 1.5,
        "webhook": 1.0,
        "sdk": 1.0,
        "embed": 1.0,
        "platform": 1.0,
        "connect": 1.0,
        "integrate": 1.5
    }
    
    # Scale indicators
    scale_keywords = {
        "volume": 1.0,
        "calls per": 1.5,
        "thousands": 1.5,
        "scale": 1.0,
        "enterprise": 1.5,
        "production": 1.0,
        "business": 0.5,
        "customers": 1.0
    }
    
    # Calculate weighted scores
    voice_score = sum(weight for keyword, weight in voice_ai_keywords.items() if keyword in all_text)
    integration_score = sum(weight for keyword, weight in integration_keywords.items() if keyword in all_text)
    scale_score = sum(weight for keyword, weight in scale_keywords.items() if keyword in all_text)
    
    total_score = voice_score + integration_score * 0.7 + scale_score * 0.5
    
    # Normalize to 0-1.5 range (allowing for very high scores)
    normalized_score = min(1.5, total_score / 10.0)
    
    # Collect indicators found
    indicators = []
    for keyword, weight in voice_ai_keywords.items():
        if keyword in all_text:
            indicators.append(f"voice_ai:{keyword}")
    
    for keyword, weight in integration_keywords.items():
        if keyword in all_text:
            indicators.append(f"integration:{keyword}")
            
    for keyword, weight in scale_keywords.items():
        if keyword in all_text:
            indicators.append(f"scale:{keyword}")
    
    return normalized_score, indicators

def main():
    print("🚀 FELLOW.AI ML TRAINING DATA EXTRACTION")
    print("=" * 50)
    
    # Create database
    print("📊 Creating training database...")
    conn = create_training_database()
    cursor = conn.cursor()
    
    # Get meetings
    meeting_data = extract_meeting_ids()
    print(f"📋 Found {len(meeting_data)} meetings to extract")
    
    if not meeting_data:
        print("❌ No meetings found!")
        return
    
    extracted_count = 0
    qualified_count = 0
    
    for recording_id, title, date, duration in meeting_data:
        print(f"\n🎯 Processing: {title} ({recording_id})")
        
        # Check if already processed
        cursor.execute("SELECT 1 FROM training_data WHERE meeting_id = ?", (recording_id,))
        if cursor.fetchone():
            print(f"   ⏭️  Already processed, skipping")
            continue
        
        # Get transcript
        transcript_output, _ = run_fellow_command(f"transcript {recording_id}")
        
        # Get AI summary  
        summary_output, _ = run_fellow_command(f"summary {recording_id}")
        
        # Get action items
        action_items_output, _ = run_fellow_command(f"action-items --title \"{title}\"")
        
        if not transcript_output or len(transcript_output) < 100:
            print(f"   ❌ No valid transcript")
            continue
            
        # Score qualification
        qualification_score, indicators = score_voice_ai_prospect(
            transcript_output, summary_output, action_items_output
        )
        is_qualified = qualification_score > 0.3  # Threshold
        
        if is_qualified:
            qualified_count += 1
            
        print(f"   📊 Score: {qualification_score:.2f} ({'✅ QUALIFIED' if is_qualified else '❌ NOT QUALIFIED'})")
        if indicators:
            print(f"   🎯 Indicators: {', '.join(indicators[:5])}")
        
        # Insert into database
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO training_data 
                (meeting_id, meeting_title, transcript, ai_summary, action_items, 
                 date, duration, qualification_score, is_qualified, voice_ai_indicators)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recording_id, title, transcript_output, summary_output, 
                action_items_output, date, duration, qualification_score, 
                is_qualified, ';'.join(indicators)
            ))
            extracted_count += 1
        except Exception as e:
            print(f"   ❌ Error inserting: {e}")
    
    conn.commit()
    
    # Final summary
    cursor.execute("SELECT COUNT(*), COUNT(CASE WHEN is_qualified = 1 THEN 1 END) FROM training_data")
    total_count, total_qualified = cursor.fetchone()
    
    print(f"\n✅ EXTRACTION COMPLETE!")
    print(f"📊 Extracted this run: {extracted_count}")
    print(f"📈 Qualified this run: {qualified_count}")
    print(f"📋 Total records: {total_count}")
    print(f"🎯 Total qualified: {total_qualified}")
    print(f"📊 Qualification rate: {total_qualified/total_count*100:.1f}%")
    print(f"💾 Database: data/fellow_training_data.db")
    
    conn.close()
    
    # Create results summary
    results = {
        'extraction_date': datetime.now().isoformat(),
        'extracted_count': extracted_count,
        'qualified_count': qualified_count, 
        'total_records': total_count,
        'total_qualified': total_qualified,
        'qualification_rate': total_qualified/total_count if total_count > 0 else 0
    }
    
    with open('data/latest_extraction_results.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()