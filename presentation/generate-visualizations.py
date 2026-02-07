#!/usr/bin/env python3
"""
Data Visualization Generator for Fellow Qualification Model Presentation
Creates charts and graphs to support business presentation
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import json

# Set style for professional charts
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def create_model_comparison_chart():
    """Create model performance comparison chart"""
    models = ['Clearbit\nDemographic', 'Business Context\nAI']
    accuracy = [60, 80.6]
    precision = [70, 83]
    recall = [75, 97]
    
    x = np.arange(len(models))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars1 = ax.bar(x - width, accuracy, width, label='Accuracy (%)', alpha=0.8)
    bars2 = ax.bar(x, precision, width, label='Precision (%)', alpha=0.8) 
    bars3 = ax.bar(x + width, recall, width, label='Recall (%)', alpha=0.8)
    
    ax.set_xlabel('Model Type')
    ax.set_ylabel('Performance (%)')
    ax.set_title('Model Performance Comparison: Business Context vs Demographics')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend()
    ax.set_ylim(0, 100)
    
    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}%',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/Users/niamhcollins/clawd/fellow-learning-system/presentation/model-performance-comparison.png', 
                dpi=300, bbox_inches='tight')
    plt.show()

def create_roi_impact_chart():
    """Create ROI impact visualization"""
    categories = ['AE Time\nSavings', 'Additional\nPipeline', 'Cost\nReduction']
    values = [140, 490, 350]
    colors = ['#2E8B57', '#4169E1', '#DAA520']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(categories, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.2)
    
    ax.set_ylabel('Annual Value ($K)')
    ax.set_title('Annual ROI Impact: $980K+ Total Business Value')
    ax.set_ylim(0, 550)
    
    # Add value labels
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.annotate(f'${value}K',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3), textcoords="offset points",
                   ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    # Add total value annotation
    ax.text(1, 500, f'Total Annual Value: $980K+', 
            ha='center', va='center', fontsize=16, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
    
    plt.tight_layout()
    plt.savefig('/Users/niamhcollins/clawd/fellow-learning-system/presentation/roi-impact-chart.png',
                dpi=300, bbox_inches='tight')
    plt.show()

def create_conversion_patterns_heatmap():
    """Create 10x conversion patterns heatmap"""
    patterns_data = {
        'AI/Voice Technology + Voice AI': 100,
        'Legal Technology + Voice AI': 100, 
        'Call Center/AI + Voice AI': 100,
        'Healthcare/AI + Voice AI': 100,
        'Security/Enterprise + Voice AI': 100,
        'Digital Marketing + SMS': 100,
        'Restaurant + Food Service': 75,
        'Generic Software + Basic Voice': 25,
        'Traditional B2B + Basic SMS': 15
    }
    
    # Create data for heatmap
    patterns = list(patterns_data.keys())
    conversion_rates = list(patterns_data.values())
    
    # Create color mapping
    colors = ['#8B0000' if x < 30 else '#DAA520' if x < 80 else '#006400' 
              for x in conversion_rates]
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    bars = ax.barh(patterns, conversion_rates, color=colors, alpha=0.8, 
                   edgecolor='black', linewidth=1)
    
    ax.set_xlabel('Conversion Rate (%)')
    ax.set_title('Industry + Use Case Conversion Patterns\n"10x Gold Patterns" in Green')
    ax.set_xlim(0, 105)
    
    # Add value labels
    for bar, value in zip(bars, conversion_rates):
        width = bar.get_width()
        ax.annotate(f'{value}%',
                   xy=(width + 1, bar.get_y() + bar.get_height() / 2),
                   va='center', fontweight='bold', fontsize=10)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#006400', label='Tier 1 Gold (90-100%)'),
        Patch(facecolor='#DAA520', label='Tier 2 Silver (70-89%)'),
        Patch(facecolor='#8B0000', label='Tier 3 Bronze (<70%)')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    plt.savefig('/Users/niamhcollins/clawd/fellow-learning-system/presentation/conversion-patterns-heatmap.png',
                dpi=300, bbox_inches='tight')
    plt.show()

def create_confusion_matrix():
    """Create confusion matrix visualization"""
    confusion_data = np.array([[0, 6], [1, 29]])
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    sns.heatmap(confusion_data, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Predicted Not Qualified', 'Predicted Qualified'],
                yticklabels=['Actually Not Qualified', 'Actually Qualified'],
                cbar_kws={'label': 'Number of Prospects'})
    
    ax.set_title('Business Context Model Confusion Matrix\nAccuracy: 80.6% (29/36 correct)')
    ax.set_ylabel('Actual Classification')
    ax.set_xlabel('Model Prediction')
    
    # Add performance metrics as text
    metrics_text = (
        'Performance Metrics:\n'
        '• True Positives: 29\n'
        '• False Positives: 6\n'
        '• False Negatives: 1\n'
        '• True Negatives: 0\n\n'
        '• Precision: 83%\n'
        '• Recall: 97%\n'
        '• F1-Score: 89%'
    )
    
    ax.text(2.5, 1, metrics_text, fontsize=10, 
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('/Users/niamhcollins/clawd/fellow-learning-system/presentation/confusion-matrix.png',
                dpi=300, bbox_inches='tight')
    plt.show()

def create_feature_importance_chart():
    """Create feature importance visualization"""
    features = [
        'AI Mention Count',
        'Voice Technology Signals', 
        'Enterprise Stakeholders',
        'Volume Mentions',
        'Competitive Replacement',
        'Healthcare Vertical',
        'Platform Business Model',
        'Technical Complexity'
    ]
    
    importance = [0.124, 0.089, 0.076, 0.071, 0.068, 0.059, 0.054, 0.051]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.barh(features, importance, color='skyblue', alpha=0.8, 
                   edgecolor='navy', linewidth=1)
    
    ax.set_xlabel('Feature Importance Score')
    ax.set_title('Top Predictive Features: Business Context Model')
    ax.set_xlim(0, 0.14)
    
    # Add value labels
    for bar, value in zip(bars, importance):
        width = bar.get_width()
        ax.annotate(f'{value:.3f}',
                   xy=(width + 0.002, bar.get_y() + bar.get_height() / 2),
                   va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/Users/niamhcollins/clawd/fellow-learning-system/presentation/feature-importance.png',
                dpi=300, bbox_inches='tight')
    plt.show()

def create_timeline_accuracy_projection():
    """Create accuracy improvement timeline"""
    weeks = list(range(1, 13))
    clearbit_baseline = [60] * 12
    business_context = [65, 68, 72, 75, 77, 79, 80, 81, 82, 83, 84, 85]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(weeks, clearbit_baseline, 'r--', linewidth=3, label='Clearbit Baseline (60%)', alpha=0.7)
    ax.plot(weeks, business_context, 'b-', linewidth=3, label='Business Context AI', marker='o')
    
    # Shade improvement area
    ax.fill_between(weeks, clearbit_baseline, business_context, 
                    alpha=0.3, color='green', label='Improvement Area')
    
    ax.set_xlabel('Implementation Timeline (Weeks)')
    ax.set_ylabel('Qualification Accuracy (%)')
    ax.set_title('Qualification Accuracy Improvement Over Time')
    ax.set_ylim(50, 90)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Add milestone annotations
    milestones = [
        (2, 68, 'A/B Test Launch'),
        (4, 75, 'Full Deployment'),
        (8, 81, 'Optimization Complete'),
        (12, 85, 'Target Achieved')
    ]
    
    for week, accuracy, milestone in milestones:
        ax.annotate(milestone, xy=(week, accuracy), xytext=(week, accuracy + 3),
                   arrowprops=dict(arrowstyle='->', color='black', alpha=0.7),
                   ha='center', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/Users/niamhcollins/clawd/fellow-learning-system/presentation/timeline-projection.png',
                dpi=300, bbox_inches='tight')
    plt.show()

def create_cost_savings_breakdown():
    """Create detailed cost savings breakdown"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. AE Time Savings
    time_categories = ['Wasted on\nUnqualified', 'Productive\nTime']
    current_time = [40, 60]
    improved_time = [20, 80]
    
    x = np.arange(len(time_categories))
    width = 0.35
    
    ax1.bar(x - width/2, current_time, width, label='Current', alpha=0.7)
    ax1.bar(x + width/2, improved_time, width, label='Improved', alpha=0.7)
    ax1.set_ylabel('Percentage of Time')
    ax1.set_title('AE Time Allocation')
    ax1.set_xticks(x)
    ax1.set_xticklabels(time_categories)
    ax1.legend()
    
    # 2. Pipeline Quality
    pipeline_stages = ['Intro', 'Demo', 'Trial', 'Close']
    current_rates = [100, 27.5, 16.5, 6.6]
    improved_rates = [100, 45, 33.8, 16.9]
    
    ax2.plot(pipeline_stages, current_rates, 'ro-', label='Current', linewidth=2)
    ax2.plot(pipeline_stages, improved_rates, 'bo-', label='Improved', linewidth=2)
    ax2.set_ylabel('Conversion Rate (%)')
    ax2.set_title('Pipeline Conversion Rates')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Cost per Lead
    cost_components = ['Lead\nAcquisition', 'AE\nTime', 'Ops\nOverhead', 'Total']
    current_costs = [150, 180, 90, 420]
    improved_costs = [150, 95, 0, 245]
    
    x = np.arange(len(cost_components))
    ax3.bar(x - width/2, current_costs, width, label='Current', alpha=0.7)
    ax3.bar(x + width/2, improved_costs, width, label='Improved', alpha=0.7)
    ax3.set_ylabel('Cost ($)')
    ax3.set_title('Cost per Qualified Lead')
    ax3.set_xticks(x)
    ax3.set_xticklabels(cost_components)
    ax3.legend()
    
    # 4. Monthly Value Creation
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    cumulative_value = [40, 95, 165, 250, 350, 465]
    
    ax4.bar(months, cumulative_value, color='green', alpha=0.7)
    ax4.set_ylabel('Cumulative Value ($K)')
    ax4.set_title('Value Creation Timeline')
    
    # Add value labels
    for i, v in enumerate(cumulative_value):
        ax4.text(i, v + 10, f'${v}K', ha='center', fontweight='bold')
    
    plt.suptitle('Fellow Qualification Model: Cost Savings Breakdown', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('/Users/niamhcollins/clawd/fellow-learning-system/presentation/cost-savings-breakdown.png',
                dpi=300, bbox_inches='tight')
    plt.show()

def create_interactive_dashboard():
    """Create interactive Plotly dashboard"""
    # Create subplot figure
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Model Performance', 'Conversion Patterns', 
                       'ROI Timeline', 'Feature Importance'),
        specs=[[{"type": "bar"}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "bar"}]]
    )
    
    # Model Performance
    fig.add_trace(
        go.Bar(x=['Clearbit', 'Business Context'], y=[60, 80.6], 
               name='Accuracy', marker_color='lightblue'),
        row=1, col=1
    )
    
    # Conversion Patterns
    patterns = ['AI+Voice', 'Healthcare+AI', 'Legal+Voice', 'Generic']
    conversions = [100, 100, 100, 25]
    fig.add_trace(
        go.Scatter(x=patterns, y=conversions, mode='markers+lines',
                  marker=dict(size=15, color='red'),
                  name='Conversion Rate'),
        row=1, col=2
    )
    
    # ROI Timeline
    months = list(range(1, 7))
    roi_values = [40, 95, 165, 250, 350, 465]
    fig.add_trace(
        go.Scatter(x=months, y=roi_values, mode='lines+markers',
                  line=dict(color='green', width=4),
                  name='Cumulative ROI ($K)'),
        row=2, col=1
    )
    
    # Feature Importance
    features = ['AI Signals', 'Voice Tech', 'Enterprise', 'Volume']
    importance = [0.124, 0.089, 0.076, 0.071]
    fig.add_trace(
        go.Bar(x=features, y=importance, name='Importance',
               marker_color='orange'),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        title_text="Fellow Qualification Model: Interactive Dashboard",
        showlegend=False,
        height=800
    )
    
    # Save as HTML
    fig.write_html('/Users/niamhcollins/clawd/fellow-learning-system/presentation/interactive-dashboard.html')
    fig.show()

def main():
    """Generate all visualization assets"""
    print("Generating Fellow Qualification Model visualizations...")
    
    # Create output directory
    import os
    os.makedirs('/Users/niamhcollins/clawd/fellow-learning-system/presentation', exist_ok=True)
    
    # Generate all charts
    create_model_comparison_chart()
    print("✅ Model comparison chart created")
    
    create_roi_impact_chart()  
    print("✅ ROI impact chart created")
    
    create_conversion_patterns_heatmap()
    print("✅ Conversion patterns heatmap created")
    
    create_confusion_matrix()
    print("✅ Confusion matrix created")
    
    create_feature_importance_chart()
    print("✅ Feature importance chart created")
    
    create_timeline_accuracy_projection()
    print("✅ Timeline projection created")
    
    create_cost_savings_breakdown()
    print("✅ Cost savings breakdown created")
    
    create_interactive_dashboard()
    print("✅ Interactive dashboard created")
    
    print("\n🎯 All visualizations generated successfully!")
    print("📂 Files saved to: /Users/niamhcollins/clawd/fellow-learning-system/presentation/")

if __name__ == "__main__":
    main()