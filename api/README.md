# Business Context Lead Qualification API

Production-ready API for qualifying leads using business context analysis instead of demographic data.

## 🎯 Overview

This API replaces Clearbit demographic scoring with conversation-style business intelligence:
- **80.6% accuracy** (vs 75% target)
- **Enterprise differentiation**: 83% enterprise vs 37% small business scores  
- **No demographic dependency**: Works for international, AI companies, startups
- **Real-time qualification**: Website → Business context → Qualification score

## 📊 Performance Validation

**Enterprise prospects** (should score HIGH):
- ✅ **Uber**: 83.0% qualified
- ✅ **Cisco**: 82.4% qualified  
- ✅ **OpenAI**: 82.4% qualified
- ✅ **Alibaba**: 86.7% qualified

**Small business** (should score LOW):
- ❌ **nest.agency**: 37.9% not qualified
- ❌ **astrobaja.com**: 35.7% not qualified
- ❌ **chefsipho.com**: 34.7% not qualified

## 🚀 Quick Start

### 1. Installation

```bash
cd api/
pip install -r requirements.txt
```

### 2. Start API Server

```bash
python qualification_api.py
```

Server runs on `http://localhost:8080`

### 3. Test API

```bash
python client_example.py
```

## 📡 API Endpoints

### Health Check
```
GET /health
```

### Single Lead Qualification
```
POST /qualify/domain

{
  "domain": "openai.com",
  "contact_name": "Sarah Johnson", 
  "company_name": "OpenAI"
}

Response:
{
  "qualification_score": 0.824,
  "is_qualified": true,
  "confidence": "HIGH",
  "business_context": {
    "industries": ["Technology"],
    "use_cases": ["AI/Automation", "API/Integration"],
    "enterprise_indicators": ["SaaS/Platform", "Innovation Leader"]
  },
  "reasoning": ["Industry: Technology", "Use cases: AI/Automation, API/Integration"]
}
```

### Batch Processing
```
POST /qualify/batch

{
  "leads": [
    {"domain": "uber.com", "contact_name": "Tom", "company_name": "Uber"},
    {"domain": "cisco.com", "contact_name": "Bob", "company_name": "Cisco"}
  ]
}
```

### Model Information
```
GET /model/info

Response:
{
  "model_version": "business_context_v1",
  "accuracy": 0.806,
  "training_samples": 144,
  "approach": "Business context analysis using Fellow.ai conversation patterns"
}
```

## 🔄 Background Scoring Service

Auto-score new Salesforce leads:

```bash
# Run continuously
python salesforce_background_scorer.py

# Run once
python salesforce_background_scorer.py --once

# Custom interval (default 5 minutes)
python salesforce_background_scorer.py --interval 600
```

**What it does**:
1. Queries Salesforce for new leads without business context scores
2. Extracts domains from email addresses or website fields
3. Calls qualification API for each lead
4. Updates Salesforce with scores and business context

**Salesforce fields created/updated**:
- `Business_Context_Score__c` (Number: 0.0-1.0)
- `Business_Context_Qualified__c` (Boolean)
- `Business_Context_Confidence__c` (Text: HIGH/CONFIDENT/UNCERTAIN/LOW)
- `Business_Context_Industries__c` (Text)
- `Business_Context_Use_Cases__c` (Text)

## 🐳 Docker Deployment

### Build & Run
```bash
# Build image
docker build -t business-context-api .

# Run container
docker run -p 8080:8080 business-context-api

# Run with volume (for model updates)
docker run -p 8080:8080 -v $(pwd):/app business-context-api
```

### Docker Compose
```yaml
version: '3.8'
services:
  qualification-api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
    
  background-scorer:
    build: .
    command: python salesforce_background_scorer.py
    depends_on:
      - qualification-api
    environment:
      - API_URL=http://qualification-api:8080
    restart: unless-stopped
```

## ☁️ Cloud Deployment

### Google Cloud Run
```bash
# Deploy to Cloud Run
gcloud run deploy business-context-api \\
  --source . \\
  --platform managed \\
  --region us-central1 \\
  --allow-unauthenticated
```

### AWS ECS / Fargate
```bash
# Build and push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.region.amazonaws.com
docker build -t business-context-api .
docker tag business-context-api:latest $AWS_ACCOUNT.dkr.ecr.region.amazonaws.com/business-context-api:latest
docker push $AWS_ACCOUNT.dkr.ecr.region.amazonaws.com/business-context-api:latest
```

### Railway (Simple)
```bash
# Connect GitHub repo to Railway
# Set start command: python qualification_api.py
# Auto-deploys on git push
```

## 🔗 Integration Examples

### Salesforce Webhook
```apex
// Apex trigger on Lead creation
@future(callout=true)
public static void qualifyLead(Id leadId) {
    Lead lead = [SELECT Email, Website FROM Lead WHERE Id = :leadId];
    
    HttpRequest req = new HttpRequest();
    req.setEndpoint('https://your-api-url.com/qualify/domain');
    req.setMethod('POST');
    req.setHeader('Content-Type', 'application/json');
    req.setBody(JSON.serialize(new Map<String, String>{
        'domain' => getDomainFromLead(lead),
        'contact_name' => lead.Name,
        'company_name' => lead.Company
    }));
    
    Http http = new Http();
    HttpResponse response = http.send(req);
    
    if (response.getStatusCode() == 200) {
        Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(response.getBody());
        
        lead.Business_Context_Score__c = (Decimal) result.get('qualification_score');
        lead.Business_Context_Qualified__c = (Boolean) result.get('is_qualified');
        update lead;
    }
}
```

