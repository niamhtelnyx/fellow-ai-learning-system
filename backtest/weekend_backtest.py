#!/usr/bin/env python3
"""
Weekend Backtest Coordinator
Runs both jobs in parallel and provides real-time monitoring
"""

import subprocess
import time
import logging
import threading
from datetime import datetime
import json
import sys
try:
    from backtest_database import BacktestDatabase
except ImportError:
    import sys
    sys.path.append('.')
    from backtest_database import BacktestDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - COORDINATOR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weekend_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WeekendBacktestCoordinator:
    def __init__(self, api_url: str = "http://localhost:8080", days_back: int = 30):
        self.api_url = api_url
        self.days_back = days_back
        self.db = BacktestDatabase()
        self.job1_process = None
        self.job2_process = None
        self.start_time = None
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check API connectivity
        try:
            import requests
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Qualification API is accessible")
            else:
                logger.error(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to API at {self.api_url}: {e}")
            logger.info("💡 Start API with: cd api && python qualification_api.py")
            return False
        
        # Check Salesforce CLI
        try:
            result = subprocess.run(['sf', 'org', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Salesforce CLI is configured")
            else:
                logger.error("❌ Salesforce CLI not configured")
                return False
        except FileNotFoundError:
            logger.error("❌ Salesforce CLI not installed")
            return False
        
        # Check database
        try:
            self.db.get_qualification_stats()
            logger.info("✅ Database is accessible")
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            return False
        
        logger.info("✅ All prerequisites met")
        return True
    
    def start_job1(self):
        """Start Job 1 - Historical Lead Scoring"""
        logger.info("🚀 Starting Job 1 - Historical Lead Scoring")
        
        cmd = [
            'python3', 'job1_historical_scoring.py',
            '--api-url', self.api_url,
            '--days', str(self.days_back),
            '--batch-size', '10'
        ]
        
        self.job1_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        logger.info(f"✅ Job 1 started (PID: {self.job1_process.pid})")
    
    def start_job2(self):
        """Start Job 2 - Deal Analysis Agent"""
        logger.info("🚀 Starting Job 2 - Deal Progression Analysis")
        
        # Wait 2 minutes before starting Job 2 to let Job 1 generate some data
        logger.info("⏱️ Waiting 2 minutes for Job 1 to generate initial data...")
        time.sleep(120)
        
        cmd = [
            'python3', 'job2_deal_analysis.py',
            '--interval', '60'  # Check every minute
        ]
        
        self.job2_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        logger.info(f"✅ Job 2 started (PID: {self.job2_process.pid})")
    
    def monitor_job1_output(self):
        """Monitor Job 1 output in real-time"""
        if not self.job1_process:
            return
        
        logger.info("👁️ Monitoring Job 1 output...")
        
        for line in iter(self.job1_process.stdout.readline, ''):
            if line:
                logger.info(f"JOB1: {line.strip()}")
            
            # Check if process ended
            if self.job1_process.poll() is not None:
                break
        
        logger.info("📋 Job 1 monitoring ended")
    
    def monitor_job2_output(self):
        """Monitor Job 2 output in real-time"""
        if not self.job2_process:
            return
        
        logger.info("👁️ Monitoring Job 2 output...")
        
        for line in iter(self.job2_process.stdout.readline, ''):
            if line:
                logger.info(f"JOB2: {line.strip()}")
            
            # Check if process ended
            if self.job2_process.poll() is not None:
                break
        
        logger.info("📋 Job 2 monitoring ended")
    
    def print_status_update(self):
        """Print periodic status update"""
        try:
            # Get current stats
            qual_stats = self.db.get_qualification_stats()
            backtest_summary = self.db.get_backtest_summary()
            runtime = datetime.now() - self.start_time
            
            logger.info("📊 WEEKEND BACKTEST STATUS UPDATE")
            logger.info(f"   ⏱️ Runtime: {runtime}")
            
            # Job 1 stats
            logger.info(f"   📈 Job 1 (Scoring): {qual_stats['total_processed']} processed, {qual_stats['qualified']} qualified ({qual_stats['qualification_rate']:.1f}%)")
            
            # Job 2 stats
            analyzed = backtest_summary['analyzed_contacts']
            progressed = backtest_summary['deals_progressed']
            avg_alignment = backtest_summary.get('avg_alignment_score', 0)
            
            logger.info(f"   🔍 Job 2 (Analysis): {analyzed} analyzed, {progressed} progressed beyond Stage 1")
            logger.info(f"   🎯 Model-AE Alignment: {avg_alignment:.2f}")
            
            # Calculate processing rates
            if runtime.total_seconds() > 0:
                scoring_rate = qual_stats['total_processed'] / runtime.total_seconds() * 3600  # per hour
                analysis_rate = analyzed / runtime.total_seconds() * 3600  # per hour
                
                logger.info(f"   ⚡ Scoring rate: {scoring_rate:.0f} contacts/hour")
                logger.info(f"   ⚡ Analysis rate: {analysis_rate:.0f} contacts/hour")
            
        except Exception as e:
            logger.error(f"❌ Error getting status update: {e}")
    
    def run_weekend_backtest(self):
        """Run the complete weekend backtest"""
        logger.info("🎯 STARTING WEEKEND BACKTEST")
        logger.info("=" * 60)
        logger.info(f"📅 Analyzing last {self.days_back} days of contacts")
        logger.info(f"🌐 API endpoint: {self.api_url}")
        logger.info("🔄 Jobs will run in parallel:")
        logger.info("   Job 1: Score historical contacts")
        logger.info("   Job 2: Analyze deal progression")
        
        self.start_time = datetime.now()
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites not met - aborting")
            return
        
        try:
            # Start Job 1 (historical scoring)
            self.start_job1()
            
            # Start monitoring threads
            job1_thread = threading.Thread(target=self.monitor_job1_output, daemon=True)
            job1_thread.start()
            
            # Start Job 2 (deal analysis) after delay
            job2_thread = threading.Thread(target=self.start_job2, daemon=True)
            job2_thread.start()
            
            # Wait for Job 2 to start, then start its monitoring
            time.sleep(150)  # Wait for Job 2 startup
            
            job2_monitor_thread = threading.Thread(target=self.monitor_job2_output, daemon=True)
            job2_monitor_thread.start()
            
            # Periodic status updates every 10 minutes
            last_status_update = time.time()
            
            while True:
                # Check if both jobs are still running
                job1_running = (self.job1_process and self.job1_process.poll() is None)
                job2_running = (self.job2_process and self.job2_process.poll() is None)
                
                # Status update every 10 minutes
                if time.time() - last_status_update > 600:  # 10 minutes
                    self.print_status_update()
                    last_status_update = time.time()
                
                # If Job 1 finished, wait for Job 2 to process remaining data
                if not job1_running and job2_running:
                    logger.info("📋 Job 1 completed - waiting for Job 2 to finish analysis...")
                
                # If both jobs finished, we're done
                if not job1_running and not job2_running:
                    logger.info("✅ Both jobs completed")
                    break
                
                # Sleep before next check
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("🛑 Weekend backtest interrupted by user")
            self.cleanup_processes()
        except Exception as e:
            logger.error(f"❌ Backtest error: {e}")
            self.cleanup_processes()
        
        # Final summary
        self.print_final_summary()
    
    def cleanup_processes(self):
        """Clean up running processes"""
        logger.info("🧹 Cleaning up processes...")
        
        if self.job1_process and self.job1_process.poll() is None:
            self.job1_process.terminate()
            logger.info("🛑 Job 1 terminated")
        
        if self.job2_process and self.job2_process.poll() is None:
            self.job2_process.terminate()
            logger.info("🛑 Job 2 terminated")
    
    def print_final_summary(self):
        """Print comprehensive final summary"""
        try:
            runtime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            qual_stats = self.db.get_qualification_stats()
            backtest_summary = self.db.get_backtest_summary()
            
            logger.info("🎯 WEEKEND BACKTEST FINAL SUMMARY")
            logger.info("=" * 60)
            logger.info(f"⏱️ Total Runtime: {runtime}")
            logger.info("")
            
            # Job 1 Results
            logger.info("📊 JOB 1 - HISTORICAL LEAD SCORING RESULTS")
            logger.info(f"   📈 Contacts processed: {qual_stats['total_processed']}")
            logger.info(f"   ✅ Qualified contacts: {qual_stats['qualified']}")
            logger.info(f"   📊 Qualification rate: {qual_stats['qualification_rate']:.1f}%")
            logger.info(f"   🎯 Average score: {qual_stats['avg_score']:.1%}")
            logger.info(f"   🔥 High confidence: {qual_stats['high_confidence']}")
            logger.info(f"   ⚠️ Low confidence: {qual_stats['low_confidence']}")
            logger.info("")
            
            # Job 2 Results
            analyzed = backtest_summary['analyzed_contacts']
            progressed = backtest_summary['deals_progressed']
            avg_alignment = backtest_summary.get('avg_alignment_score', 0)
            
            logger.info("🔍 JOB 2 - DEAL PROGRESSION ANALYSIS RESULTS")
            logger.info(f"   📈 Contacts analyzed: {analyzed}")
            logger.info(f"   🚀 Deals progressed beyond Stage 1: {progressed}")
            logger.info(f"   📊 Progression rate: {(progressed/analyzed*100):.1f}%" if analyzed > 0 else "   📊 Progression rate: N/A")
            logger.info(f"   🎯 Model-AE Alignment: {avg_alignment:.2f}")
            logger.info("")
            
            # Model Performance Analysis
            if 'confusion_matrix' in backtest_summary and backtest_summary['confusion_matrix']:
                logger.info("🧠 MODEL PERFORMANCE ANALYSIS")
                
                # Calculate confusion matrix metrics
                tp = fp = tn = fn = 0
                for model_qual, actual_prog, count in backtest_summary['confusion_matrix']:
                    if model_qual and actual_prog: tp = count  # True Positive
                    elif model_qual and not actual_prog: fp = count  # False Positive
                    elif not model_qual and not actual_prog: tn = count  # True Negative
                    elif not model_qual and actual_prog: fn = count  # False Negative
                
                total = tp + fp + tn + fn
                if total > 0:
                    accuracy = (tp + tn) / total
                    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                    
                    logger.info(f"   ✅ True Positives: {tp} (model qualified, AE progressed)")
                    logger.info(f"   ❌ False Positives: {fp} (model qualified, AE didn't progress)")
                    logger.info(f"   ✅ True Negatives: {tn} (model didn't qualify, AE didn't progress)")
                    logger.info(f"   ❌ False Negatives: {fn} (model didn't qualify, AE progressed)")
                    logger.info(f"   🎯 Accuracy: {accuracy:.1%}")
                    logger.info(f"   🎯 Precision: {precision:.1%}")
                    logger.info(f"   🎯 Recall: {recall:.1%}")
                logger.info("")
            
            # Business Impact
            logger.info("💰 BUSINESS IMPACT ANALYSIS")
            if qual_stats['total_processed'] > 0:
                qualified_rate = qual_stats['qualification_rate']
                if qualified_rate < 50:
                    logger.info(f"   🎯 Conservative qualification ({qualified_rate:.1f}%) reduces AE time waste")
                else:
                    logger.info(f"   ⚡ Active qualification ({qualified_rate:.1f}%) generates more opportunities")
            
            if avg_alignment > 0.7:
                logger.info(f"   ✅ High model-AE alignment ({avg_alignment:.2f}) validates approach")
            elif avg_alignment > 0.5:
                logger.info(f"   ⚠️ Moderate alignment ({avg_alignment:.2f}) - model needs tuning")
            else:
                logger.info(f"   ❌ Low alignment ({avg_alignment:.2f}) - significant model issues")
            
            logger.info("")
            logger.info("📄 Detailed results saved in:")
            logger.info("   📊 Database: backtest_results.db")
            logger.info("   📋 Job 1 Log: job1_historical_scoring.log")
            logger.info("   📋 Job 2 Log: job2_deal_analysis.log")
            logger.info("   📋 Coordinator Log: weekend_backtest.log")
            logger.info("")
            logger.info("✅ Weekend backtest complete!")
            
        except Exception as e:
            logger.error(f"❌ Error generating final summary: {e}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Weekend Backtest Coordinator')
    parser.add_argument('--api-url', default='http://localhost:8080', help='Qualification API URL')
    parser.add_argument('--days', type=int, default=30, help='Days back to analyze')
    parser.add_argument('--test', action='store_true', help='Test mode (small dataset)')
    
    args = parser.parse_args()
    
    if args.test:
        logger.info("🧪 Running in TEST MODE")
        args.days = 7  # Only analyze last 7 days for testing
    
    coordinator = WeekendBacktestCoordinator(
        api_url=args.api_url,
        days_back=args.days
    )
    
    coordinator.run_weekend_backtest()

if __name__ == "__main__":
    main()