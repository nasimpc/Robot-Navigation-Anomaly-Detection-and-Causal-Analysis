"""
Visualization module for the anomaly detection pipeline.
Provides functions for plotting data insights and algorithm validation.
"""

from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.tree import plot_tree

from .config import ANOM_LABELS, SAVEFIG_KW, configure_matplotlib
from .data_structures import RunData


def plot_anomaly_distribution(valid_runs: List[RunData], output_path: Path = None) -> None:
    """Plot anomaly frequency by scenario category.
    
    Args:
        valid_runs: List of valid RunData instances
        output_path: Path to save the figure (optional)
    """
    configure_matplotlib()
    
    anomaly_data = []
    for run in valid_runs:
        for a in run.anomalies:
            anomaly_data.append({
                'category': run.scenario_category,
                'anomaly': a
            })
    
    if not anomaly_data:
        print('No anomalies detected to plot.')
        return
    
    df_anom = pd.DataFrame(anomaly_data)
    categories = sorted(df_anom['category'].unique())
    df_counts = df_anom.value_counts(['anomaly', 'category']).reset_index(name='count')
    
    # Ensure every anomaly/category combo exists
    grid = pd.DataFrame(
        [{'anomaly': a, 'category': c} for a in ANOM_LABELS for c in categories]
    )
    df_counts = grid.merge(df_counts, on=['anomaly', 'category'], how='left').fillna({'count': 0})
    
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.barplot(data=df_counts, y='anomaly', x='count', hue='category', ax=ax, palette='viridis')
    ax.set_title('Anomaly Frequency by Scenario Category')
    ax.set_xlabel('Count')
    ax.set_ylabel('Anomaly Type')
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, **SAVEFIG_KW)
    plt.close()



def plot_surrogate_trees(surrogate_extractors: Dict, surrogate_metrics: Dict,
                         feature_names: List[str], output_path: Path = None) -> None:
    """Plot surrogate decision trees.
    
    Args:
        surrogate_extractors: Dictionary of SurrogateTreeExtractor instances
        surrogate_metrics: Dictionary of metrics for each surrogate tree
        feature_names: List of feature names
        output_path: Path to save the figure (optional)
    """
    configure_matplotlib()
    
    n_trees = len(surrogate_extractors)
    if n_trees == 0:
        print('No surrogate trees to plot.')
        return
    
    cols = min(2, n_trees)
    rows = (n_trees + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(14 * cols, 10 * rows))
    if n_trees == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
    
    for idx, (anom, surrogate) in enumerate(surrogate_extractors.items()):
        if idx >= len(axes):
            break
        ax = axes[idx]
        plot_tree(
            surrogate.surrogate_tree,
            feature_names=feature_names,
            class_names=['No Anomaly', 'Anomaly'],
            filled=True, rounded=True, fontsize=8, ax=ax
        )
        metrics = surrogate_metrics[anom]
        ax.set_title(
            f'{anom}\n(Fidelity={metrics["fidelity"]:.2f}, F1={metrics.get("f1", 0):.2f})',
            fontsize=12
        )
    
    for idx in range(len(surrogate_extractors), len(axes)):
        axes[idx].axis('off')
    
    plt.suptitle('Surrogate Decision Trees (Distilled from Ensemble Models)', fontsize=14)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', **SAVEFIG_KW)
    plt.close()


def plot_feature_importance(surrogate_extractors: Dict, feature_names: List[str],
                            output_path: Path = None) -> None:
    """Plot feature importance heatmap.
    
    Args:
        surrogate_extractors: Dictionary of SurrogateTreeExtractor instances
        feature_names: List of feature names
        output_path: Path to save the figure (optional)
    """
    configure_matplotlib()
    
    importance_data = []
    for anom, surrogate in surrogate_extractors.items():
        if surrogate.surrogate_tree:
            imps = surrogate.surrogate_tree.feature_importances_
            for name, imp in zip(feature_names, imps):
                if imp > 0:
                    importance_data.append({
                        'Anomaly': anom,
                        'Feature': name,
                        'Importance': imp
                    })
    
    if not importance_data:
        print('No feature importance data available.')
        return
    
    imp_df = pd.DataFrame(importance_data)
    pivot_df = imp_df.pivot_table(
        index='Feature', columns='Anomaly', values='Importance', fill_value=0
    )
    
    # Sort by total importance
    pivot_df['Total'] = pivot_df.sum(axis=1)
    pivot_df = pivot_df.sort_values('Total', ascending=False).drop(columns='Total')
    
    plt.figure(figsize=(12, max(6, len(pivot_df) * 0.3)))
    sns.heatmap(pivot_df, annot=True, fmt='.2f', cmap='viridis',
                cbar_kws={'label': 'Importance'})
    plt.title('Feature Importance by Anomaly Type (Surrogate Trees)')
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, **SAVEFIG_KW)
    plt.close()




def plot_generalization_summary(generalization_df: pd.DataFrame, output_path: Path = None) -> None:
    """Plot surrogate tree generalization performance.
    
    Args:
        generalization_df: DataFrame with performance metrics
        output_path: Path to save the figure (optional)
    """
    configure_matplotlib()
    
    if generalization_df.empty:
        print('No generalization data to plot.')
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    metrics_to_plot = ['Fidelity', 'Accuracy', 'Precision', 'Recall', 'F1']
    cols = [c for c in metrics_to_plot if c in generalization_df.columns]
    
    sns.heatmap(
        generalization_df.set_index('Anomaly')[cols],
        annot=True, fmt='.3f', cmap='viridis', vmin=0, vmax=1, ax=ax
    )
    ax.set_title('Surrogate Tree Performance Metrics')
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, **SAVEFIG_KW)
    plt.close()
