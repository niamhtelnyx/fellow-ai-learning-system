#!/usr/bin/env python3
"""
Simple test extraction for Telnyx intro calls
"""

import sqlite3
import subprocess
import os
import time

# Set the API key
os.environ['FELLOW_API_KEY'] = "c2e66647b10bfbc93b85cc1b05b8bc519bc61d849a09f5ac8f767fbad927dcc4"

def run_fellow_command(command):
    """Run Fellow skill command"""
    fellow_script = "/Users/niamhcollins/clawd/skills/fellow/skills/fellow/fellow.sh"
    try:
        print(f"Running: {fellow_script} {' '.join(command)}")
        result = subprocess.run(
            [fellow_script] + command, 
            capture_output=True, 
            text=True,
            env=os.environ.copy(),
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout, None
        else:
            return None, result.stderr
    except Exception as e:
        return None, str(e)

def main():
    print("🧪 TESTING TELNYX INTRO CALL EXTRACTION")
    print("=" * 50)
    
    # Get recent meetings
    print("📋 Getting recent meetings...")
    meetings_output, error = run_fellow_command(['meetings', '--limit', '10'])
    
    if error:
        print(f"❌ Error: {error}")
        return
    
    print(f"✅ Got meetings output: {len(meetings_output)} characters")
    print("\nFirst few lines:")
    print(meetings_output[:500])
    
    # Parse meetings
    print("\n📊 Parsing meetings...")
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
                
                # Filter for Telnyx intro calls
                if title and "Telnyx Intro Call" in title:
                    meeting_data.append((recording_id, title, date, duration))
                    print(f"   📅 Found: {title} ({recording_id}) - {date}")
    
    print(f"\n🎯 Found {len(meeting_data)} Telnyx intro calls")
    
    if meeting_data:
        # Test extraction for first meeting
        recording_id, title, date, duration = meeting_data[0]
        print(f"\n🧪 Testing extraction for: {title} ({recording_id})")
        
        # Check database first
        conn = sqlite3.connect("data/fellow_training_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM training_data WHERE meeting_id = ?", (recording_id,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"   ✅ Already in database, skipping extraction test")
        else:
            print(f"   🔄 Getting transcript...")
            transcript_output, transcript_error = run_fellow_command(['transcript', recording_id])
            
            if transcript_error:
                print(f"   ❌ Transcript error: {transcript_error}")
            elif transcript_output:
                print(f"   ✅ Got transcript: {len(transcript_output)} characters")
                print(f"   📝 First 200 chars: {transcript_output[:200]}...")
            else:
                print(f"   ❌ No transcript output")
        
        conn.close()
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()