#!/usr/bin/env python3
"""
Example client for Business Context Qualification API
"""

import requests
import json

# API Configuration
API_BASE_URL = "http://localhost:8080"  # Update with your deployed URL

def test_single_qualification():
    """Test single lead qualification"""
    print("🧪 Testing single lead qualification...")
    
    # Example: Enterprise prospect
    lead_data = {
        "domain": "openai.com",
        "contact_name": "Sarah Johnson", 
        "company_name": "OpenAI"
    }
    
    response = requests.post(f"{API_BASE_URL}/qualify/domain", json=lead_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Qualification Result:")
        print(f"   Domain: {result['domain']}")
        print(f"   Score: {result['qualification_score']:.1%}")
        print(f"   Qualified: {'✅ YES' if result['is_qualified'] else '❌ NO'}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Industries: {', '.join(result['business_context']['industries'])}")
        print(f"   Use Cases: {', '.join(result['business_context']['use_cases'])}")
        print(f"   Reasoning: {'; '.join(result['reasoning'])}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_batch_qualification():
    """Test batch lead qualification"""
    print("\n🧪 Testing batch lead qualification...")
    
    # Example: Mix of enterprise and small business
    leads_data = {
        "leads": [
            {"domain": "uber.com", "contact_name": "Tom Wilson", "company_name": "Uber"},
            {"domain": "cisco.com", "contact_name": "Bob Smith", "company_name": "Cisco"},
            {"domain": "nest.agency", "contact_name": "Alice Green", "company_name": "Nest Agency"},
            {"domain": "chefsipho.com", "contact_name": "Chef Sipho", "company_name": "Chef Sipho"}
        ]
    }
    
    response = requests.post(f"{API_BASE_URL}/qualify/batch", json=leads_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Batch Results ({result['total_processed']} leads):")
        
        for lead in result['results']:
            status = "✅ QUALIFIED" if lead.get('is_qualified', False) else "❌ NOT QUALIFIED"
            score = lead.get('qualification_score', 0)
            domain = lead.get('domain', 'unknown')
            print(f"   {status} | {domain:<20} | {score:>5.1%}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_model_info():
    """Test model information endpoint"""
    print("\n🧪 Testing model information...")
    
    response = requests.get(f"{API_BASE_URL}/model/info")
    
    if response.status_code == 200:
        info = response.json()
        print(f"✅ Model Information:")
        print(f"   Version: {info['model_version']}")
        print(f"   Accuracy: {info['accuracy']:.1%}")
        print(f"   Training Samples: {info['training_samples']}")
        print(f"   Features: {info['feature_count']}")
        print(f"   Target Met: {info['target_met']}")
        print(f"   Approach: {info['approach']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_health_check():
    """Test API health"""
    print("\n🧪 Testing API health...")
    
    response = requests.get(f"{API_BASE_URL}/health")
    
    if response.status_code == 200:
        health = response.json()
        print(f"✅ API Health:")
        print(f"   Status: {health['status']}")
        print(f"   Model Loaded: {health['model_loaded']}")
        print(f"   Timestamp: {health['timestamp']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("🚀 Business Context Qualification API - Client Test")
    print("=" * 60)
    
    # Test all endpoints
    test_health_check()
    test_model_info()
    test_single_qualification()
    test_batch_qualification()
    
    print(f"\n🎯 Integration Examples:")
    print(f"   Salesforce Webhook: POST /qualify/domain with lead data")
    print(f"   Batch Processing: POST /qualify/batch for daily scoring")
    print(f"   A/B Testing: Compare results with Clearbit scoring")
    print(f"   Monitoring: GET /health for uptime checks")