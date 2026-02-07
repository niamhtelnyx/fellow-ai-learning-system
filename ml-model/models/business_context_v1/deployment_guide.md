# Business Context Qualification Model v1.0
## Deployment Guide

### Model Details
- **Model Type:** RandomForest
- **Accuracy:** 80.6%
- **Features:** 70 business context features
- **Training Data:** 144 Fellow calls

### Performance
- **Target:** >75% accuracy (BEAT ✅)
- **Baseline:** 72.5% (Clearbit demographic scoring)  
- **Achieved:** 80.6%
- **Improvement:** +8.1 percentage points

### Usage
```python
import joblib

# Load model and feature extractor
model = joblib.load('fellow_business_context_v1.joblib')
extractor = joblib.load('feature_extractor.joblib')

# Extract features from call transcript
features = extractor.extract_features(transcript, summary)
feature_vector = [features[col] for col in feature_columns]

# Get prediction
probability = model.predict_proba([feature_vector])[0][1]
is_qualified = probability > 0.5

# Get business context reasoning
top_features = get_top_contributing_features(features, model)
```

### Key Business Context Features
                 feature  importance
            reading_ease    0.063753
          question_count    0.054650
sales_marketing_mentions    0.050380
      sentiment_negative    0.045370
  questions_per_sentence    0.041556
              word_count    0.040696
    large_scale_mentions    0.038261
        excitement_count    0.034882
      sentiment_positive    0.034853
          sentence_count    0.031202

### Deployment Checklist
- [ ] Load model and extractor in production environment  
- [ ] Implement feature extraction pipeline
- [ ] Set up qualification probability output
- [ ] Configure business context reasoning
- [ ] Test against validation dataset
- [ ] Monitor model performance in production
- [ ] Schedule model retraining (recommended: monthly)

### API Integration
The model replaces Clearbit demographic scoring with pure business context analysis.
No demographic data required - only conversation transcripts and summaries.

Generated: 2026-02-06 17:28:13