### Zapier Integration
```javascript
// Zapier webhook action
const response = await fetch('https://your-api-url.com/qualify/domain', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    domain: inputData.email.split('@')[1],
    contact_name: inputData.name,
    company_name: inputData.company
  })
});

const result = await response.json();

// Use result.qualification_score and result.is_qualified for routing
return {
  qualification_score: result.qualification_score,
  is_qualified: result.is_qualified,
  business_context: result.business_context
};
```

### Lead Routing Logic
```python
# Example routing based on business context scores
def route_lead(qualification_result):
    score = qualification_result['qualification_score']
    confidence = qualification_result['confidence']
    industries = qualification_result['business_context']['industries']
    
    # Enterprise routing
    if score >= 0.8 and confidence == 'HIGH':
        return 'enterprise_ae'
    
    # Tech company routing  
    elif score >= 0.6 and 'Technology' in industries:
        return 'tech_specialist_ae'
    
    # Voice AI specialist routing
    elif 'AI/Automation' in qualification_result['business_context']['use_cases']:
        return 'voice_ai_specialist'
    
    # Standard qualification
    elif score >= 0.5:
        return 'standard_ae'
    
    # Self-service
    else:
        return 'self_service'
```

## 📈 A/B Testing vs Clearbit

### Test Setup
```python
# Route 50% traffic to business context, 50% to Clearbit
import random

def qualification_ab_test(lead_data):
    if random.random() < 0.5:
        # Business context qualification
        result = requests.post('http://api:8080/qualify/domain', json={
            'domain': extract_domain(lead_data['email'])
        }).json()
        
        return {
            'method': 'business_context',
            'score': result['qualification_score'],
            'qualified': result['is_qualified'],
            'reasoning': result['reasoning']
        }
    else:
        # Clearbit qualification (existing)
        clearbit_data = clearbit.qualify(lead_data)
        return {
            'method': 'clearbit',
            'score': clearbit_score(clearbit_data),
            'qualified': clearbit_qualified(clearbit_data),
            'reasoning': ['Demographic scoring']
        }
```

### Success Metrics
- **AE Progression Rate**: % of qualified leads that progress past intro call
- **Pipeline Velocity**: Time from lead → opportunity
- **AE Time Savings**: Reduced time on unqualified leads
- **Revenue Attribution**: Revenue from qualified vs non-qualified leads

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
export FLASK_ENV=production
export FLASK_DEBUG=false
export API_PORT=8080

# Model Configuration  
export MODEL_PATH=/app/ml-model/models/business_context_v1/
export QUALIFICATION_THRESHOLD=0.5
export HIGH_CONFIDENCE_THRESHOLD=0.8

# Salesforce Integration
export SF_ORG=niamh@telnyx.com
export SF_CHECK_INTERVAL=300

# Rate Limiting
export MAX_REQUESTS_PER_MINUTE=100
export MAX_BATCH_SIZE=50
```

### Custom Thresholds
```python
# Adjust qualification thresholds based on your needs
QUALIFICATION_THRESHOLDS = {
    'enterprise': 0.8,      # Enterprise prospects
    'standard': 0.5,        # Standard qualification  
    'tech_company': 0.6,    # Technology companies
    'voice_ai': 0.7,        # Voice AI use cases
}
```

## 🔍 Monitoring & Observability

### Health Monitoring
```bash
# Check API health
curl http://localhost:8080/health

# Check model info
curl http://localhost:8080/model/info
```

### Logging
- API requests/responses logged to stdout
- Background scorer logs include qualification rates
- Model performance metrics tracked
- Failed qualifications logged with reasons

### Metrics to Track
- **API Response Time**: < 5 seconds for domain analysis
- **Qualification Rate**: % of leads qualified over time
- **Confidence Distribution**: HIGH/CONFIDENT/UNCERTAIN/LOW ratios  
- **Industry Breakdown**: Which industries score highest
- **Error Rate**: Failed website analyses

## 🚀 Next Steps

1. **Deploy API** to cloud platform (Railway, Cloud Run, etc.)
2. **Set up background scorer** on dedicated server/container
3. **Configure Salesforce fields** for business context data
4. **Start A/B test** (50% business context, 50% Clearbit)
5. **Monitor metrics** for 2-4 weeks
6. **Analyze results** and optimize thresholds
7. **Full rollout** once validated

## 💡 Business Context Advantages

✅ **Works for AI companies** (Clearbit often missing)  
✅ **International prospects** (Not US-centric)  
✅ **Conversation-style intelligence** (Like AE assessment)  
✅ **Enterprise differentiation** (83% vs 37% scores)  
✅ **Privacy compliant** (No demographic scraping)  
✅ **Real-time analysis** (Website → qualification in seconds)  

## 📞 Support

Questions? Contact:
- **GitHub**: https://github.com/niamhtelnyx/fellow-ai-learning-system  
- **Model Performance**: 80.6% accuracy, 144 Fellow intro calls training
- **Enterprise Validation**: 6/6 enterprise prospects correctly qualified