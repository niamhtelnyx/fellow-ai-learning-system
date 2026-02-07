#!/usr/bin/env python3
"""
Background Lead Scoring Service
Integrates with Salesforce to automatically score new leads
"""

import subprocess
import json
import time
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SalesforceBackgroundScorer:
    def __init__(self, api_base_url: str = "http://localhost:8080", check_interval: int = 300):
        self.api_base_url = api_base_url
        self.check_interval = check_interval  # 5 minutes default
        self.last_check = None
        
    def get_new_leads(self) -> List[Dict]:
        """Get new leads from Salesforce that need scoring"""
        try:
            # Calculate time window (last check or last hour)
            if self.last_check:
                since_date = self.last_check.isoformat()
            else:
                since_date = (datetime.now() - timedelta(hours=1)).isoformat()
            
            # Query for new leads without business context scores
            soql = f"""
                SELECT Id, Name, Company, Email, Website, Status, CreatedDate, 
                       Business_Context_Score__c, Business_Context_Qualified__c
                FROM Lead 
                WHERE CreatedDate > {since_date}
                AND Business_Context_Score__c = null
                ORDER BY CreatedDate DESC
                LIMIT 50
            """
            
            result = subprocess.run([
                'sf', 'data', 'query', 
                '--query', soql,
                '--target-org', 'niamh@telnyx.com',
                '--json'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                leads = data.get('result', {}).get('records', [])
                logger.info(f"📊 Found {len(leads)} new leads to score")
                return leads
            else:
                logger.error(f"❌ Salesforce query failed: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting new leads: {e}")
            return []
    
    def extract_domain_from_email(self, email: str) -> str:
        """Extract domain from email address"""
        if not email or '@' not in email:
            return None
        return email.split('@')[1]
    
    def score_lead(self, lead: Dict) -> Dict:
        """Score a single lead using the qualification API"""
        try:
            # Get domain from email or website
            domain = None
            
            if lead.get('Website'):
                domain = lead['Website'].replace('https://', '').replace('http://', '').split('/')[0]
            elif lead.get('Email'):
                domain = self.extract_domain_from_email(lead['Email'])
            
            if not domain:
                return {
                    'success': False,
                    'error': 'No domain found',
                    'score': 0.3,
                    'qualified': False
                }
            
            # Call qualification API
            api_data = {
                "domain": domain,
                "contact_name": lead.get('Name', ''),
                "company_name": lead.get('Company', '')
            }
            
            response = requests.post(
                f"{self.api_base_url}/qualify/domain",
                json=api_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'score': result['qualification_score'],
                    'qualified': result['is_qualified'],
                    'confidence': result['confidence'],
                    'industries': result['business_context']['industries'],
                    'use_cases': result['business_context']['use_cases'],
                    'reasoning': result.get('reasoning', [])
                }
            else:
                logger.error(f"❌ API error for {domain}: {response.status_code}")
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'score': 0.3,
                    'qualified': False
                }
                
        except Exception as e:
            logger.error(f"❌ Error scoring lead {lead.get('Id')}: {e}")
            return {
                'success': False,
                'error': str(e),
                'score': 0.3,
                'qualified': False
            }
    
    def update_salesforce_lead(self, lead_id: str, score_result: Dict) -> bool:
        """Update Salesforce lead with business context score"""
        try:
            # Prepare update data
            update_data = {
                'Business_Context_Score__c': score_result['score'],
                'Business_Context_Qualified__c': score_result['qualified'],
                'Business_Context_Confidence__c': score_result.get('confidence', 'UNKNOWN'),
                'Business_Context_Industries__c': ', '.join(score_result.get('industries', [])),
                'Business_Context_Use_Cases__c': ', '.join(score_result.get('use_cases', [])),
                'Business_Context_Updated__c': datetime.now().isoformat()
            }
            
            # Create SOQL update
            set_clauses = []
            for field, value in update_data.items():
                if isinstance(value, str):
                    set_clauses.append(f"{field}='{value}'")
                elif isinstance(value, bool):
                    set_clauses.append(f"{field}={str(value).lower()}")
                else:
                    set_clauses.append(f"{field}={value}")
            
            # Use sf data update command
            result = subprocess.run([
                'sf', 'data', 'update', 'record',
                '--sobject', 'Lead',
                '--record-id', lead_id,
                '--values', ' '.join(set_clauses),
                '--target-org', 'niamh@telnyx.com'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Updated lead {lead_id}: {score_result['score']:.1%} qualified={score_result['qualified']}")
                return True
            else:
                logger.error(f"❌ Failed to update lead {lead_id}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating lead {lead_id}: {e}")
            return False
    
    def run_scoring_cycle(self):
        """Run one scoring cycle"""
        logger.info("🚀 Starting scoring cycle...")
        
        # Get new leads
        leads = self.get_new_leads()
        
        if not leads:
            logger.info("📭 No new leads to score")
            return
        
        # Score each lead
        scored_count = 0
        qualified_count = 0
        
        for lead in leads:
            logger.info(f"📊 Scoring: {lead.get('Name', 'Unknown')} @ {lead.get('Company', 'Unknown')}")
            
            # Score the lead
            score_result = self.score_lead(lead)
            
            if score_result['success']:
                # Update Salesforce
                if self.update_salesforce_lead(lead['Id'], score_result):
                    scored_count += 1
                    if score_result['qualified']:
                        qualified_count += 1
                        logger.info(f"   🎯 QUALIFIED: {score_result['score']:.1%} confidence={score_result['confidence']}")
                    else:
                        logger.info(f"   ❌ Not qualified: {score_result['score']:.1%}")
            else:
                logger.warning(f"   ⚠️ Scoring failed: {score_result['error']}")
            
            # Rate limiting
            time.sleep(2)
        
        # Update last check time
        self.last_check = datetime.now()
        
        # Summary
        qualification_rate = (qualified_count / scored_count * 100) if scored_count > 0 else 0
        logger.info(f"📊 Cycle complete: {scored_count} scored, {qualified_count} qualified ({qualification_rate:.1f}%)")
    
    def run_background_service(self):
        """Run the background scoring service"""
        logger.info(f"🚀 Starting Business Context Background Scorer")
        logger.info(f"   API: {self.api_base_url}")
        logger.info(f"   Check interval: {self.check_interval} seconds")
        logger.info(f"   Salesforce org: niamh@telnyx.com")
        
        while True:
            try:
                self.run_scoring_cycle()
                
                # Wait for next cycle
                logger.info(f"⏱️ Waiting {self.check_interval} seconds until next cycle...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Background scorer stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Cycle error: {e}")
                logger.info(f"⏱️ Retrying in {self.check_interval} seconds...")
                time.sleep(self.check_interval)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Business Context Background Scorer')
    parser.add_argument('--api-url', default='http://localhost:8080', help='Qualification API URL')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run once instead of continuous')
    
    args = parser.parse_args()
    
    scorer = SalesforceBackgroundScorer(
        api_base_url=args.api_url,
        check_interval=args.interval
    )
    
    if args.once:
        scorer.run_scoring_cycle()
    else:
        scorer.run_background_service()

if __name__ == "__main__":
    main()