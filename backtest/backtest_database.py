#!/usr/bin/env python3
"""
Backtest Database Schema
Shared database for historical lead scoring and deal progression analysis
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class BacktestDatabase:
    def __init__(self, db_path: str = "backtest_results.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Job 1: Lead qualification results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lead_qualifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id TEXT NOT NULL,
                contact_name TEXT,
                company_name TEXT,
                email TEXT,
                domain TEXT,
                account_id TEXT,
                created_date TEXT,
                qualification_score REAL,
                is_qualified BOOLEAN,
                confidence TEXT,
                industries TEXT,
                use_cases TEXT,
                enterprise_indicators TEXT,
                reasoning TEXT,
                business_signals TEXT,
                content_length INTEGER,
                processed_at TEXT,
                UNIQUE(contact_id)
            )
        ''')
        
        # Job 2: Deal progression analysis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deal_progressions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id TEXT NOT NULL,
                account_id TEXT,
                opportunity_id TEXT,
                opportunity_name TEXT,
                stage_name TEXT,
                beyond_stage_one BOOLEAN,
                ae_owner TEXT,
                ae_progression_reason TEXT,
                close_date TEXT,
                amount REAL,
                win_reason TEXT,
                loss_reason TEXT,
                model_score REAL,
                model_qualified BOOLEAN,
                model_reasoning TEXT,
                alignment_score REAL,
                analysis_notes TEXT,
                analyzed_at TEXT,
                FOREIGN KEY (contact_id) REFERENCES lead_qualifications (contact_id)
            )
        ''')
        
        # Analysis summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_date TEXT,
                total_contacts INTEGER,
                model_qualified INTEGER,
                model_not_qualified INTEGER,
                deals_beyond_stage_one INTEGER,
                model_true_positives INTEGER,
                model_false_positives INTEGER,
                model_true_negatives INTEGER,
                model_false_negatives INTEGER,
                model_accuracy REAL,
                model_precision REAL,
                model_recall REAL,
                ae_model_alignment_avg REAL,
                insights TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_qualification_result(self, contact_data: Dict, qualification_result: Dict):
        """Store lead qualification result from Job 1"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO lead_qualifications 
            (contact_id, contact_name, company_name, email, domain, account_id,
             created_date, qualification_score, is_qualified, confidence,
             industries, use_cases, enterprise_indicators, reasoning,
             business_signals, content_length, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            contact_data['Id'],
            contact_data.get('Name'),
            contact_data.get('Account', {}).get('Name'),
            contact_data.get('Email'),
            qualification_result.get('domain'),
            contact_data.get('AccountId'),
            contact_data.get('CreatedDate'),
            qualification_result.get('qualification_score'),
            qualification_result.get('is_qualified'),
            qualification_result.get('confidence'),
            ', '.join(qualification_result.get('business_context', {}).get('industries', [])),
            ', '.join(qualification_result.get('business_context', {}).get('use_cases', [])),
            ', '.join(qualification_result.get('business_context', {}).get('enterprise_indicators', [])),
            '; '.join(qualification_result.get('reasoning', [])),
            json.dumps(qualification_result.get('business_signals', {})),
            qualification_result.get('content_analyzed', 0),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_pending_deal_analysis(self, limit: int = 10) -> List[Dict]:
        """Get contacts that need deal progression analysis (Job 2)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT lq.contact_id, lq.account_id, lq.qualification_score, 
                   lq.is_qualified, lq.reasoning, lq.contact_name, lq.company_name
            FROM lead_qualifications lq
            LEFT JOIN deal_progressions dp ON lq.contact_id = dp.contact_id
            WHERE dp.contact_id IS NULL
            ORDER BY lq.processed_at ASC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'contact_id': row[0],
            'account_id': row[1], 
            'qualification_score': row[2],
            'is_qualified': row[3],
            'reasoning': row[4],
            'contact_name': row[5],
            'company_name': row[6]
        } for row in results]
    
    def store_deal_analysis(self, analysis_result: Dict):
        """Store deal progression analysis from Job 2"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO deal_progressions
            (contact_id, account_id, opportunity_id, opportunity_name, 
             stage_name, beyond_stage_one, ae_owner, ae_progression_reason,
             close_date, amount, win_reason, loss_reason, model_score,
             model_qualified, model_reasoning, alignment_score, analysis_notes, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis_result['contact_id'],
            analysis_result['account_id'],
            analysis_result.get('opportunity_id'),
            analysis_result.get('opportunity_name'),
            analysis_result.get('stage_name'),
            analysis_result.get('beyond_stage_one'),
            analysis_result.get('ae_owner'),
            analysis_result.get('ae_progression_reason'),
            analysis_result.get('close_date'),
            analysis_result.get('amount'),
            analysis_result.get('win_reason'),
            analysis_result.get('loss_reason'),
            analysis_result.get('model_score'),
            analysis_result.get('model_qualified'),
            analysis_result.get('model_reasoning'),
            analysis_result.get('alignment_score'),
            analysis_result.get('analysis_notes'),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_backtest_summary(self) -> Dict:
        """Generate comprehensive backtest summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_contacts,
                SUM(CASE WHEN is_qualified = 1 THEN 1 ELSE 0 END) as model_qualified,
                AVG(qualification_score) as avg_score
            FROM lead_qualifications
        ''')
        
        total_stats = cursor.fetchone()
        
        # Deal progression stats
        cursor.execute('''
            SELECT 
                COUNT(*) as analyzed_contacts,
                SUM(CASE WHEN beyond_stage_one = 1 THEN 1 ELSE 0 END) as deals_progressed,
                AVG(alignment_score) as avg_alignment
            FROM deal_progressions
        ''')
        
        deal_stats = cursor.fetchone()
        
        # Confusion matrix
        cursor.execute('''
            SELECT 
                lq.is_qualified,
                dp.beyond_stage_one,
                COUNT(*) as count
            FROM lead_qualifications lq
            JOIN deal_progressions dp ON lq.contact_id = dp.contact_id
            GROUP BY lq.is_qualified, dp.beyond_stage_one
        ''')
        
        confusion_data = cursor.fetchall()
        conn.close()
        
        return {
            'total_contacts': total_stats[0],
            'model_qualified': total_stats[1],
            'avg_qualification_score': total_stats[2],
            'analyzed_contacts': deal_stats[0] if deal_stats[0] else 0,
            'deals_progressed': deal_stats[1] if deal_stats[1] else 0,
            'avg_alignment_score': deal_stats[2] if deal_stats[2] else 0,
            'confusion_matrix': confusion_data
        }
    
    def get_qualification_stats(self) -> Dict:
        """Get real-time qualification processing stats"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_processed,
                SUM(CASE WHEN is_qualified = 1 THEN 1 ELSE 0 END) as qualified,
                AVG(qualification_score) as avg_score,
                COUNT(CASE WHEN confidence = 'HIGH' THEN 1 END) as high_confidence,
                COUNT(CASE WHEN confidence = 'LOW' THEN 1 END) as low_confidence,
                MAX(processed_at) as last_processed
            FROM lead_qualifications
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total_processed': result[0],
            'qualified': result[1],
            'qualification_rate': (result[1] / result[0] * 100) if result[0] > 0 else 0,
            'avg_score': result[2],
            'high_confidence': result[3],
            'low_confidence': result[4],
            'last_processed': result[5]
        }

if __name__ == "__main__":
    # Test database setup
    db = BacktestDatabase()
    print("✅ Backtest database initialized")
    print("📊 Tables created: lead_qualifications, deal_progressions, backtest_summary")