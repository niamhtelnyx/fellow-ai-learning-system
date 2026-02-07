#!/usr/bin/env python3
"""
Business Context Extractor for Fellow Intro Call Transcripts
Extracts structured business context from 200 intro call transcripts
"""

import sqlite3
import json
import re
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class BusinessContext:
    meeting_id: str
    meeting_title: str
    industry_vertical: Optional[str] = None
    use_case_need: Optional[str] = None
    scale_indicators: List[str] = None
    geographic_markets: List[str] = None
    competitive_references: List[str] = None
    technical_requirements: List[str] = None
    transcript_length: int = 0
    qualification_status: Optional[str] = None
    
    def __post_init__(self):
        if self.scale_indicators is None:
            self.scale_indicators = []
        if self.geographic_markets is None:
            self.geographic_markets = []
        if self.competitive_references is None:
            self.competitive_references = []
        if self.technical_requirements is None:
            self.technical_requirements = []

class BusinessContextExtractor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.industry_keywords = {
            'Healthcare': ['health', 'medical', 'hospital', 'patient', 'clinic', 'healthcare', 'pharmaceutical', 'pharma'],
            'E-commerce': ['ecommerce', 'e-commerce', 'retail', 'shopping', 'store', 'marketplace', 'product', 'cart'],
            'Voice AI': ['voice', 'ai', 'artificial intelligence', 'chatbot', 'conversational', 'speech'],
            'Financial Services': ['bank', 'financial', 'fintech', 'payment', 'lending', 'investment', 'trading'],
            'Education': ['education', 'school', 'university', 'student', 'learning', 'training'],
            'Real Estate': ['real estate', 'property', 'realtor', 'mortgage', 'rental'],
            'Marketing/Agency': ['marketing', 'agency', 'advertising', 'seo', 'campaign', 'brand'],
            'Software/SaaS': ['software', 'saas', 'platform', 'app', 'development', 'tech'],
            'Logistics': ['shipping', 'delivery', 'logistics', 'transportation', 'freight'],
            'Automotive': ['auto', 'car', 'vehicle', 'automotive', 'dealership'],
            'Insurance': ['insurance', 'policy', 'claim', 'coverage', 'premium'],
            'Travel': ['travel', 'hotel', 'booking', 'vacation', 'tourism']
        }
        
        self.use_case_keywords = {
            'Call center automation': ['call center', 'customer service', 'support', 'inbound calls', 'outbound calls'],
            'SMS notifications': ['sms', 'text', 'messaging', 'notification', 'alerts'],
            'Voice verification': ['verification', 'auth', 'otp', 'two factor', '2fa', 'voice verify'],
            'Marketing automation': ['marketing', 'campaign', 'lead', 'nurture', 'drip'],
            'Appointment reminders': ['appointment', 'reminder', 'scheduling', 'booking'],
            'Order updates': ['order', 'status', 'shipping', 'tracking', 'delivery'],
            'Payment processing': ['payment', 'billing', 'charge', 'transaction', 'stripe'],
            'Customer onboarding': ['onboarding', 'welcome', 'activation', 'setup'],
            'Lead qualification': ['lead', 'qualification', 'scoring', 'prospect'],
            'Emergency alerts': ['emergency', 'alert', 'critical', 'urgent', 'incident']
        }
        
        self.scale_patterns = [
            r'(\d+(?:,\d{3})*)\s*(?:calls?|messages?|texts?|customers?|users?)',
            r'(\d+(?:k|K|million|M|billion|B))\s*(?:calls?|messages?|texts?|customers?|users?)',
            r'team\s*of\s*(\d+)',
            r'(\d+)\s*(?:person|people|employee|staff)',
            r'volume.*?(\d+(?:,\d{3})*)',
            r'scale.*?(\d+(?:,\d{3})*)'
        ]
        
        self.geographic_patterns = [
            r'\b(?:US|USA|United States|America|American)\b',
            r'\b(?:UK|United Kingdom|Britain|British)\b',
            r'\b(?:Canada|Canadian)\b',
            r'\b(?:Australia|Australian)\b',
            r'\b(?:Europe|European)\b',
            r'\b(?:Asia|Asian)\b',
            r'\b(?:global|international|worldwide)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s*(?:CA|TX|NY|FL|IL|PA|OH|GA|NC|MI|NJ|VA|WA|AZ|MA|TN|IN|MO|MD|WI|CO|MN|SC|AL|LA|KY|OR|OK|CT|UT|IA|NV|AR|MS|KS|NM|NE|WV|ID|HI|NH|ME|MT|RI|DE|SD|ND|AK|VT|WY)\b'
        ]
        
        self.competitor_keywords = [
            'twilio', 'aws', 'amazon', 'google', 'microsoft', 'salesforce', 'hubspot',
            'zendesk', 'intercom', 'mailchimp', 'sendgrid', 'mandrill', 'plivo',
            'nexmo', 'vonage', 'bandwidth', 'signalwire', 'messagebird'
        ]
        
        self.tech_patterns = [
            r'API\b', r'REST\b', r'webhook', r'integration', r'SDK',
            r'real-?time', r'latency', r'scalable?', r'high-?volume',
            r'database', r'analytics', r'reporting', r'dashboard',
            r'mobile', r'web', r'cloud', r'on-?premise'
        ]
    
    def extract_industry_vertical(self, text: str) -> Optional[str]:
        """Extract industry/vertical from transcript text"""
        text_lower = text.lower()
        
        # Score industries based on keyword frequency
        industry_scores = {}
        for industry, keywords in self.industry_keywords.items():
            score = sum(text_lower.count(keyword.lower()) for keyword in keywords)
            if score > 0:
                industry_scores[industry] = score
        
        # Return industry with highest score
        if industry_scores:
            return max(industry_scores.items(), key=lambda x: x[1])[0]
        return None
    
    def extract_use_case(self, text: str) -> Optional[str]:
        """Extract primary use case/need from transcript"""
        text_lower = text.lower()
        
        use_case_scores = {}
        for use_case, keywords in self.use_case_keywords.items():
            score = sum(text_lower.count(keyword.lower()) for keyword in keywords)
            if score > 0:
                use_case_scores[use_case] = score
        
        if use_case_scores:
            return max(use_case_scores.items(), key=lambda x: x[1])[0]
        return None
    
    def extract_scale_indicators(self, text: str) -> List[str]:
        """Extract volume/scale indicators from transcript"""
        indicators = []
        
        for pattern in self.scale_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                indicators.append(match.group().strip())
        
        return list(set(indicators))  # Remove duplicates
    
    def extract_geographic_markets(self, text: str) -> List[str]:
        """Extract geographic markets mentioned"""
        markets = []
        
        for pattern in self.geographic_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                markets.append(match.group().strip())
        
        return list(set(markets))
    
    def extract_competitive_references(self, text: str) -> List[str]:
        """Extract competitor mentions"""
        text_lower = text.lower()
        competitors = []
        
        for competitor in self.competitor_keywords:
            if competitor.lower() in text_lower:
                competitors.append(competitor.title())
        
        return list(set(competitors))
    
    def extract_technical_requirements(self, text: str) -> List[str]:
        """Extract technical requirements discussed"""
        requirements = []
        
        for pattern in self.tech_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                requirements.append(match.group().strip())
        
        return list(set(requirements))
    
    def extract_context_from_transcript(self, meeting_id: str, meeting_title: str, 
                                      transcript: str, qualification: str) -> BusinessContext:
        """Extract all business context from a single transcript"""
        
        context = BusinessContext(
            meeting_id=meeting_id,
            meeting_title=meeting_title,
            transcript_length=len(transcript),
            qualification_status=qualification
        )
        
        context.industry_vertical = self.extract_industry_vertical(transcript)
        context.use_case_need = self.extract_use_case(transcript)
        context.scale_indicators = self.extract_scale_indicators(transcript)
        context.geographic_markets = self.extract_geographic_markets(transcript)
        context.competitive_references = self.extract_competitive_references(transcript)
        context.technical_requirements = self.extract_technical_requirements(transcript)
        
        return context
    
    def process_all_calls(self, progress_callback=None) -> List[Dict]:
        """Process all 200 calls and extract business context"""
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all calls
        cursor.execute("""
            SELECT meeting_id, meeting_title, transcript, voice_ai_indicators 
            FROM training_data 
            ORDER BY created_at
        """)
        
        calls = cursor.fetchall()
        conn.close()
        
        results = []
        total_calls = len(calls)
        
        print(f"Starting extraction from {total_calls} calls...")
        
        for i, (meeting_id, meeting_title, transcript, qualification) in enumerate(calls, 1):
            # Extract context
            context = self.extract_context_from_transcript(
                meeting_id, meeting_title or f"Call {meeting_id}", 
                transcript or "", qualification or ""
            )
            
            # Convert to dict for JSON serialization
            results.append(asdict(context))
            
            # Progress reporting every 50 calls
            if i % 50 == 0 or i == total_calls:
                if progress_callback:
                    progress_callback(i, total_calls, results[-50:] if i >= 50 else results)
                else:
                    self._default_progress_report(i, total_calls, results[-50:] if i >= 50 else results)
        
        return results
    
    def _default_progress_report(self, processed: int, total: int, recent_batch: List[Dict]):
        """Default progress reporting"""
        print(f"\n--- PROGRESS REPORT: {processed}/{total} calls processed ---")
        
        if recent_batch:
            # Analyze recent batch patterns
            industries = {}
            use_cases = {}
            
            for call in recent_batch:
                if call['industry_vertical']:
                    industries[call['industry_vertical']] = industries.get(call['industry_vertical'], 0) + 1
                if call['use_case_need']:
                    use_cases[call['use_case_need']] = use_cases.get(call['use_case_need'], 0) + 1
            
            print(f"Top industries in batch: {dict(sorted(industries.items(), key=lambda x: x[1], reverse=True)[:3])}")
            print(f"Top use cases in batch: {dict(sorted(use_cases.items(), key=lambda x: x[1], reverse=True)[:3])}")
        
        print("---")

