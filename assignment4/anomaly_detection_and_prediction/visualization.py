"""
Visualization module for the anomaly detection and prediction pipeline.
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


# --- Supporting visualizations (available data overview) ----------------------

def _extract_run_dataframe(run: RunData) -> Optional[pd.DataFrame]:
    """
    Best-effort extraction of a tabular dataframe from a RunData instance.
    This keeps visualization code resilient to different internal field names.
    """
    for attr in ("data", "df", "dataframe", "frame", "features", "features_df", "X", "X_df"):
        if hasattr(run, attr):
            obj = getattr(run, attr)
            if isinstance(obj, pd.DataFrame):
                return obj
    return None


def plot_supporting_visualizations(
    valid_runs: List[RunData],
    output_dir: Path,
    feature_names: Optional[List[str]] = None,
    max_features: int = 12,
) -> None:
    """
    Create supporting visualizations representing available data:
      - Runs per scenario category
      - Anomaly count per category
      - Run length distribution (if per-run DataFrames exist)
      - Feature correlation heatmap (if numeric data exists)
      - Feature distributions for a subset of numeric features (if numeric data exists)

    Figures are saved into `output_dir`.
    """
    configure_matplotlib()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not valid_runs:
        print("No valid runs available for supporting visualizations.")
        return

    # Per-run summary (always available)
    summary_rows = []
    frames = []
    for i, run in enumerate(valid_runs):
        df_run = _extract_run_dataframe(run)
        run_len = int(len(df_run)) if isinstance(df_run, pd.DataFrame) else np.nan
        n_anom = int(len(getattr(run, "anomalies", []) or []))
        summary_rows.append(
            {
                "run_id": getattr(run, "run_id", i),
                "category": getattr(run, "scenario_category", "unknown"),
                "n_anomalies": n_anom,
                "run_length": run_len,
            }
        )
        if isinstance(df_run, pd.DataFrame) and not df_run.empty:
            tmp = df_run.copy()
            tmp["__category__"] = getattr(run, "scenario_category", "unknown")
            tmp["__run_id__"] = getattr(run, "run_id", i)
            frames.append(tmp)

    summary_df = pd.DataFrame(summary_rows)

    # 1) Runs per category
    fig, ax = plt.subplots(figsize=(10, 5))
    cat_counts = summary_df["category"].value_counts().sort_index()
    sns.barplot(x=cat_counts.index, y=cat_counts.values, ax=ax, palette="viridis")
    ax.set_title("Runs per Scenario Category")
    ax.set_xlabel("Scenario Category")
    ax.set_ylabel("Number of Runs")
    ax.tick_params(axis="x", rotation=30)
    plt.tight_layout()
    plt.savefig(output_dir / "runs_per_category.png", dpi=150, **SAVEFIG_KW)
    plt.close()

    