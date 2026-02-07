#!/usr/bin/env python3
"""
Sentiment-Based ML Model Trainer for Fellow.ai Qualification
Trains models using AE sentiment and deal progression features instead of keyword matching
"""

import pandas as pd
import numpy as np
import sqlite3
import joblib
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# ML imports
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    confusion_matrix, classification_report, roc_auc_score
)
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

# Import our sentiment feature extractor
from sentiment_feature_extractor import extract_sentiment_features, SentimentFeatures

class SentimentModelTrainer:
    """ML Model trainer using sentiment-based features"""
    
    def __init__(self, model_dir: str = "models", random_state: int = 42):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.random_state = random_state
        self.scaler = StandardScaler()
        
        # Define feature names for interpretability
        self.feature_names = [
            'ae_engagement_score',
            'deal_progression_score', 
            'customer_readiness_score',
            'momentum_indicators',
            'sales_call_probability',
            'transcript_length_normalized',
            'speaker_turns_normalized'
        ]
        
        # Model configurations optimized for small dataset
        self.model_configs = {
            'logistic': {
                'model': LogisticRegression(
                    random_state=random_state, 
                    max_iter=1000,
                    class_weight='balanced'  # Handle class imbalance
                ),
                'param_grid': {
                    'C': [0.1, 1.0, 10.0],
                    'penalty': ['l1', 'l2'],
                    'solver': ['liblinear']
                }
            },
            'random_forest': {
                'model': RandomForestClassifier(
                    random_state=random_state, 
                    n_estimators=50,  # Smaller for small dataset
                    class_weight='balanced',
                    max_depth=5  # Prevent overfitting
                ),
                'param_grid': {
                    'n_estimators': [25, 50, 100],
                    'max_depth': [3, 5, 7],
                    'min_samples_split': [2, 5]
                }
            },
            'gradient_boosting': {
                'model': GradientBoostingClassifier(
                    random_state=random_state,
                    n_estimators=50,
                    max_depth=3  # Shallow trees for small dataset
                ),
                'param_grid': {
                    'n_estimators': [25, 50, 75],
                    'max_depth': [2, 3, 4],
                    'learning_rate': [0.1, 0.2]
                }
            },
            'xgboost': {
                'model': xgb.XGBClassifier(
                    random_state=random_state,
                    n_estimators=50,
                    max_depth=3,
                    eval_metric='logloss'
                ),
                'param_grid': {
                    'n_estimators': [25, 50],
                    'max_depth': [2, 3, 4],
                    'learning_rate': [0.1, 0.2]
                }
            }
        }
    
    def load_and_process_data(self, db_path: str) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """Load data from database and extract sentiment features"""
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        query = """
        SELECT meeting_id, meeting_title, transcript, is_qualified, qualification_score
        FROM training_data 
        WHERE transcript IS NOT NULL 
        AND transcript != '## Transcript: Meeting\n\n_No transcript available for this recording._'
        AND LENGTH(transcript) > 100
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"Loaded {len(df)} records from database")
        print(f"Qualified: {df['is_qualified'].sum()}, Non-qualified: {len(df) - df['is_qualified'].sum()}")
        
        # Extract sentiment features for each transcript
        features_list = []
        feature_vectors = []
        
        for idx, row in df.iterrows():
            try:
                features = extract_sentiment_features(row['transcript'], row['meeting_title'])
                features_dict = {
                    'meeting_id': row['meeting_id'],
                    'meeting_title': row['meeting_title'], 
                    'is_qualified': row['is_qualified'],
                    'ae_engagement_score': features.ae_engagement_score,
                    'deal_progression_score': features.deal_progression_score,
                    'customer_readiness_score': features.customer_readiness_score,
                    'momentum_indicators': features.momentum_indicators,
                    'feature_vector': features.feature_vector
                }
                features_list.append(features_dict)
                feature_vectors.append(features.feature_vector)
                
            except Exception as e:
                print(f"Error processing {row['meeting_title']}: {e}")
                continue
        
        # Convert to arrays
        X = np.array(feature_vectors)
        y = np.array([f['is_qualified'] for f in features_list])
        
        print(f"Feature matrix shape: {X.shape}")
        print(f"Target distribution: {np.bincount(y)}")
        
        return X, y, features_list
    
    def train_and_evaluate_model(self, X: np.ndarray, y: np.ndarray, model_name: str = 'logistic') -> Dict:
        """Train and evaluate a specific model"""
        
        if model_name not in self.model_configs:
            raise ValueError(f"Unknown model: {model_name}")
        
        config = self.model_configs[model_name]
        model = config['model']
        
        # Split data (stratified to maintain class balance)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=self.random_state, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)
        y_prob_test = model.predict_proba(X_test_scaled)[:, 1] if hasattr(model, 'predict_proba') else None
        
        # Calculate metrics
        train_accuracy = accuracy_score(y_train, y_pred_train)
        test_accuracy = accuracy_score(y_test, y_pred_test)
        precision = precision_score(y_test, y_pred_test, zero_division=0)
        recall = recall_score(y_test, y_pred_test, zero_division=0)
        f1 = f1_score(y_test, y_pred_test, zero_division=0)
        
        # Cross-validation with smaller folds for small dataset
        cv_folds = min(5, len(y) // 2)  # Ensure at least 2 samples per fold
        if cv_folds >= 2:
            cv_scores = cross_val_score(
                model, X, y, cv=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=self.random_state)
            )
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
        else:
            cv_mean = cv_std = 0.0
        
        # Feature importance (if available)
        feature_importance = None
        if hasattr(model, 'feature_importances_'):
            feature_importance = dict(zip(self.feature_names, model.feature_importances_))
        elif hasattr(model, 'coef_'):
            feature_importance = dict(zip(self.feature_names, model.coef_[0]))
        
        results = {
            'model_name': model_name,
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'cv_mean': cv_mean,
            'cv_std': cv_std,
            'feature_importance': feature_importance,
            'confusion_matrix': confusion_matrix(y_test, y_pred_test).tolist(),
            'classification_report': classification_report(y_test, y_pred_test, output_dict=True)
        }
        
        if y_prob_test is not None:
            try:
                auc_score = roc_auc_score(y_test, y_prob_test)
                results['auc_score'] = auc_score
            except:
                results['auc_score'] = None
        
        return results, model
    
    def compare_all_models(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Train and compare all model types"""
        
        results = {}
        models = {}
        
        print("Training and comparing sentiment-based models...")
        print("=" * 60)
        
        for model_name in self.model_configs.keys():
            print(f"\nTraining {model_name.upper()} model...")
            try:
                result, model = self.train_and_evaluate_model(X, y, model_name)
                results[model_name] = result
                models[model_name] = model
                
                print(f"Test Accuracy: {result['test_accuracy']:.3f}")
                print(f"Precision: {result['precision']:.3f}")
                print(f"Recall: {result['recall']:.3f}")
                print(f"F1 Score: {result['f1_score']:.3f}")
                if result.get('cv_mean'):
                    print(f"CV Accuracy: {result['cv_mean']:.3f} ± {result['cv_std']:.3f}")
                    
            except Exception as e:
                print(f"Error training {model_name}: {e}")
                continue
        
        # Find best model
        best_model_name = max(results.keys(), key=lambda x: results[x]['test_accuracy'])
        best_result = results[best_model_name]
        best_model = models[best_model_name]
        
        print("\n" + "=" * 60)
        print(f"BEST MODEL: {best_model_name.upper()}")
        print(f"Test Accuracy: {best_result['test_accuracy']:.1%}")
        print(f"Precision: {best_result['precision']:.1%}")
        print(f"Recall: {best_result['recall']:.1%}")
        print(f"F1 Score: {best_result['f1_score']:.1%}")
        
        # Feature importance analysis
        if best_result.get('feature_importance'):
            print("\nTop Feature Importances:")
            importance_items = sorted(
                best_result['feature_importance'].items(), 
                key=lambda x: abs(x[1]), 
                reverse=True
            )
            for feature, importance in importance_items[:5]:
                print(f"  {feature}: {importance:.3f}")
        
        return {
            'all_results': results,
            'best_model_name': best_model_name,
            'best_result': best_result,
            'best_model': best_model,
            'feature_names': self.feature_names
        }
    
    def save_model(self, model, scaler, model_name: str, metadata: Dict):
        """Save trained model and metadata"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_file = self.model_dir / f"sentiment_model_{model_name}_{timestamp}.joblib"
        scaler_file = self.model_dir / f"scaler_{model_name}_{timestamp}.joblib"
        metadata_file = self.model_dir / f"metadata_{model_name}_{timestamp}.json"
        
        # Save model and scaler
        joblib.dump(model, model_file)
        joblib.dump(scaler, scaler_file)
        
        # Save metadata
        metadata['model_file'] = str(model_file)
        metadata['scaler_file'] = str(scaler_file)
        metadata['created_at'] = timestamp
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\nModel saved:")
        print(f"  Model: {model_file}")
        print(f"  Scaler: {scaler_file}")
        print(f"  Metadata: {metadata_file}")
        
        return model_file, scaler_file, metadata_file

def main():
    """Main training pipeline"""
    
    # Initialize trainer
    trainer = SentimentModelTrainer()
    
    # Load and process data
    db_path = "/Users/niamhcollins/clawd/fellow-learning-system/data/fellow_training_data.db"
    X, y, features_list = trainer.load_and_process_data(db_path)
    
    if len(X) == 0:
        print("No valid data found!")
        return
    
    # Train and compare models
    comparison_results = trainer.compare_all_models(X, y)
    
    # Save best model
    best_model = comparison_results['best_model']
    best_model_name = comparison_results['best_model_name']
    best_result = comparison_results['best_result']
    
    # Prepare metadata
    metadata = {
        'model_type': 'sentiment_based_qualification',
        'feature_extraction': 'ae_sentiment_and_progression',
        'training_samples': len(X),
        'qualified_samples': int(y.sum()),
        'non_qualified_samples': int(len(y) - y.sum()),
        'feature_names': trainer.feature_names,
        'performance_metrics': best_result,
        'comparison_results': comparison_results['all_results']
    }
    
    # Save model
    model_files = trainer.save_model(best_model, trainer.scaler, best_model_name, metadata)
    
    # Print final results
    print(f"\n🎯 FINAL RESULTS:")
    print(f"📈 Model Accuracy: {best_result['test_accuracy']:.1%}")
    print(f"📊 Baseline (Quinn): 38.8%")
    print(f"🚀 Improvement: {(best_result['test_accuracy'] - 0.388) * 100:+.1f} percentage points")
    
    if best_result['test_accuracy'] > 0.388:
        print("✅ SUCCESS: Beat Quinn's baseline!")
    else:
        print("❌ Did not beat baseline - needs further refinement")
    
    return comparison_results

if __name__ == "__main__":
    results = main()