#!/usr/bin/env python3
"""
Enhanced Fellow Learning Qualification Scorer
Real-time lead qualification using advanced text analysis and business logic
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class EnhancedFellowScorer:
    """Advanced scoring engine for Fellow call qualification"""
    
    def __init__(self):
        self.voice_ai_keywords = [
            'voice ai', 'conversational ai', 'ai calling', 'voice automation',
            'ai voice', 'voice bot', 'ai assistant', 'speech ai', 'voice agent',
            'ai marketplace', 'calling agent', 'voice-enabled', 'ai powered',
            'voice assistant', 'speech recognition', 'voice biometrics',
            'voice analytics', 'ai orchestration', 'voice infrastructure',
            'sentiment analysis', 'call routing ai', 'voice screening'
        ]
        
        self.business_scale_indicators = {
            'high': ['enterprise', 'fortune 500', 'procurement', 'million', 'large',
                    'global', 'contract', 'budget approved', 'immediate implementation'],
            'medium': ['growing', 'scaling', 'series', 'funded', 'technical team',
                      'ready', 'launched', 'established', 'professional'],
            'small': ['startup', 'small', 'family', 'individual', 'limited budget',
                     'basic', 'simple', 'minimal', 'no technical']
        }
        
        self.urgency_indicators = [
            'immediate', 'asap', 'ready', 'launched', 'approved', 'procurement',
            'timeline', 'urgent', 'now', 'this week', 'next month', 'q2', 'q3'
        ]
        
        self.industry_multipliers = {
            'ai': 1.3, 'technology': 1.2, 'software': 1.15, 'healthcare': 1.1,
            'finance': 1.1, 'security': 1.1, 'telecommunications': 1.2,
            'call center': 1.25, 'legal': 1.05, 'marketing': 1.0,
            'restaurant': 0.7, 'retail': 0.8, 'nonprofit': 0.6
        }
    
    def analyze_voice_ai_signals(self, text: str) -> Dict:
        """Analyze text for Voice AI signals and strength"""
        if not text:
            return {'score': 0, 'signals': [], 'confidence': 0.0}
        
        text_lower = text.lower()
        detected_signals = []
        
        for keyword in self.voice_ai_keywords:
            if keyword in text_lower:
                detected_signals.append(keyword)
        
        # Weight signals by importance
        signal_weights = {
            'voice ai': 3.0, 'conversational ai': 3.0, 'ai calling': 2.5,
            'voice automation': 2.5, 'ai marketplace': 2.0, 'voice bot': 2.0,
            'ai assistant': 1.5, 'voice agent': 2.0, 'voice-enabled': 1.5
        }
        
        weighted_score = sum(signal_weights.get(signal, 1.0) for signal in detected_signals)
        
        # Convert to 0-100 scale
        voice_ai_score = min(100, weighted_score * 15)
        confidence = min(1.0, len(detected_signals) * 0.2)
        
        return {
            'score': voice_ai_score,
            'signals': detected_signals,
            'confidence': confidence,
            'signal_count': len(detected_signals)
        }
    
    def analyze_business_scale(self, company_info: Dict) -> Dict:
        """Analyze business scale and potential"""
        text = ' '.join([
            company_info.get('call_notes', ''),
            company_info.get('industry', ''),
            company_info.get('employees', '')
        ]).lower()
        
        scale_scores = {'high': 0, 'medium': 0, 'small': 0}
        
        for scale, indicators in self.business_scale_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    scale_scores[scale] += 1
        
        # Determine primary scale
        primary_scale = max(scale_scores, key=scale_scores.get)
        scale_confidence = scale_scores[primary_scale] / max(1, sum(scale_scores.values()))
        
        # Convert to score
        scale_multipliers = {'high': 1.4, 'medium': 1.2, 'small': 0.8}
        scale_multiplier = scale_multipliers.get(primary_scale, 1.0)
        
        return {
            'scale': primary_scale,
            'multiplier': scale_multiplier,
            'confidence': scale_confidence,
            'indicators': scale_scores
        }
    
    def analyze_urgency(self, call_notes: str, urgency_level: int) -> Dict:
        """Analyze urgency and timeline signals"""
        if not call_notes:
            base_urgency = urgency_level * 20  # Convert 1-5 to 0-100
            return {'score': base_urgency, 'signals': [], 'confidence': 0.5}
        
        text_lower = call_notes.lower()
        urgency_signals = []
        
        for indicator in self.urgency_indicators:
            if indicator in text_lower:
                urgency_signals.append(indicator)
        
        # Combine explicit urgency level with text signals
        text_urgency = len(urgency_signals) * 15
        level_urgency = urgency_level * 18
        
        combined_urgency = min(100, max(text_urgency, level_urgency))
        confidence = 0.3 + (len(urgency_signals) * 0.1) + (urgency_level * 0.1)
        
        return {
            'score': combined_urgency,
            'signals': urgency_signals,
            'confidence': min(1.0, confidence)
        }
    
    def analyze_industry_fit(self, industry: str) -> Dict:
        """Analyze industry fit and apply multipliers"""
        if not industry:
            return {'multiplier': 1.0, 'category': 'unknown'}
        
        industry_lower = industry.lower()
        
        # Find best matching industry category
        best_match = None
        best_multiplier = 1.0
        
        for category, multiplier in self.industry_multipliers.items():
            if category in industry_lower:
                if best_match is None or multiplier > best_multiplier:
                    best_match = category
                    best_multiplier = multiplier
        
        return {
            'multiplier': best_multiplier,
            'category': best_match or 'general',
            'industry': industry
        }
    
    def calculate_progression_probability(self, company_info: Dict) -> float:
        """Calculate likelihood of AE progression based on call signals"""
        call_notes = company_info.get('call_notes', '').lower()
        
        positive_signals = [
            'budget approved', 'ready to implement', 'procurement', 'timeline',
            'technical team ready', 'integration ready', 'pilot', 'poc',
            'pricing', 'contract', 'next steps', 'follow up', 'evaluation'
        ]
        
        negative_signals = [
            'just looking', 'no budget', 'not ready', 'exploring',
            'limited budget', 'small', 'basic', 'simple', 'maybe later'
        ]
        
        positive_score = sum(2 if signal in call_notes else 0 for signal in positive_signals)
        negative_score = sum(1 if signal in call_notes else 0 for signal in negative_signals)
        
        base_probability = 0.6  # Default progression probability
        signal_adjustment = (positive_score - negative_score) * 0.05
        
        return max(0.1, min(0.95, base_probability + signal_adjustment))
    
    def generate_qualification_reasoning(self, analysis: Dict) -> List[str]:
        """Generate human-readable reasoning for qualification decision"""
        reasoning = []
        
        voice_ai = analysis['voice_ai']
        business = analysis['business_scale'] 
        urgency = analysis['urgency']
        industry = analysis['industry']
        
        # Voice AI reasoning
        if voice_ai['score'] > 80:
            reasoning.append(f"Strong Voice AI signals detected: {', '.join(voice_ai['signals'][:3])}")
        elif voice_ai['score'] > 40:
            reasoning.append(f"Moderate Voice AI potential: {', '.join(voice_ai['signals'][:2])}")
        elif voice_ai['score'] == 0:
            reasoning.append("No Voice AI signals detected")
        
        # Business scale reasoning
        if business['scale'] == 'high':
            reasoning.append("Enterprise-scale opportunity with high potential")
        elif business['scale'] == 'medium':
            reasoning.append("Growing business with solid potential")
        else:
            reasoning.append("Small business with limited scale")
        
        # Urgency reasoning
        if urgency['score'] > 70:
            reasoning.append(f"High urgency indicators: {', '.join(urgency['signals'][:2])}")
        elif urgency['score'] > 40:
            reasoning.append("Moderate urgency and timeline pressure")
        
        # Industry reasoning
        if industry['multiplier'] > 1.2:
            reasoning.append(f"High-value {industry['category']} industry vertical")
        elif industry['multiplier'] < 0.9:
            reasoning.append(f"Lower-priority {industry['category']} industry")
        
        return reasoning[:4]  # Return top 4 reasons
    
    def score_lead(self, company_info: Dict) -> Dict:
        """Main scoring function - returns comprehensive qualification analysis"""
        
        # Extract key information
        call_notes = company_info.get('call_notes', '')
        industry = company_info.get('industry', '')
        urgency_level = company_info.get('urgency_level', 0)
        company_name = company_info.get('company_name', '')
        
        # Run comprehensive analysis
        voice_ai_analysis = self.analyze_voice_ai_signals(f"{call_notes} {industry} {company_name}")
        business_analysis = self.analyze_business_scale(company_info)
        urgency_analysis = self.analyze_urgency(call_notes, urgency_level)
        industry_analysis = self.analyze_industry_fit(industry)
        
        # Calculate base qualification score
        base_score = 40  # Starting point
        
        # Apply Voice AI boost (major factor)
        voice_ai_boost = voice_ai_analysis['score'] * 0.4
        base_score += voice_ai_boost
        
        # Apply business scale multiplier
        base_score *= business_analysis['multiplier']
        
        # Apply urgency boost
        urgency_boost = urgency_analysis['score'] * 0.2
        base_score += urgency_boost
        
        # Apply industry multiplier
        base_score *= industry_analysis['multiplier']
        
        # Cap the score
        qualification_score = min(100, max(10, int(base_score)))
        
        # Voice AI fit is based on AI signals only
        voice_ai_fit = int(voice_ai_analysis['score'])
        
        # Calculate progression probability
        progression_probability = self.calculate_progression_probability(company_info)
        
        # Determine routing recommendation
        if qualification_score >= 75:
            recommendation = 'AE_HANDOFF'
            priority = 'HIGH_VOICE_AI' if voice_ai_fit > 60 else 'HIGH'
        elif qualification_score >= 50:
            recommendation = 'AE_HANDOFF' 
            priority = 'MEDIUM'
        else:
            recommendation = 'SELF_SERVICE'
            priority = 'LOW'
        
        # Calculate overall confidence
        confidence_factors = [
            voice_ai_analysis['confidence'],
            business_analysis['confidence'],
            urgency_analysis['confidence']
        ]
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        # Generate reasoning
        analysis_data = {
            'voice_ai': voice_ai_analysis,
            'business_scale': business_analysis,
            'urgency': urgency_analysis,
            'industry': industry_analysis
        }
        reasoning = self.generate_qualification_reasoning(analysis_data)
        
        return {
            'qualification_score': qualification_score,
            'voice_ai_fit': voice_ai_fit,
            'progression_probability': progression_probability,
            'recommendation': recommendation,
            'priority': priority,
            'confidence': round(overall_confidence, 2),
            'reasoning': reasoning,
            'analysis_breakdown': {
                'base_score': 40,
                'voice_ai_boost': round(voice_ai_boost, 1),
                'business_multiplier': business_analysis['multiplier'],
                'urgency_boost': round(urgency_boost, 1),
                'industry_multiplier': industry_analysis['multiplier'],
                'final_score': qualification_score
            },
            'model_version': 'enhanced_v1',
            'scored_at': datetime.now().isoformat()
        }

# Test the enhanced scorer
if __name__ == '__main__':
    scorer = EnhancedFellowScorer()
    
    # Test with Voice AI company
    test_voice_ai = {
        'company_name': 'Speaker AI',
        'industry': 'AI/Voice Technology', 
        'call_notes': 'AI marketplace platform where customers buy voice AI agents for calling and automation',
        'urgency_level': 5
    }
    
    result = scorer.score_lead(test_voice_ai)
    print(f"Voice AI Test - Score: {result['qualification_score']}, Voice AI Fit: {result['voice_ai_fit']}")
    print(f"Reasoning: {result['reasoning']}")
    print()
    
    # Test with small business
    test_small = {
        'company_name': 'Mom Pizza',
        'industry': 'Restaurant',
        'call_notes': 'Small pizza shop wants basic SMS for order notifications, limited budget',
        'urgency_level': 1
    }
    
    result2 = scorer.score_lead(test_small)
    print(f"Small Business Test - Score: {result2['qualification_score']}, Voice AI Fit: {result2['voice_ai_fit']}")
    print(f"Reasoning: {result2['reasoning']}")