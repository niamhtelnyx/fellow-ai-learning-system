#!/usr/bin/env python3
"""
Sentiment-Based Feature Extractor for Fellow.ai Qualification Model
Extracts AE engagement sentiment and deal progression indicators from transcripts
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

@dataclass
class SentimentFeatures:
    """Container for extracted sentiment features"""
    ae_engagement_score: float = 0.0
    deal_progression_score: float = 0.0
    customer_readiness_score: float = 0.0
    momentum_indicators: float = 0.0
    feature_vector: List[float] = None

class AESentimentExtractor:
    """Extract AE engagement sentiment from transcripts"""
    
    def __init__(self):
        # AE engagement indicators (positive sentiment)
        self.engagement_patterns = [
            # Research/preparation signals
            r'(?i)(did.*research|looked into|researched|investigated)',
            r'(?i)(keen to understand|excited to|would love to)',
            r'(?i)(provide.*context|share.*information|walk.*through)',
            
            # Solution offering signals  
            r'(?i)(we can provide|let me show|I can walk|we offer)',
            r'(?i)(high level overview|deep dive|demonstration|demo)',
            r'(?i)(leader.*in|expertise|specialized|best practice)',
            
            # Resource sharing signals
            r'(?i)(set.*session|schedule.*follow|next.*step)',
            r'(?i)(send.*over|share.*with|provide.*you)',
            r'(?i)(resources|materials|documentation|case study)',
            
            # Consultative approach
            r'(?i)(what.*use case|tell me about|help me understand)',
            r'(?i)(sounds like|seems like|appears)',
            r'(?i)(recommend|suggest|advise|propose)'
        ]
        
        # Deal progression indicators
        self.progression_patterns = [
            # Next steps
            r'(?i)(next.*step|follow.*up|move.*forward|proceed)',
            r'(?i)(schedule|set.*up|arrange|plan)',
            r'(?i)(technical.*call|deep.*dive|detailed.*discussion)',
            r'(?i)(pilot|trial|proof.*concept|poc)',
            
            # Timeline establishment
            r'(?i)(timeline|timeframe|when.*looking|by.*when)',
            r'(?i)(urgent|asap|soon|immediately|priority)',
            r'(?i)(quarter|month|week|deadline)',
            
            # Stakeholder engagement
            r'(?i)(team|colleagues|decision.*maker|stakeholder)',
            r'(?i)(introduce.*to|connect.*with|involve)',
            r'(?i)(technical.*team|engineering|it.*team)',
            
            # Budget/commercial discussion
            r'(?i)(budget|cost|price|investment|spend)',
            r'(?i)(approval|sign.*off|decision)',
            r'(?i)(contract|agreement|terms)'
        ]
        
        # Customer readiness signals
        self.readiness_patterns = [
            # Problem articulation
            r'(?i)(problem|challenge|issue|pain.*point)',
            r'(?i)(currently.*using|existing.*solution|competitor)',
            r'(?i)(looking.*for|need.*to|want.*to|require)',
            
            # Specific requirements
            r'(?i)(requirement|specification|criteria|must.*have)',
            r'(?i)(integration|api|technical|feature)',
            r'(?i)(scalability|performance|security|compliance)',
            
            # Use case clarity
            r'(?i)(use.*case|scenario|workflow|process)',
            r'(?i)(patients|customers|users|calls)',
            r'(?i)(volume|frequency|scale|size)',
            
            # Organizational context
            r'(?i)(hospital|healthcare|government|enterprise)',
            r'(?i)(department|division|organization|company)'
        ]
        
        # Momentum indicators
        self.momentum_patterns = [
            # Multiple touchpoints
            r'(?i)(second.*call|follow.*up.*call|previous.*discussion)',
            r'(?i)(as.*discussed|as.*mentioned|from.*last.*time)',
            
            # Active participation
            r'(?i)(great.*question|good.*point|exactly|absolutely)',
            r'(?i)(that.*makes.*sense|I.*understand|got.*it)',
            
            # Forward movement
            r'(?i)(excited|interested|keen|eager)',
            r'(?i)(perfect|great|excellent|fantastic)',
            r'(?i)(aligned|fits|matches|suitable)'
        ]

    def extract_ae_engagement(self, transcript: str) -> float:
        """Extract AE engagement level from transcript"""
        if not transcript or len(transcript) < 100:
            return 0.0
            
        engagement_score = 0.0
        transcript_length = len(transcript)
        
        # Count engagement pattern matches
        for pattern in self.engagement_patterns:
            matches = len(re.findall(pattern, transcript))
            # Normalize by transcript length
            normalized_matches = matches / (transcript_length / 1000)
            engagement_score += normalized_matches
            
        # Cap at reasonable maximum
        return min(engagement_score, 10.0)
    
    def extract_deal_progression(self, transcript: str) -> float:
        """Extract deal progression signals"""
        if not transcript:
            return 0.0
            
        progression_score = 0.0
        transcript_length = len(transcript)
        
        for pattern in self.progression_patterns:
            matches = len(re.findall(pattern, transcript))
            normalized_matches = matches / (transcript_length / 1000)
            progression_score += normalized_matches
            
        return min(progression_score, 8.0)
    
    def extract_customer_readiness(self, transcript: str) -> float:
        """Extract customer readiness indicators"""
        if not transcript:
            return 0.0
            
        readiness_score = 0.0
        transcript_length = len(transcript)
        
        for pattern in self.readiness_patterns:
            matches = len(re.findall(pattern, transcript))
            normalized_matches = matches / (transcript_length / 1000)
            readiness_score += normalized_matches
            
        return min(readiness_score, 7.0)
    
    def extract_momentum_indicators(self, transcript: str) -> float:
        """Extract deal momentum signals"""
        if not transcript:
            return 0.0
            
        momentum_score = 0.0
        transcript_length = len(transcript)
        
        for pattern in self.momentum_patterns:
            matches = len(re.findall(pattern, transcript))
            normalized_matches = matches / (transcript_length / 1000)
            momentum_score += normalized_matches
            
        return min(momentum_score, 6.0)

class CallQualityAnalyzer:
    """Analyze call quality indicators"""
    
    def __init__(self):
        # Internal/non-sales call indicators (negative signals)
        self.internal_patterns = [
            r'(?i)(incident|ticket|bug|error|fix)',
            r'(?i)(deployment|rollback|migration|upgrade)',
            r'(?i)(internal.*call|team.*sync|standup)',
            r'(?i)(retrospective|planning|review.*meeting)',
            r'(?i)(network.*issue|connectivity|latency|jitter)'
        ]
        
        # Customer engagement indicators (positive signals)
        self.customer_patterns = [
            r'(?i)(customer|client|prospect|lead)',
            r'(?i)(intro.*call|discovery.*call|demo)',
            r'(?i)(solution|product|service|offering)',
            r'(?i)(business.*case|roi|value.*proposition)'
        ]

    def is_sales_call(self, transcript: str, meeting_title: str = "") -> float:
        """Determine if this is a sales/customer call vs internal"""
        if not transcript:
            return 0.0
            
        internal_score = 0.0
        customer_score = 0.0
        
        # Check for internal patterns
        for pattern in self.internal_patterns:
            internal_score += len(re.findall(pattern, transcript))
            
        # Check for customer patterns  
        for pattern in self.customer_patterns:
            customer_score += len(re.findall(pattern, transcript))
            
        # Check meeting title
        if meeting_title:
            if re.search(r'(?i)(intro|discovery|demo|customer)', meeting_title):
                customer_score += 2
            if re.search(r'(?i)(internal|sync|standup|team)', meeting_title):
                internal_score += 2
                
        # Return probability of being a sales call
        total_signals = internal_score + customer_score
        if total_signals == 0:
            return 0.5  # Neutral if no clear signals
            
        return customer_score / total_signals

def extract_sentiment_features(transcript: str, meeting_title: str = "") -> SentimentFeatures:
    """Main function to extract all sentiment-based features"""
    
    extractor = AESentimentExtractor()
    quality_analyzer = CallQualityAnalyzer()
    
    # Extract core features
    ae_engagement = extractor.extract_ae_engagement(transcript)
    deal_progression = extractor.extract_deal_progression(transcript) 
    customer_readiness = extractor.extract_customer_readiness(transcript)
    momentum_indicators = extractor.extract_momentum_indicators(transcript)
    
    # Analyze call quality
    sales_call_probability = quality_analyzer.is_sales_call(transcript, meeting_title)
    
    # Apply quality multiplier - internal calls get heavily penalized
    quality_multiplier = sales_call_probability
    
    ae_engagement *= quality_multiplier
    deal_progression *= quality_multiplier
    customer_readiness *= quality_multiplier
    momentum_indicators *= quality_multiplier
    
    # Create feature vector
    feature_vector = [
        ae_engagement,
        deal_progression, 
        customer_readiness,
        momentum_indicators,
        sales_call_probability,
        len(transcript) / 1000 if transcript else 0,  # Transcript length normalized
        transcript.count('\n') / 10 if transcript else 0  # Speaker turn count normalized
    ]
    
    return SentimentFeatures(
        ae_engagement_score=ae_engagement,
        deal_progression_score=deal_progression,
        customer_readiness_score=customer_readiness,
        momentum_indicators=momentum_indicators,
        feature_vector=feature_vector
    )

if __name__ == "__main__":
    # Test with sample transcript
    sample_transcript = """
    [3:27] Edmond Pouilly: My name is Edmund, I'm the account executive at Telnex here based out of Sydney.
    [3:35] Edmond Pouilly: So yeah, thank you for submitting the inquiry. I think you provide quite a bit of detail as well.
    [3:39] Edmond Pouilly: We're absolutely keen to understand your organization, the use case a little bit better and we can provide more context around who Tanux is, what we do and why.
    [3:48] Edmond Pouilly: We're a leader on the Voice AI side as well.
    [3:50] Edmond Pouilly: And if we're aligned we can move into maybe a high level overview of the AI agent today as well.
    [3:56] Edmond Pouilly: And if we've got time and we're aligned still, we can maybe set a session for a very much a deep dive into the AI agent in the following session.
    """
    
    features = extract_sentiment_features(sample_transcript, "Telnyx Intro Call")
    print(f"AE Engagement: {features.ae_engagement_score:.2f}")
    print(f"Deal Progression: {features.deal_progression_score:.2f}")
    print(f"Customer Readiness: {features.customer_readiness_score:.2f}")
    print(f"Momentum: {features.momentum_indicators:.2f}")
    print(f"Feature Vector: {features.feature_vector}")