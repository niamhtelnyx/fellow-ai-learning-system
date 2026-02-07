# Weekend Backtest System
**Validate Business Context Qualification Model Against Real AE Decisions**

## 🎯 Overview

This backtest system validates our business context qualification model by:
1. **Job 1**: Scoring all contacts from the last 30 days using the qualification model
2. **Job 2**: Analyzing which contacts progressed to deals beyond Stage 1 and comparing model reasoning with AE reasoning

**Key Questions Answered**:
- Does the model correctly identify prospects that AEs actually progress?
- How well does model reasoning align with AE reasoning?
- What's the false positive/negative rate compared to real outcomes?
- Which business context patterns correlate with actual deal progression?

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│     JOB 1       │    │   SHARED DB     │    │     JOB 2       │
│ Historical      │───▶│ backtest_       │◀───│ Deal Analysis   │
│ Lead Scoring    │    │ results.db      │    │ Agent           │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Salesforce      │    │ Lead            │    │ Opportunity     │
│ Contacts API    │    │ Qualifications  │    │ Progression     │
│ (30 days)       │    │ Results         │    │ Analysis        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Business Context│    │ Model Scores &  │    │ AE Reasoning &  │
│ Qualification   │    │ Reasoning       │    │ Stage Progress  │
│ API             │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Setup
```bash
cd backtest/
chmod +x setup_backtest.sh
./setup_backtest.sh
```

### 2. Start API (if not running)
```bash
cd ../api/
python3 qualification_api.py &
cd ../backtest/
```

### 3. Run Backtest

**Test Run** (7 days, small dataset):
```bash
python3 weekend_backtest.py --test
```

**Full Backtest** (30 days):
```bash
python3 weekend_backtest.py --days 30
```

**Production Run** (60 days):
```bash
python3 weekend_backtest.py --days 60
```

## 📊 What Each Job Does

### Job 1: Historical Lead Scoring
**File**: `job1_historical_scoring.py`

**Process**:
1. Queries Salesforce for contacts created in last N days
2. Extracts business domain from email or account website
3. Calls qualification API for each contact
4. Stores qualification score, confidence, business context, reasoning
5. Processes in batches with rate limiting

**Output**:
- Qualification scores (0-100%)
- Business context (industries, use cases, enterprise indicators)
- Model reasoning for each decision
- Processing metrics and logs

**Example Log**:
```
📊 Processing batch 5/20 (10 contacts)
🧠 Scoring John Smith @ acme-corp.com
   📊 ✅ QUALIFIED | 82.4% | HIGH CONFIDENCE
   🔍 BUSINESS CONTEXT: Technology, API/Integration, SaaS/Platform
📊 Batch 5 complete: 7/10 qualified (70.0%)
```

### Job 2: Deal Progression Analysis Agent
**File**: `job2_deal_analysis.py`

**Process**:
1. Monitors Job 1 output for newly scored contacts
2. Queries Salesforce for opportunities on contact's account
3. Determines if deals progressed beyond Stage 1
4. Extracts AE reasoning from opportunity fields
5. Calculates alignment score between model and AE reasoning
6. Runs continuously, analyzing as data becomes available

**Output**:
- Deal progression status (beyond Stage 1 or not)
- AE reasoning extraction from opportunity data
- Model-AE alignment scores
- Performance analysis (true/false positives/negatives)

**Example Log**:
```
🔍 Analyzing Sarah Johnson @ TechCorp Inc
   📊 Model: ✅ QUALIFIED | AE: ✅ PROGRESSED | Alignment: 0.85
   💡 Model correctly identified qualified prospect - AE progressed deal
```

## 🗄️ Database Schema

### `lead_qualifications` table
Stores Job 1 results:
```sql
- contact_id (Salesforce ID)
- qualification_score (0.0-1.0)
- is_qualified (boolean)
- confidence (HIGH/CONFIDENT/UNCERTAIN/LOW)
- industries (Technology, Healthcare, etc.)
- use_cases (Voice/Communication, API/Integration, etc.)
- reasoning (Model explanation)
- business_signals (Raw feature data)
```

### `deal_progressions` table
Stores Job 2 results:
```sql
- contact_id (links to lead_qualifications)
- opportunity_id (Salesforce Opportunity ID)
- beyond_stage_one (boolean)
- ae_owner (AE name)
- ae_progression_reason (extracted from opportunity)
- alignment_score (0.0-1.0)
- analysis_notes (interpretation)
```

### `backtest_summary` table
Aggregated results:
```sql
- total_contacts
- model_qualified / model_not_qualified
- deals_beyond_stage_one
- model_accuracy / precision / recall
- ae_model_alignment_avg
```

## 📈 Real-Time Monitoring

The coordinator provides real-time updates:

