# Lead Qualification Modernization - PRD

## 📋 **Product Requirements Document**
**Version**: 1.0  
**Date**: 2026-02-06  
**Status**: Discovery & Development  

---

## 🚨 **Business Problem**

### **Current System Failures**
Our lead qualification relies on **outdated static demographic data** that fails modern business realities:

1. **Clearbit Data Gaps**: Missing international companies, new AI startups
2. **Outdated Assumptions**: Low employee count ≠ bad prospect (AI companies = small teams, big contracts)
3. **Static Scoring**: 5+ year old matrix based on revenue/headcount, not business context
4. **Pipeline Inefficiency**: Good leads rejected, bad leads waste AE time

### **Root Cause**
**Demographic qualification ≠ Business fit qualification**

---

## 🎯 **Business Objectives**

### **Primary Goal**
Replace static demographic scoring with **AE conversation-based qualification** that identifies real business fit signals.

### **Success Metrics**
1. **Pipeline Efficiency**: Increase good leads reaching AEs, decrease bad leads wasting time
2. **Coverage**: Qualify international/AI companies currently missed by Clearbit
3. **Accuracy**: Model predictions match AE progression decisions
4. **Data Independence**: Reduce/eliminate Clearbit dependency

---

## 💡 **Solution Approach**

### **Core Insight**
**AE conversations reveal true qualification signals** that demographic data cannot capture.

### **Example Discovery**
If analysis finds AEs are **10x more likely to progress deals** when prospects mention:
- "Voice AI in health insurance"
- "Patient communication automation"  
- "Hospital discharge follow-ups"

Then qualification should prioritize **business context** (health insurance + voice AI) over demographics (employee count).

### **Solution Components**

#### **1. AE Conversation Analysis**
- Extract Fellow.ai intro call transcripts
- Identify patterns in successful vs unsuccessful AE progressions
- Map conversation topics → AE progression likelihood

#### **2. Signal Discovery Engine**
- Find high-value business context combinations
- Weight qualification factors by actual AE behavior
- Identify industry + use case patterns that convert

#### **3. Clearbit-Independent Qualification**
- Extract qualification signals from:
  - Website content analysis
  - Conversation context
  - Business problem descriptions
  - Use case discussions
- Remove dependency on static demographic data

#### **4. Dynamic Scoring Model**
- Score prospects based on conversation-derived signals
- Continuously learn from new AE outcomes
- Adapt to evolving market patterns (e.g., AI company characteristics)

---

## 🏗️ **Technical Architecture**

### **Data Sources**
```
Fellow.ai Transcripts → Conversation Analysis → Business Context Extraction → Qualification Scoring
Website Analysis → Business Context Detection → 
Prospect Communications → Use Case Identification →
```

### **Signal Extraction Pipeline**
1. **Conversation Topic Modeling**: Identify key business themes
2. **Industry Classification**: Health insurance, fintech, etc.
3. **Use Case Detection**: Voice AI, automation, integrations
4. **AE Outcome Mapping**: Progression vs rejection patterns

### **Scoring Algorithm**
```
Qualification Score = Σ(Business Context Weight × Industry Weight × Use Case Weight)
```

**Not**: Employee Count × Revenue × Tech Stack (Clearbit approach)

---

## 📊 **Discovery Phase Results**

### **From 40 Fellow Transcripts Analysis**
- **27.5% AE progression rate** (realistic baseline)
- **Key patterns identified**: Engagement signals, next steps, business validation
- **Conversation-based classification**: 72.5% accuracy predicting AE progression

### **Next: Business Context Analysis**
- [ ] Extract industry mentions from transcripts
- [ ] Identify high-conversion use case patterns  
- [ ] Map business problems → AE progression likelihood
- [ ] Find Clearbit-independent qualification signals

---

## 🎯 **Phase 1: Signal Discovery** (Current)

### **Objectives**
1. **Map AE progression patterns** from Fellow conversations
2. **Identify high-value business contexts** that lead to deals
3. **Extract qualification signals** independent of Clearbit data
4. **Build business context taxonomy** (industry + use case combinations)

### **Deliverables**
- [ ] Business context classification model
- [ ] High-conversion pattern identification
- [ ] Clearbit-independent signal extraction
- [ ] Industry + use case taxonomy

### **Success Criteria**
- Identify **3-5 high-value business context patterns** (e.g., "Voice AI + Health Insurance")
- Map conversation topics to **AE progression likelihood**
- Extract qualification signals **without demographic dependency**

---

## 🔍 **Research Questions**

### **Business Context Discovery**
1. **Which industry + use case combinations** have highest AE progression rates?
2. **What business problems** do successful prospects describe?
3. **Which conversation topics** correlate with deal progression?
4. **How can we detect these signals** without Clearbit data?

### **Pattern Analysis**
1. **Voice AI prospects**: What makes them convert vs not?
2. **International prospects**: How do they differ from US prospects?
3. **AI companies**: What signals indicate real business vs experimentation?
4. **Industry patterns**: Health insurance vs fintech vs other verticals?

---

## 📈 **Expected Outcomes**

### **Short-term (Phase 1)**
- **Business context taxonomy**: Industry + use case classification
- **High-value pattern identification**: Top 5 conversion patterns
- **Signal extraction framework**: Clearbit-independent qualification

### **Medium-term (Phase 2)**
- **Dynamic qualification model**: Context-based scoring
- **Pipeline efficiency improvement**: Better lead routing
- **International coverage**: Qualify non-US prospects effectively

### **Long-term (Phase 3)**
- **Continuous learning system**: Model updates from new AE outcomes
- **Clearbit replacement**: Fully context-based qualification
- **Pipeline optimization**: Maximum good leads to AEs, minimum bad leads

---

## 🚧 **Current Status**

### ✅ **Completed**
- Fellow.ai data extraction (40 transcripts)
- AE progression analysis (27.5% progression rate)
- Conversation-based classification model (72.5% accuracy)

### 🎯 **Next Steps**
1. **Business context extraction**: Identify industry + use case patterns
2. **High-value pattern discovery**: Find 10x conversion opportunities
3. **Signal mapping**: Conversation topics → qualification weights
4. **Clearbit independence**: Extract signals without demographic data

---

## 🎯 **Success Definition**

### **Primary Success**
Replace demographic-based qualification with **business context-based qualification** that:
- Increases AE pipeline efficiency
- Captures previously missed prospects (international, AI companies)
- Adapts to evolving market patterns

### **Measurable Outcomes**
1. **Coverage increase**: Qualify 30%+ more international/AI prospects
2. **Efficiency improvement**: Reduce AE time on unqualified prospects by 40%+
3. **Accuracy improvement**: Model predictions align with AE progression decisions
4. **Data independence**: <20% reliance on Clearbit demographic data

---

## 🔄 **Next Actions**

### **Immediate** (Next 2 weeks)
- [ ] Extract business context from Fellow transcripts (industry, use case, business problems)
- [ ] Identify high-conversion conversation patterns
- [ ] Map business context → AE progression likelihood

### **Short-term** (Next month)
- [ ] Build business context classification system
- [ ] Create Clearbit-independent qualification framework
- [ ] Test context-based scoring vs current demographic scoring

---

**Document Owner**: Ninibot  
**Stakeholder**: Niamh Collins  
**Last Updated**: 2026-02-06  
**Next Review**: Weekly during discovery phase