def main():
    db_path = "/Users/niamhcollins/clawd/fellow-learning-system/data/fellow_training_data.db"
    output_path = "/Users/niamhcollins/clawd/fellow-learning-system/analysis/business-context-extraction.json"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    extractor = BusinessContextExtractor(db_path)
    
    # Process all calls
    results = extractor.process_all_calls()
    
    # Save results
    output_data = {
        "extraction_date": datetime.now().isoformat(),
        "total_calls_processed": len(results),
        "extraction_metadata": {
            "database_source": db_path,
            "extraction_method": "keyword_pattern_matching",
            "industries_detected": len(set(r['industry_vertical'] for r in results if r['industry_vertical'])),
            "use_cases_detected": len(set(r['use_case_need'] for r in results if r['use_case_need']))
        },
        "business_contexts": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n🎉 EXTRACTION COMPLETE!")
    print(f"📊 Processed: {len(results)} calls")
    print(f"💾 Saved to: {output_path}")
    
    # Summary statistics
    industries = {}
    use_cases = {}
    for result in results:
        if result['industry_vertical']:
            industries[result['industry_vertical']] = industries.get(result['industry_vertical'], 0) + 1
        if result['use_case_need']:
            use_cases[result['use_case_need']] = use_cases.get(result['use_case_need'], 0) + 1
    
    print(f"\n📈 TOP INDUSTRIES:")
    for industry, count in sorted(industries.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {industry}: {count} calls")
    
    print(f"\n🎯 TOP USE CASES:")
    for use_case, count in sorted(use_cases.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {use_case}: {count} calls")

if __name__ == "__main__":
    main()