```
📊 WEEKEND BACKTEST STATUS UPDATE
   ⏱️ Runtime: 2:34:15
   📈 Job 1 (Scoring): 487 processed, 127 qualified (26.1%)
   🔍 Job 2 (Analysis): 143 analyzed, 45 progressed beyond Stage 1
   🎯 Model-AE Alignment: 0.73
   ⚡ Scoring rate: 194 contacts/hour
   ⚡ Analysis rate: 67 contacts/hour
```

## 📋 Individual Job Usage

### Run Job 1 Independently
```bash
# Test with 20 contacts
python3 job1_historical_scoring.py --test

# Full run with custom parameters
python3 job1_historical_scoring.py --days 30 --batch-size 10 --api-url http://localhost:8080

# Check logs
tail -f job1_historical_scoring.log
```

### Run Job 2 Independently
```bash
# Analyze once
python3 job2_deal_analysis.py --once

# Run continuously (monitors Job 1 output)
python3 job2_deal_analysis.py --interval 60

# Check logs
tail -f job2_deal_analysis.log
```

## 📊 Results Analysis

### Query Results Directly
```python
from backtest_database import BacktestDatabase

db = BacktestDatabase()

# Get overall stats
stats = db.get_qualification_stats()
print(f"Qualification rate: {stats['qualification_rate']:.1f}%")

# Get backtest summary
summary = db.get_backtest_summary()
print(f"Model accuracy: {summary.get('model_accuracy', 0):.1%}")
```

### SQLite Queries
```bash
sqlite3 backtest_results.db

# Top qualified prospects
SELECT contact_name, company_name, qualification_score, confidence, industries 
FROM lead_qualifications 
WHERE is_qualified = 1 
ORDER BY qualification_score DESC 
LIMIT 10;

# Model vs AE alignment
SELECT 
  AVG(alignment_score) as avg_alignment,
  COUNT(*) as total_analyzed
FROM deal_progressions;

# Confusion matrix
SELECT 
  lq.is_qualified as model_qualified,
  dp.beyond_stage_one as ae_progressed,
  COUNT(*) as count
FROM lead_qualifications lq
JOIN deal_progressions dp ON lq.contact_id = dp.contact_id
GROUP BY lq.is_qualified, dp.beyond_stage_one;
```

## 🎯 Expected Results

### Success Indicators
- **Qualification Rate**: 20-40% (conservative, appropriate)
- **Model Accuracy**: >70% (better than random)
- **Model-AE Alignment**: >0.6 (reasonable agreement)
- **Processing Rate**: 100+ contacts/hour

### Pattern Discovery
- **Enterprise prospects** should score 70-90%
- **Small business** should score 20-40%
- **Technology companies** should score higher than average
- **API/Integration use cases** should correlate with progression

### Business Insights
- Which industries have highest progression rates?
- What business context patterns AEs actually progress?
- Where does demographic scoring fail vs business context?
- Which confidence levels correlate with AE decisions?

## 🚨 Troubleshooting

### API Connection Issues
```bash
# Check if API is running
curl http://localhost:8080/health

# Start API if needed
cd ../api && python3 qualification_api.py &
```

### Salesforce Connectivity
```bash
# Check SF CLI authentication
sf org list

# Re-authenticate if needed
sf org login web
```

### Database Issues
```bash
# Reset database
rm backtest_results.db
python3 -c "from backtest_database import BacktestDatabase; BacktestDatabase()"
```

### Performance Issues
```bash
# Reduce batch size
python3 job1_historical_scoring.py --batch-size 5

# Increase check interval
python3 job2_deal_analysis.py --interval 120
```

## 📄 Output Files

After running, you'll have:

- **`backtest_results.db`** - SQLite database with all results
- **`weekend_backtest.log`** - Coordinator logs
- **`job1_historical_scoring.log`** - Lead scoring logs
- **`job2_deal_analysis.log`** - Deal analysis logs

## 🎯 Success Metrics

### Model Validation
- **True Positives**: Model qualified, AE progressed → Good!
- **True Negatives**: Model didn't qualify, AE didn't progress → Good!
- **False Positives**: Model qualified, AE didn't progress → Wasted AE time
- **False Negatives**: Model didn't qualify, AE progressed → Missed opportunities

### Business Impact
- **AE Time Savings**: Reduced false positives
- **Opportunity Capture**: Minimized false negatives
- **Routing Efficiency**: Right leads to right AEs
- **Qualification Speed**: Faster than manual review

## 🚀 Next Steps After Backtest

1. **Analyze Results**: Review accuracy, alignment, patterns
2. **Tune Thresholds**: Optimize qualification cutoffs
3. **A/B Test**: Run parallel with current system
4. **Production Deploy**: Replace Clearbit with business context
5. **Continuous Learning**: Use AE feedback to improve model

## 💡 Pro Tips

- **Start with test mode** to validate setup
- **Monitor logs in real-time** with `tail -f`
- **Run over weekend** for full 30-day analysis without disruption
- **Check API health** before long runs
- **Keep Salesforce CLI authenticated** for uninterrupted access

---

**This backtest validates that business context qualification outperforms demographic scoring for modern sales qualification needs!** 🎯