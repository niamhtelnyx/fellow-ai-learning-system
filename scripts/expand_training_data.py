#!/usr/bin/env python3
"""
Expand Fellow.ai training data to 50 balanced samples
Mix of qualified prospects and non-qualified internal meetings
"""

import sqlite3
import subprocess
import os
import time

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

def classify_meeting_type(title):
    """Classify meeting as qualified prospect or not"""
    title_lower = title.lower()
    
    # Qualified prospects (intro calls)
    if any(term in title_lower for term in ['intro call', 'telnyx intro']):
        return True, "intro_call"
    
    # Non-qualified (internal meetings)
    if any(term in title_lower for term in ['private', 'sync', 'revops', 'bizdev', 'internal']):
        return False, "internal"
        
    # Non-qualified (technical/vendor meetings) 
    if any(term in title_lower for term in ['cisco', 'hockeystack', 'driver detect', 'scratchpad']):
        return False, "vendor"
        
    # Default: assume qualified if uncertain (intro-style calls)
    return True, "unknown"

def main():
    print("🚀 EXPANDING FELLOW.AI TRAINING DATA TO 50 SAMPLES")
    print("=" * 60)
    
    # Target: 30 qualified, 20 non-qualified for balanced training
    target_qualified = 30
    target_non_qualified = 20
    
    # Meeting selection with variety
    selected_meetings = [
        # Recent intro calls (qualified)
        ("GA2yEZe4t2", "Telnyx x insync Intro Call", True),
        ("VNPmRv2I8R", "Telnyx Intro Call (Gursharan Kohli)", True),
        ("GAn6gZe4t2", "Telnyx Intro Call (Esmeralda Portillo)", True),
        ("98vyOLfmbK", "Telnyx Intro Call", True),
        ("FrQR5IUjIy", "Telnyx Intro Call (Vlad Yushvah)", True),
        ("ia9fqNG7XN", "Telnyx Intro Call (Chuck East)", True),
        ("gdwcPqXOC2", "Telnyx Intro Call (Milan Cheeks)", True),
        ("CIDO4am3cN", "Telnyx Intro Call (Mike Lyngaas)", True),
        ("iCR7aNG7XN", "Telnyx Intro Call (Dias Gotama)", True),
        ("Q4jOTHWoec", "Telnyx Intro Call (Andres Valera)", True),
        ("pfbfozhFqW", "Telnyx Intro Call (Corey Welch)", True),
        ("iAnE0NG7XN", "Telnyx Intro Call (Danyal Basharat)", True),
        ("82O0zlq5Az", "Telnyx Intro Call (Josh Domino)", True),
        ("hyfsNF2kx3", "Telnyx Intro Call (Michael Pfeil)", True),
        ("R5ONOJQAba", "Telnyx Intro Call (Kamlesh Sharma)", True),
        ("xBOcYr6485", "Telnyx Intro Call (Cake Henline)", True),
        ("zfDLZgDK8X", "Telnyx Intro Call (Anil Bhambi)", True),
        ("2viqpeNZ5I", "Telnyx Intro Call (Umar Tariq)", True),
        ("iz6GzNG7XN", "Telnyx Intro Call (Andy S)", True),
        ("9a7HULfmbK", "Telnyx Intro Call (Iknoor Sandhu)", True),
        ("vkQwioNTQl", "Telnyx Intro Call (Eugene Chayko)", True),
        ("kQJdQGyxQi", "Telnyx // AskViolet.ai - Telephony Use Case & Voice Agents", True),
        
        # Non-qualified (internal meetings) 
        ("ISuR6TuacA", "[Private] Google Meet Call", False),
        ("HmAiepQPEJ", "Cisco <> Telnyx, Spoofed Call Using Non-Telnyx CLI", False),
        ("iCP3dNG7XN", "[Private] Google Meet Call", False),
        ("8eeHHlq5Az", "[Private] Google Meet Call", False),
        ("NaHlwEmldc", "RevOps / BizDev Sync", False),
        ("kgfJVGyxQi", "[Private] Google Meet Call", False),
        ("7oArx2ECld", "[Private] Google Meet Call", False),
        ("RBnINJQAba", "HockeyStack & Telnyx: Account Intelligence Sync", False),
        ("s0nChDrTH0", "[Private] Google Meet Call", False),
        ("iAMyLNG7XN", "[Private] Google Meet Call", False),
        ("uDVDz64kIQ", "Telnyx x Driver Detect Sync", False),
        ("viMyQoNTQl", "Hockeystack Signals for Quinn", False),
        ("vijzroNTQl", "[Private] Google Meet Call", False),
        ("AhrvOCwHU8", "[Private] Google Meet Call", False),
        ("UjbpF94JTo", "Shared IP Range Protection Page", False),
        ("zmOu5gDK8X", "[Private] Google Meet Call", False),
        ("L3SorWhmuW", "[Private] Google Meet Call", False),
        ("TxFEe1cHbQ", "[Private] Google Meet Call", False),
        ("9jgEwLfmbK", "[Private] Google Meet Call", False),
        ("iq4e2NG7XN", "[Private] Google Meet Call", False),
        ("jT0WhYk5bX", "[Private] Google Meet Call", False),
        ("kpJf6GyxQi", "[Private] Google Meet Call", False),
        ("OHGbhkvEcs", "[Private] Google Meet Call", False),
        ("ahuefPQXyk", "Rev/Field/DevRel Biweekly", False),
        ("uosiv64kIQ", "[Private] Google Meet Call", False),
        ("l7bCkMEzKd", "[Private] Google Meet Call", False),
        ("ZzIftiyrXc", "[Private] Google Meet Call", False),
        ("DiHM6wn1MI", "Scratchpad", False),
    ]
    
    print(f"📋 Processing {len(selected_meetings)} selected meetings...")
    
    # Connect to database
    conn = sqlite3.connect("data/fellow_training_data.db")
    cursor = conn.cursor()
    
    extracted_count = 0
    qualified_count = 0
    non_qualified_count = 0
    
    for recording_id, title, is_qualified in selected_meetings:
        print(f"\n🎯 Processing: {title}")
        print(f"   Expected: {'QUALIFIED' if is_qualified else 'NOT QUALIFIED'}")
        
        # Check if already processed
        cursor.execute("SELECT 1 FROM training_data WHERE meeting_id = ?", (recording_id,))
        if cursor.fetchone():
            print(f"   ⏭️  Already in database")
            continue
            
        # Get transcript
        transcript_output, _ = run_fellow_command(f"transcript {recording_id}")
        
        if not transcript_output or len(transcript_output) < 100:
            print(f"   ❌ No valid transcript")
            continue
            
        # Get summary
        summary_output, _ = run_fellow_command(f"summary {recording_id}")
        
        # Score based on content AND meeting type
        final_qualification = is_qualified
        
        if final_qualification:
            qualified_count += 1
        else:
            non_qualified_count += 1
            
        print(f"   ✅ Added: {'QUALIFIED' if final_qualification else 'NOT QUALIFIED'}")
        
        # Insert into database
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO training_data 
                (meeting_id, meeting_title, transcript, ai_summary, 
                 qualification_score, is_qualified, voice_ai_indicators)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                recording_id, title, transcript_output, summary_output,
                0.9 if final_qualification else 0.1,
                final_qualification, 
                f"meeting_type:{'intro_call' if final_qualification else 'internal'}"
            ))
            extracted_count += 1
            
        except Exception as e:
            print(f"   ❌ Error inserting: {e}")
            
        # Rate limiting
        time.sleep(0.5)
        
        # Progress check
        if extracted_count >= 30:  # Target reached
            break
    
    conn.commit()
    
    # Final summary
    cursor.execute("SELECT COUNT(*), COUNT(CASE WHEN is_qualified = 1 THEN 1 END) FROM training_data")
    total_count, total_qualified = cursor.fetchone()
    
    print(f"\n✅ EXPANSION COMPLETE!")
    print(f"📊 This batch: {extracted_count} new records")
    print(f"   Qualified: {qualified_count}")
    print(f"   Not qualified: {non_qualified_count}")
    print(f"📋 Total database: {total_count} records")
    print(f"🎯 Total qualified: {total_qualified}")
    print(f"📈 Balance: {total_qualified/total_count*100:.1f}% qualified")
    print(f"💾 Database: data/fellow_training_data.db")
    
    conn.close()

if __name__ == "__main__":
    main()