#!/usr/bin/env python3
"""
JOB 2: Deal Progression Analysis Agent
Continuously analyze qualified contacts to see if they progressed to deals beyond Stage 1
Compare model reasoning with AE reasoning
"""

import subprocess
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import re
try:
    from backtest_database import BacktestDatabase
except ImportError:
    import sys
    sys.path.append('.')
    from backtest_database import BacktestDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - JOB2 - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job2_deal_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DealAnalysisAgent:
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval  # Check every minute
        self.db = BacktestDatabase()
        self.analyzed_count = 0
        self.alignment_scores = []
        
    def get_account_opportunities(self, account_id: str) -> List[Dict]:
        """Get opportunities for a specific account"""
        try:
            soql = f"""
                SELECT Id, Name, StageName, Amount, CloseDate, OwnerId, Owner.Name,
                       CreatedDate, Description, NextStep, Loss_Reason__c, Win_Reason__c,
                       Type, LeadSource, AccountId
                FROM Opportunity 
                WHERE AccountId = '{account_id}'
                AND CreatedDate >= LAST_N_DAYS:60
                ORDER BY CreatedDate DESC
            """
            
            result = subprocess.run([
                'sf', 'data', 'query',
                '--query', soql,
                '--target-org', 'niamh@telnyx.com',
                '--json'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                opportunities = data.get('result', {}).get('records', [])
                return opportunities
            else:
                logger.error(f"❌ Opportunity query failed for account {account_id}: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting opportunities for account {account_id}: {e}")
            return []
    
    def is_beyond_stage_one(self, stage_name: str) -> bool:
        """Determine if opportunity progressed beyond Stage 1"""
        if not stage_name:
            return False
            
        stage_lower = stage_name.lower()
        
        # Stage 1 indicators (not progressed)
        stage_one_indicators = [
            'lead', 'prospect', 'qualification', 'initial', 'discovery',
            'cold', 'unqualified', 'inquiry', 'marketing', 'nurture'
        ]
        
        # Beyond Stage 1 indicators
        beyond_stage_one_indicators = [
            'demo', 'proposal', 'evaluation', 'negotiation', 'contract',
            'closed won', 'closed lost', 'technical', 'poc', 'trial',
            'proof of concept', 'decision', 'purchase', 'implementation'
        ]
        
        # Check for beyond stage 1
        for indicator in beyond_stage_one_indicators:
            if indicator in stage_lower:
                return True
        
        # If it contains stage 1 indicators, it's not beyond
        for indicator in stage_one_indicators:
            if indicator in stage_lower:
                return False
        
        # Default: if we can't determine, assume it's beyond stage 1
        # (since most CRMs use stage names like "Stage 2", "Stage 3", etc.)
        return True
    
    def extract_ae_reasoning(self, opportunity: Dict) -> str:
        """Extract AE reasoning from opportunity fields"""
        reasoning_parts = []
        
        # Stage progression indicates reasoning
        stage = opportunity.get('StageName', '')
        if stage:
            reasoning_parts.append(f"Stage: {stage}")
        
        # NextStep field often contains AE thinking
        next_step = opportunity.get('NextStep', '')
        if next_step:
            reasoning_parts.append(f"Next step: {next_step}")
        
        # Description field may have notes
        description = opportunity.get('Description', '')
        if description:
            reasoning_parts.append(f"Notes: {description[:200]}...")
        
        # Win/Loss reasons
        win_reason = opportunity.get('Win_Reason__c', '')
        loss_reason = opportunity.get('Loss_Reason__c', '')
        
        if win_reason:
            reasoning_parts.append(f"Win reason: {win_reason}")
        if loss_reason:
            reasoning_parts.append(f"Loss reason: {loss_reason}")
        
        # Opportunity type
        opp_type = opportunity.get('Type', '')
        if opp_type:
            reasoning_parts.append(f"Type: {opp_type}")
        
        return '; '.join(reasoning_parts) if reasoning_parts else 'No AE reasoning available'
    
    def calculate_alignment_score(self, model_reasoning: str, ae_reasoning: str, 
                                 model_qualified: bool, beyond_stage_one: bool) -> float:
        """Calculate alignment score between model and AE reasoning"""
        
        # Base alignment from qualification decision
        decision_alignment = 1.0 if (model_qualified == beyond_stage_one) else 0.0
        
        if not model_reasoning or not ae_reasoning:
            return decision_alignment
        
        # Convert to lowercase for comparison
        model_lower = model_reasoning.lower()
        ae_lower = ae_reasoning.lower()
        
        # Look for reasoning alignment
        reasoning_alignment = 0.0
        alignment_indicators = 0
        total_indicators = 0
        
        # Technology alignment
        total_indicators += 1
        if ('technology' in model_lower or 'tech' in model_lower) and \
           ('technology' in ae_lower or 'tech' in ae_lower):
            alignment_indicators += 1
            reasoning_alignment += 0.2
        
        # Enterprise signals
        total_indicators += 1
        if ('enterprise' in model_lower or 'large' in model_lower) and \
           ('enterprise' in ae_lower or 'corporate' in ae_lower):
            alignment_indicators += 1
            reasoning_alignment += 0.2
        
        # API/Integration use cases
        total_indicators += 1
        if ('api' in model_lower or 'integration' in model_lower) and \
           ('api' in ae_lower or 'integration' in ae_lower or 'technical' in ae_lower):
            alignment_indicators += 1
            reasoning_alignment += 0.2
        
        # Voice/Communication use cases
        total_indicators += 1
        if ('voice' in model_lower or 'communication' in model_lower) and \
           ('voice' in ae_lower or 'call' in ae_lower or 'communication' in ae_lower):
            alignment_indicators += 1
            reasoning_alignment += 0.2
        
        # AI/Automation signals
        total_indicators += 1
        if ('ai' in model_lower or 'automation' in model_lower) and \
           ('ai' in ae_lower or 'automation' in ae_lower or 'intelligent' in ae_lower):
            alignment_indicators += 1
            reasoning_alignment += 0.2
        
        # Combine decision alignment (70%) and reasoning alignment (30%)
        final_score = (decision_alignment * 0.7) + (reasoning_alignment * 0.3)
        
        return min(1.0, final_score)
    
    def analyze_contact_progression(self, contact_data: Dict) -> Dict:
        """Analyze a single contact's deal progression"""
        try:
            contact_id = contact_data['contact_id']
            account_id = contact_data['account_id']
            
            logger.info(f"🔍 Analyzing {contact_data['contact_name']} @ {contact_data['company_name']}")
            
            # Get opportunities for this account
            opportunities = self.get_account_opportunities(account_id)
            
            if not opportunities:
                # No opportunities found - contact didn't progress
                return {
                    'contact_id': contact_id,
                    'account_id': account_id,
                    'opportunity_id': None,
                    'opportunity_name': None,
                    'stage_name': 'No Opportunity',
                    'beyond_stage_one': False,
                    'ae_owner': None,
                    'ae_progression_reason': 'No opportunity created',
                    'close_date': None,
                    'amount': None,
                    'win_reason': None,
                    'loss_reason': None,
                    'model_score': contact_data['qualification_score'],
                    'model_qualified': contact_data['is_qualified'],
                    'model_reasoning': contact_data['reasoning'],
                    'alignment_score': 1.0 if not contact_data['is_qualified'] else 0.0,  # Model correctly predicted no progression
                    'analysis_notes': 'No opportunities found - model prediction accuracy depends on qualification'
                }
            
            # Analyze the most recent/relevant opportunity
            best_opportunity = opportunities[0]  # Most recent
            
            # Find the most advanced opportunity if multiple exist
            for opp in opportunities:
                if self.is_beyond_stage_one(opp.get('StageName', '')):
                    best_opportunity = opp
                    break
            
            beyond_stage_one = self.is_beyond_stage_one(best_opportunity.get('StageName', ''))
            ae_reasoning = self.extract_ae_reasoning(best_opportunity)
            
            # Calculate alignment between model and AE
            alignment_score = self.calculate_alignment_score(
                contact_data['reasoning'],
                ae_reasoning,
                contact_data['is_qualified'],
                beyond_stage_one
            )
            
            # Generate analysis notes
            analysis_notes = []
            
            if contact_data['is_qualified'] and beyond_stage_one:
                analysis_notes.append("✅ Model correctly identified qualified prospect - AE progressed deal")
            elif not contact_data['is_qualified'] and not beyond_stage_one:
                analysis_notes.append("✅ Model correctly identified unqualified prospect - no progression")
            elif contact_data['is_qualified'] and not beyond_stage_one:
                analysis_notes.append("❌ Model false positive - qualified but AE didn't progress")
            else:
                analysis_notes.append("⚠️ Model false negative - didn't qualify but AE progressed")
            
            analysis_notes.append(f"Alignment score: {alignment_score:.2f}")
            
            return {
                'contact_id': contact_id,
                'account_id': account_id,
                'opportunity_id': best_opportunity.get('Id'),
                'opportunity_name': best_opportunity.get('Name'),
                'stage_name': best_opportunity.get('StageName'),
                'beyond_stage_one': beyond_stage_one,
                'ae_owner': best_opportunity.get('Owner', {}).get('Name'),
                'ae_progression_reason': ae_reasoning,
                'close_date': best_opportunity.get('CloseDate'),
                'amount': best_opportunity.get('Amount'),
                'win_reason': best_opportunity.get('Win_Reason__c'),
                'loss_reason': best_opportunity.get('Loss_Reason__c'),
                'model_score': contact_data['qualification_score'],
                'model_qualified': contact_data['is_qualified'],
                'model_reasoning': contact_data['reasoning'],
                'alignment_score': alignment_score,
                'analysis_notes': '; '.join(analysis_notes)
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing contact {contact_data['contact_id']}: {e}")
            return {
                'contact_id': contact_data['contact_id'],
                'account_id': contact_data['account_id'],
                'analysis_notes': f'Analysis error: {str(e)}',
                'alignment_score': 0.0
            }
    
    def run_analysis_cycle(self):
        """Run one analysis cycle"""
        logger.info("🔄 Running deal progression analysis cycle...")
        
        # Get contacts that need analysis
        pending_contacts = self.db.get_pending_deal_analysis(limit=20)
        
        if not pending_contacts:
            logger.info("📭 No contacts pending analysis")
            return
        
        logger.info(f"📊 Analyzing {len(pending_contacts)} contacts...")
        
        cycle_alignments = []
        
        for contact in pending_contacts:
            # Analyze progression
            analysis_result = self.analyze_contact_progression(contact)
            
            # Store in database
            self.db.store_deal_analysis(analysis_result)
            
            # Track metrics
            self.analyzed_count += 1
            alignment_score = analysis_result.get('alignment_score', 0)
            cycle_alignments.append(alignment_score)
            self.alignment_scores.append(alignment_score)
            
            # Log result
            model_status = "✅ QUALIFIED" if contact['is_qualified'] else "❌ NOT QUALIFIED"
            ae_status = "✅ PROGRESSED" if analysis_result.get('beyond_stage_one') else "❌ NO PROGRESS"
            
            logger.info(f"   📊 Model: {model_status} | AE: {ae_status} | Alignment: {alignment_score:.2f}")
            logger.info(f"   💡 {analysis_result.get('analysis_notes', 'No notes')[:100]}...")
            
            # Rate limiting
            time.sleep(2)
        
        # Cycle summary
        avg_alignment = sum(cycle_alignments) / len(cycle_alignments) if cycle_alignments else 0
        logger.info(f"📊 Cycle complete: {len(pending_contacts)} analyzed, avg alignment: {avg_alignment:.2f}")
    
    def run_continuous_analysis(self):
        """Run continuous analysis monitoring Job 1 output"""
        logger.info("🚀 Starting Deal Progression Analysis Agent (Job 2)")
        logger.info(f"   🔄 Check interval: {self.check_interval} seconds")
        logger.info("   📊 Monitoring Job 1 output for new contacts to analyze")
        
        start_time = datetime.now()
        
        try:
            while True:
                self.run_analysis_cycle()
                
                # Progress summary every 10 analyses
                if self.analyzed_count > 0 and self.analyzed_count % 10 == 0:
                    avg_alignment = sum(self.alignment_scores) / len(self.alignment_scores)
                    runtime = datetime.now() - start_time
                    
                    logger.info(f"🎯 PROGRESS: {self.analyzed_count} analyzed, avg alignment: {avg_alignment:.2f}")
                    logger.info(f"   ⏱️ Runtime: {runtime}")
                    logger.info(f"   📈 Analysis rate: {self.analyzed_count / runtime.total_seconds() * 60:.1f} contacts/minute")
                
                # Wait for next cycle
                logger.debug(f"⏱️ Waiting {self.check_interval} seconds until next check...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Deal analysis agent stopped by user")
            self.print_final_summary()
        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            logger.info(f"⏱️ Retrying in {self.check_interval} seconds...")
            time.sleep(self.check_interval)
    
    def print_final_summary(self):
        """Print final analysis summary"""
        logger.info("📊 FINAL ANALYSIS SUMMARY")
        logger.info(f"   📈 Total analyzed: {self.analyzed_count}")
        
        if self.alignment_scores:
            avg_alignment = sum(self.alignment_scores) / len(self.alignment_scores)
            logger.info(f"   🎯 Average alignment: {avg_alignment:.2f}")
            logger.info(f"   📊 High alignment (>0.8): {sum(1 for s in self.alignment_scores if s > 0.8)}")
            logger.info(f"   ⚠️ Low alignment (<0.4): {sum(1 for s in self.alignment_scores if s < 0.4)}")
        
        # Get database summary
        summary = self.db.get_backtest_summary()
        logger.info(f"📊 Database summary: {summary}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deal Progression Analysis Agent - Job 2')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run analysis once instead of continuous')
    
    args = parser.parse_args()
    
    agent = DealAnalysisAgent(check_interval=args.interval)
    
    if args.once:
        agent.run_analysis_cycle()
        agent.print_final_summary()
    else:
        agent.run_continuous_analysis()

if __name__ == "__main__":
    main()