#!/usr/bin/env python3
"""
JOB 1: Historical Lead Scoring
Pull all contacts from last 30 days and run through business context qualification model
"""

import subprocess
import json
import time
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os
try:
    from backtest_database import BacktestDatabase
except ImportError:
    import sys
    sys.path.append('.')
    from backtest_database import BacktestDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - JOB1 - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job1_historical_scoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HistoricalLeadScorer:
    def __init__(self, api_base_url: str = "http://localhost:8080", batch_size: int = 10):
        self.api_base_url = api_base_url
        self.batch_size = batch_size
        self.db = BacktestDatabase()
        self.processed_count = 0
        self.qualified_count = 0
        self.error_count = 0
        
    def get_historical_contacts(self, days_back: int = 30) -> List[Dict]:
        """Get all contacts created in the last N days from Salesforce"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            logger.info(f"📅 Querying contacts from {start_date.date()} to {end_date.date()}")
            
            # SOQL query for contacts with email addresses (needed for domain extraction)
            soql = f"""
                SELECT Id, Name, Email, AccountId, Account.Name, Account.Website, 
                       CreatedDate, LeadSource, Title, Department
                FROM Contact 
                WHERE CreatedDate >= {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}
                AND CreatedDate <= {end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}
                AND Email != null
                ORDER BY CreatedDate DESC
            """
            
            logger.info(f"🔍 Executing Salesforce query...")
            result = subprocess.run([
                'sf', 'data', 'query',
                '--query', soql,
                '--target-org', 'niamh@telnyx.com', 
                '--json'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                contacts = data.get('result', {}).get('records', [])
                logger.info(f"📊 Found {len(contacts)} contacts with email addresses from last {days_back} days")
                return contacts
            else:
                logger.error(f"❌ Salesforce query failed: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting historical contacts: {e}")
            return []
    
    def extract_domain_from_email(self, email: str) -> str:
        """Extract domain from email address"""
        if not email or '@' not in email:
            return None
        return email.split('@')[1].strip().lower()
    
    def extract_domain_from_website(self, website: str) -> str:
        """Extract domain from website URL"""
        if not website:
            return None
        
        # Clean up website URL
        domain = website.replace('https://', '').replace('http://', '').split('/')[0]
        return domain.strip().lower()
    
    def get_best_domain(self, contact: Dict) -> str:
        """Get the best domain for analysis (Account website preferred, then email domain)"""
        # Try account website first
        if contact.get('Account', {}).get('Website'):
            domain = self.extract_domain_from_website(contact['Account']['Website'])
            if domain and not domain.startswith('www.'):
                return domain
        
        # Fall back to email domain
        if contact.get('Email'):
            domain = self.extract_domain_from_email(contact['Email'])
            # Skip common email providers
            if domain and domain not in ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com']:
                return domain
        
        return None
    
    def score_contact(self, contact: Dict) -> Dict:
        """Score a single contact using the qualification API"""
        try:
            domain = self.get_best_domain(contact)
            
            if not domain:
                return {
                    'success': False,
                    'error': 'No business domain found',
                    'qualification_score': 0.2,
                    'is_qualified': False,
                    'confidence': 'LOW',
                    'domain': None
                }
            
            # Prepare API request
            api_data = {
                "domain": domain,
                "contact_name": contact.get('Name', ''),
                "company_name": contact.get('Account', {}).get('Name', '')
            }
            
            logger.info(f"🧠 Scoring {contact.get('Name', 'Unknown')} @ {domain}")
            
            # Call qualification API
            response = requests.post(
                f"{self.api_base_url}/qualify/domain",
                json=api_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                result['success'] = True
                return result
            else:
                logger.error(f"❌ API error for {domain}: {response.status_code}")
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'qualification_score': 0.3,
                    'is_qualified': False,
                    'confidence': 'ERROR',
                    'domain': domain
                }
                
        except Exception as e:
            logger.error(f"❌ Error scoring contact {contact.get('Id')}: {e}")
            return {
                'success': False,
                'error': str(e),
                'qualification_score': 0.3,
                'is_qualified': False,
                'confidence': 'ERROR',
                'domain': None
            }
    
    def process_batch(self, contacts: List[Dict]) -> Dict:
        """Process a batch of contacts"""
        batch_results = {
            'processed': 0,
            'qualified': 0,
            'errors': 0,
            'avg_score': 0
        }
        
        scores = []
        
        for contact in contacts:
            # Score the contact
            score_result = self.score_contact(contact)
            
            if score_result['success']:
                # Store in database
                self.db.store_qualification_result(contact, score_result)
                
                # Update counters
                batch_results['processed'] += 1
                if score_result.get('is_qualified', False):
                    batch_results['qualified'] += 1
                
                scores.append(score_result.get('qualification_score', 0))
                
                # Log result
                score = score_result.get('qualification_score', 0)
                qualified_status = "✅ QUALIFIED" if score_result.get('is_qualified') else "❌ NOT QUALIFIED"
                confidence = score_result.get('confidence', 'UNKNOWN')
                
                logger.info(f"   📊 {qualified_status} | {score:.1%} | {confidence}")
                
            else:
                batch_results['errors'] += 1
                logger.warning(f"   ⚠️ Error: {score_result['error']}")
            
            # Rate limiting
            time.sleep(1)
        
        batch_results['avg_score'] = sum(scores) / len(scores) if scores else 0
        return batch_results
    
    def run_historical_scoring(self, days_back: int = 30):
        """Run the complete historical scoring job"""
        logger.info("🚀 Starting Historical Lead Scoring (Job 1)")
        logger.info(f"   📅 Date range: Last {days_back} days")
        logger.info(f"   🎯 API endpoint: {self.api_base_url}")
        logger.info(f"   📊 Batch size: {self.batch_size}")
        
        start_time = datetime.now()
        
        # Get historical contacts
        contacts = self.get_historical_contacts(days_back)
        
        if not contacts:
            logger.error("❌ No contacts found to process")
            return
        
        logger.info(f"📊 Processing {len(contacts)} contacts in batches of {self.batch_size}")
        
        # Process in batches
        total_batches = (len(contacts) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(contacts), self.batch_size):
            batch_num = (i // self.batch_size) + 1
            batch = contacts[i:i + self.batch_size]
            
            logger.info(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} contacts)")
            
            batch_results = self.process_batch(batch)
            
            # Update totals
            self.processed_count += batch_results['processed']
            self.qualified_count += batch_results['qualified']
            self.error_count += batch_results['errors']
            
            # Log batch summary
            qualification_rate = (batch_results['qualified'] / batch_results['processed'] * 100) if batch_results['processed'] > 0 else 0
            logger.info(f"   📊 Batch {batch_num} complete: {batch_results['qualified']}/{batch_results['processed']} qualified ({qualification_rate:.1f}%)")
            logger.info(f"   📈 Average score: {batch_results['avg_score']:.1%}")
            
            # Progress update every 5 batches
            if batch_num % 5 == 0:
                overall_qualification_rate = (self.qualified_count / self.processed_count * 100) if self.processed_count > 0 else 0
                logger.info(f"🎯 PROGRESS: {self.processed_count} processed, {self.qualified_count} qualified ({overall_qualification_rate:.1f}% rate)")
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("📊 JOB 1 COMPLETE - Historical Lead Scoring")
        logger.info(f"   ⏱️ Duration: {duration}")
        logger.info(f"   📊 Total processed: {self.processed_count}")
        logger.info(f"   ✅ Qualified: {self.qualified_count}")
        logger.info(f"   ❌ Errors: {self.error_count}")
        
        if self.processed_count > 0:
            overall_rate = (self.qualified_count / self.processed_count * 100)
            logger.info(f"   📈 Overall qualification rate: {overall_rate:.1f}%")
            logger.info(f"   ⚡ Processing rate: {self.processed_count / duration.total_seconds() * 60:.1f} contacts/minute")
        
        # Store summary in database
        summary = self.db.get_qualification_stats()
        logger.info(f"📊 Database summary: {summary}")
        
        logger.info("✅ Job 1 data ready for Job 2 analysis")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Historical Lead Scoring - Job 1')
    parser.add_argument('--api-url', default='http://localhost:8080', help='Qualification API URL')
    parser.add_argument('--days', type=int, default=30, help='Days back to analyze')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')
    parser.add_argument('--test', action='store_true', help='Test mode (process only 20 contacts)')
    
    args = parser.parse_args()
    
    # Test API connectivity first
    try:
        response = requests.get(f"{args.api_url}/health", timeout=10)
        if response.status_code != 200:
            logger.error(f"❌ API not accessible at {args.api_url}")
            sys.exit(1)
        logger.info(f"✅ API health check passed")
    except Exception as e:
        logger.error(f"❌ API connection failed: {e}")
        logger.info("💡 Make sure to start the API first: python api/qualification_api.py")
        sys.exit(1)
    
    scorer = HistoricalLeadScorer(
        api_base_url=args.api_url,
        batch_size=args.batch_size
    )
    
    if args.test:
        logger.info("🧪 Running in TEST MODE - processing 20 contacts only")
        # Get test batch and limit to 20
        contacts = scorer.get_historical_contacts(args.days)[:20]
        if contacts:
            scorer.process_batch(contacts)
    else:
        scorer.run_historical_scoring(args.days)

if __name__ == "__main__":
    main()