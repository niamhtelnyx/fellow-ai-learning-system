#!/usr/bin/env python3
"""
AE Sentiment & Qualification Analysis for Fellow Intro Calls
Analyzes 200 call transcripts to determine true qualification labels for ML training
"""

import sqlite3
import json
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

@dataclass
class QualificationAnalysis:
    call_id: str
    meeting_title: str
    engagement_level: str
    progression_signals: List[str]
    rejection_signals: List[str]
    questions_depth: str
    discovery_patterns: List[str]
    qualification_label: str
    confidence_score: float
    original_score: float
    original_qualified: bool
    analysis_notes: str

class AESentimentAnalyzer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.results = []
        
        # Progression signal patterns
        self.progression_patterns = [
            r"let me connect you",
            r"next steps?",
            r"follow.?up",
            r"schedule",
            r"meeting",
            r"when can we",
            r"I'll set",
            r"moving forward",
            r"sounds good",
            r"interested",
            r"definitely",
            r"perfect",
            r"that works",
            r"sounds like a fit",
            r"exactly what we need",
            r"I'd like to explore",
            r"can you show me",
            r"tell me more"
        ]
        
        # Rejection signal patterns
        self.rejection_patterns = [
            r"not a fit",
            r"not right timing",
            r"different requirements",
            r"not what we're looking for",
            r"we're all set",
            r"we have something",
            r"already using",
            r"not interested",
            r"maybe in the future",
            r"budget",
            r"pricing is",
            r"too expensive",
            r"we'll think about it",
            r"I'll get back to you",
            r"not right now"
        ]
        
        # Discovery question patterns
        self.discovery_patterns = [
            r"what's your current",
            r"how do you currently",
            r"what challenges",
            r"what problems",
            r"walk me through",
            r"can you explain",
            r"what does your process",
            r"how many",
            r"what's your volume",
            r"what integrations",
            r"what's your timeline",
            r"what's important to you"
        ]

    def extract_speaker_turns(self, transcript: str) -> Dict[str, List[str]]:
        """Extract individual speaker turns from transcript"""
        # Split by timestamp patterns [MM:SS] or speaker patterns
        turns = re.split(r'\[\d+:\d+\]', transcript)
        
        ae_turns = []
        prospect_turns = []
        
        for turn in turns:
            if not turn.strip():
                continue
                
            # Look for speaker name at beginning of turn
            speaker_match = re.match(r'^([^:]+):', turn.strip())
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                content = turn[len(speaker)+1:].strip()
                
                # Classify as AE or prospect based on common AE names/patterns
                if any(name in speaker.lower() for name in ['mario', 'matthew', 'ernie', 'abdullah', 'quinn']):
                    ae_turns.append(content)
                else:
                    prospect_turns.append(content)
        
        return {"ae": ae_turns, "prospect": prospect_turns}

    def analyze_engagement_level(self, ae_turns: List[str], prospect_turns: List[str]) -> Tuple[str, float]:
        """Analyze AE engagement level"""
        if not ae_turns:
            return "unknown", 0.0
            
        ae_content = " ".join(ae_turns).lower()
        
        # Count engagement indicators
        excited_indicators = len(re.findall(r'(great|awesome|perfect|fantastic|excellent|amazing|love|excited)', ae_content))
        neutral_indicators = len(re.findall(r'(okay|sure|alright|understood|right|yes)', ae_content))
        rejection_indicators = len(re.findall(r'(unfortunately|however|but|concern|issue|problem)', ae_content))
        
        # Calculate scores
        total_words = len(ae_content.split())
        if total_words < 10:
            return "unknown", 0.0
            
        excited_ratio = excited_indicators / (total_words / 100)
        neutral_ratio = neutral_indicators / (total_words / 100)
        rejection_ratio = rejection_indicators / (total_words / 100)
        
        if excited_ratio > 2.0:
            return "excited", 0.9
        elif rejection_ratio > 1.5:
            return "polite_rejection", 0.8
        else:
            return "neutral", 0.7

    def find_progression_signals(self, transcript: str) -> List[str]:
        """Find progression signals in transcript"""
        signals = []
        content = transcript.lower()
        
        for pattern in self.progression_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                signals.extend(matches)
        
        return list(set(signals))  # Remove duplicates

    def find_rejection_signals(self, transcript: str) -> List[str]:
        """Find rejection signals in transcript"""
        signals = []
        content = transcript.lower()
        
        for pattern in self.rejection_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                signals.extend(matches)
        
        return list(set(signals))

    def analyze_question_depth(self, ae_turns: List[str]) -> Tuple[str, float]:
        """Analyze depth of AE questions"""
        if not ae_turns:
            return "none", 0.0
            
        ae_content = " ".join(ae_turns).lower()
        
        # Count question types
        surface_questions = len(re.findall(r'(how are you|what do you do|tell me about)', ae_content))
        discovery_questions = 0
        
        for pattern in self.discovery_patterns:
            discovery_questions += len(re.findall(pattern, ae_content))
        
        technical_questions = len(re.findall(r'(integration|api|technical|implementation|architecture)', ae_content))
        
        if discovery_questions > 3 or technical_questions > 2:
            return "deep_technical", 0.9
        elif discovery_questions > 1:
            return "moderate_discovery", 0.7
        elif surface_questions > 0:
            return "surface_level", 0.4
        else:
            return "none", 0.1

    def analyze_discovery_patterns(self, ae_turns: List[str]) -> List[str]:
        """Analyze discovery patterns in AE behavior"""
        if not ae_turns:
            return []
            
        ae_content = " ".join(ae_turns).lower()
        patterns_found = []
        
        if "business needs" in ae_content or "requirements" in ae_content:
            patterns_found.append("business_needs_exploration")
            
        if "current solution" in ae_content or "how do you currently" in ae_content:
            patterns_found.append("current_state_discovery")
            
        if "pain point" in ae_content or "challenge" in ae_content or "problem" in ae_content:
            patterns_found.append("pain_point_identification")
            
        if "timeline" in ae_content or "when" in ae_content:
            patterns_found.append("timeline_qualification")
            
        if "budget" in ae_content or "pricing" in ae_content or "cost" in ae_content:
            patterns_found.append("budget_discovery")
            
        return patterns_found

    def determine_qualification(self, 
                              engagement_level: str,
                              progression_signals: List[str],
                              rejection_signals: List[str],
                              questions_depth: str,
                              discovery_patterns: List[str]) -> Tuple[str, float]:
        """Determine final qualification label and confidence"""
        
        # Calculate qualification score
        score = 0.0
        confidence = 0.5
        
        # Engagement scoring
        if engagement_level == "excited":
            score += 0.3
            confidence += 0.2
        elif engagement_level == "polite_rejection":
            score -= 0.3
            confidence += 0.3
        
        # Progression signals
        if len(progression_signals) > 2:
            score += 0.4
            confidence += 0.2
        elif len(progression_signals) > 0:
            score += 0.2
            confidence += 0.1
            
        # Rejection signals (negative scoring)
        if len(rejection_signals) > 1:
            score -= 0.4
            confidence += 0.2
        elif len(rejection_signals) > 0:
            score -= 0.2
            confidence += 0.1
            
        # Question depth
        if questions_depth == "deep_technical":
            score += 0.3
            confidence += 0.2
        elif questions_depth == "moderate_discovery":
            score += 0.2
            confidence += 0.1
            
        # Discovery patterns
        score += len(discovery_patterns) * 0.1
        confidence += len(discovery_patterns) * 0.05
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        # Determine qualification
        if score > 0.3:
            return "QUALIFIED", confidence
        else:
            return "NOT_QUALIFIED", confidence

    def analyze_transcript(self, record: Dict[str, Any]) -> QualificationAnalysis:
        """Analyze a single transcript"""
        transcript = record.get('transcript', '')
        if not transcript:
            return self.create_empty_analysis(record)
        
        # Extract speaker turns
        turns = self.extract_speaker_turns(transcript)
        ae_turns = turns["ae"]
        prospect_turns = turns["prospect"]
        
        # Perform analysis
        engagement_level, eng_confidence = self.analyze_engagement_level(ae_turns, prospect_turns)
        progression_signals = self.find_progression_signals(transcript)
        rejection_signals = self.find_rejection_signals(transcript)
        questions_depth, depth_confidence = self.analyze_question_depth(ae_turns)
        discovery_patterns = self.analyze_discovery_patterns(ae_turns)
        
        # Determine qualification
        qualification_label, confidence_score = self.determine_qualification(
            engagement_level, progression_signals, rejection_signals, 
            questions_depth, discovery_patterns
        )
        
        # Create analysis notes
        analysis_notes = f"AE Turns: {len(ae_turns)}, Prospect Turns: {len(prospect_turns)}, "
        analysis_notes += f"Progression: {len(progression_signals)}, Rejection: {len(rejection_signals)}"
        
        return QualificationAnalysis(
            call_id=record.get('meeting_id', ''),
            meeting_title=record.get('meeting_title', ''),
            engagement_level=engagement_level,
            progression_signals=progression_signals,
            rejection_signals=rejection_signals,
            questions_depth=questions_depth,
            discovery_patterns=discovery_patterns,
            qualification_label=qualification_label,
            confidence_score=confidence_score,
            original_score=record.get('qualification_score', 0.0),
            original_qualified=record.get('is_qualified', False),
            analysis_notes=analysis_notes
        )

    def create_empty_analysis(self, record: Dict[str, Any]) -> QualificationAnalysis:
        """Create empty analysis for records without transcript"""
        return QualificationAnalysis(
            call_id=record.get('meeting_id', ''),
            meeting_title=record.get('meeting_title', ''),
            engagement_level="unknown",
            progression_signals=[],
            rejection_signals=[],
            questions_depth="none",
            discovery_patterns=[],
            qualification_label="NOT_QUALIFIED",
            confidence_score=0.1,
            original_score=record.get('qualification_score', 0.0),
            original_qualified=record.get('is_qualified', False),
            analysis_notes="No transcript available"
        )

    def process_database(self) -> Dict[str, Any]:
        """Process all records in the database"""
        print(f"🔍 Starting AE sentiment analysis on {self.db_path}")
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all records
        cursor.execute("SELECT * FROM training_data ORDER BY id")
        records = cursor.fetchall()
        
        print(f"📊 Found {len(records)} records to analyze")
        
        # Process each record
        qualified_count = 0
        progress_count = 0
        
        for i, record in enumerate(records):
            analysis = self.analyze_transcript(dict(record))
            self.results.append(analysis)
            
            if analysis.qualification_label == "QUALIFIED":
                qualified_count += 1
                
            progress_count += 1
            
            # Progress report every 40 calls
            if progress_count % 40 == 0:
                qualification_rate = (qualified_count / progress_count) * 100
                print(f"📈 Progress: {progress_count}/200 calls analyzed")
                print(f"   Qualification Rate: {qualification_rate:.1f}% ({qualified_count} qualified)")
                print(f"   Current Analysis: {analysis.meeting_title}")
                print(f"   Result: {analysis.qualification_label} (confidence: {analysis.confidence_score:.2f})")
        
        conn.close()
        
        # Final statistics
        final_qualification_rate = (qualified_count / len(records)) * 100
        
        # Calculate agreement with original labels
        original_qualified = sum(1 for r in self.results if r.original_qualified)
        new_qualified = sum(1 for r in self.results if r.qualification_label == "QUALIFIED")
        
        agreement_count = sum(1 for r in self.results 
                            if (r.original_qualified and r.qualification_label == "QUALIFIED") or
                               (not r.original_qualified and r.qualification_label == "NOT_QUALIFIED"))
        
        agreement_rate = (agreement_count / len(records)) * 100
        
        return {
            "analysis_summary": {
                "total_calls": len(records),
                "qualified_count": qualified_count,
                "qualification_rate": final_qualification_rate,
                "original_qualified_count": original_qualified,
                "original_qualification_rate": (original_qualified / len(records)) * 100,
                "agreement_rate": agreement_rate,
                "analysis_date": datetime.now().isoformat()
            },
            "results": [
                {
                    "call_id": r.call_id,
                    "meeting_title": r.meeting_title,
                    "sentiment_analysis": {
                        "engagement_level": r.engagement_level,
                        "progression_signals": r.progression_signals,
                        "rejection_signals": r.rejection_signals,
                        "questions_depth": r.questions_depth,
                        "discovery_patterns": r.discovery_patterns
                    },
                    "qualification": {
                        "label": r.qualification_label,
                        "confidence_score": r.confidence_score,
                        "original_score": r.original_score,
                        "original_qualified": r.original_qualified
                    },
                    "analysis_notes": r.analysis_notes
                }
                for r in self.results
            ]
        }

def main():
    # Initialize analyzer
    db_path = "/Users/niamhcollins/clawd/fellow-learning-system/data/fellow_training_data.db"
    output_path = "/Users/niamhcollins/clawd/fellow-learning-system/analysis/ae-sentiment-analysis.json"
    
    analyzer = AESentimentAnalyzer(db_path)
    
    # Process database
    results = analyzer.process_database()
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Analysis complete!")
    print(f"📋 Results saved to: {output_path}")
    print(f"📊 Final Statistics:")
    print(f"   Total Calls: {results['analysis_summary']['total_calls']}")
    print(f"   New Qualification Rate: {results['analysis_summary']['qualification_rate']:.1f}%")
    print(f"   Original Qualification Rate: {results['analysis_summary']['original_qualification_rate']:.1f}%")
    print(f"   Agreement Rate: {results['analysis_summary']['agreement_rate']:.1f}%")

if __name__ == "__main__":
    main()