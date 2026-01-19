"""
Model classes for ensemble anomaly prediction and surrogate tree rule extraction.
"""

from typing import List, Tuple, Dict, Optional
import numpy as np
import pickle
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import precision_recall_fscore_support, accuracy_score
from sklearn.inspection import permutation_importance

from .config import FEATURE_NAMES, BOOL_FEATURES


class EnsembleAnomalyPredictor:
    """Ensemble-based anomaly prediction with multiple model comparison."""
    
    def __init__(self, feature_names: List[str] = None):
        """Initialize the ensemble predictor.
        
        Args:
            feature_names: List of feature names
        """
        self.feature_names = feature_names or FEATURE_NAMES
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.feature_importance = None
        self.rule_thresholds = {}
    
    def _create_models(self, n_samples: int, n_positive: int) -> Dict:
        """Create model candidates with appropriate hyperparameters.
        
        Args:
            n_samples: Total number of samples
            n_positive: Number of positive samples
            
        Returns:
            Dictionary of model instances
        """
        min_samples = max(2, int(n_samples * 0.02))
        
        models = {
            'DecisionTree': DecisionTreeClassifier(
                max_depth=5, min_samples_leaf=min_samples,
                min_samples_split=min_samples*2, class_weight='balanced', random_state=42
            ),
            'RandomForest': RandomForestClassifier(
                n_estimators=100, max_depth=6, min_samples_leaf=min_samples,
                class_weight='balanced', random_state=42, n_jobs=-1
            ),
            'GradientBoosting': GradientBoostingClassifier(
                n_estimators=100, max_depth=4, min_samples_leaf=min_samples,
                learning_rate=0.1, random_state=42
            )
        }
        
        return models
    
    def fit(self, X: np.ndarray, y: np.ndarray, cv_folds: int = 5) -> Dict:
        """Train multiple models and select the best one based on F1 score.
        
        Args:
            X: Feature matrix
            y: Target labels
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dictionary of results for each model
        """
        n_positive = sum(y)
        models = self._create_models(len(X), n_positive)
        
        best_f1 = -1
        results = {}
        
        cv = StratifiedKFold(n_splits=min(cv_folds, n_positive), shuffle=True, random_state=42)
        
        for name, model in models.items():
            try:
                # Cross-validation scores
                scores = cross_val_score(model, X, y, cv=cv, scoring='f1')
                mean_f1 = scores.mean()
                std_f1 = scores.std()
                
                # Fit on full data
                model.fit(X, y)
                self.models[name] = model
                
                results[name] = {
                    'mean_f1': mean_f1,
                    'std_f1': std_f1,
                    'model': model
                }
                
                if mean_f1 > best_f1:
                    best_f1 = mean_f1
                    self.best_model = model
                    self.best_model_name = name
                    
            except Exception as e:
                print(f"    Warning: {name} failed - {e}")
                continue
        
        # Compute feature importance from best model
        self._compute_feature_importance(X, y)
        
        # Extract rule thresholds
        self._extract_rule_thresholds(X, y)
        
        return results
    
    def _compute_feature_importance(self, X: np.ndarray, y: np.ndarray) -> None:
        """Compute feature importance using multiple methods."""
        if self.best_model is None:
            return
        
        importance_scores = np.zeros(len(self.feature_names))
        
        # Method 1: Native feature importance (tree-based models)
        if hasattr(self.best_model, 'feature_importances_'):
            importance_scores += self.best_model.feature_importances_
        
        # Method 2: Permutation importance
        try:
            perm_imp = permutation_importance(
                self.best_model, X, y, n_repeats=10, random_state=42, n_jobs=-1
            )
            perm_scores = perm_imp.importances_mean
            if perm_scores.max() > 0:
                perm_scores = perm_scores / perm_scores.max()
            importance_scores += perm_scores
        except Exception:
            pass
        
        # Normalize final scores
        if importance_scores.max() > 0:
            importance_scores = importance_scores / importance_scores.max()
        
        self.feature_importance = dict(zip(self.feature_names, importance_scores))
    
    def _extract_rule_thresholds(self, X: np.ndarray, y: np.ndarray) -> None:
        """Extract optimal thresholds for each important feature."""
        if self.feature_importance is None:
            return
        
        # Get top features
        sorted_features = sorted(self.feature_importance.items(), key=lambda x: -x[1])
        top_features = [f for f, imp in sorted_features if imp > 0.1][:10]
        
        for feat in top_features:
            feat_idx = self.feature_names.index(feat)
            feat_values = X[:, feat_idx]
            
            best_threshold, best_gain = None, -1
            
            unique_vals = np.unique(feat_values)
            if len(unique_vals) <= 1:
                continue
            
            thresholds = (unique_vals[:-1] + unique_vals[1:]) / 2
            
            for thresh in thresholds[:50]:
                left_mask = feat_values <= thresh
                right_mask = ~left_mask
                
                if sum(left_mask) < 3 or sum(right_mask) < 3:
                    continue
                
                p_left = y[left_mask].mean() if sum(left_mask) > 0 else 0
                p_right = y[right_mask].mean() if sum(right_mask) > 0 else 0
                
                gain = abs(p_left - p_right)
                
                if gain > best_gain:
                    best_gain = gain
                    best_threshold = thresh
            
            if best_threshold is not None:
                self.rule_thresholds[feat] = {
                    'threshold': best_threshold,
                    'direction': '>' if y[feat_values > best_threshold].mean() > y[feat_values <= best_threshold].mean() else '<=',
                    'gain': best_gain
                }
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the best model."""
        if self.best_model is None:
            return np.zeros(len(X))
        return self.best_model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities using the best model."""
        if self.best_model is None:
            return np.zeros((len(X), 2))
        if hasattr(self.best_model, 'predict_proba'):
            return self.best_model.predict_proba(X)
        else:
            preds = self.predict(X)
            return np.column_stack([1-preds, preds])
    
    def get_top_features(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top n most important features."""
        if self.feature_importance is None:
            return []
        return sorted(self.feature_importance.items(), key=lambda x: -x[1])[:n]
    
    def save(self, path: Path) -> None:
        """Save model to file."""
        with open(path, 'wb') as f:
            pickle.dump({
                'best_model': self.best_model,
                'best_model_name': self.best_model_name,
                'feature_importance': self.feature_importance,
                'rule_thresholds': self.rule_thresholds,
                'feature_names': self.feature_names
            }, f)
    
    def load(self, path: Path) -> None:
        """Load model from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.best_model = data['best_model']
            self.best_model_name = data['best_model_name']
            self.feature_importance = data['feature_importance']
            self.rule_thresholds = data['rule_thresholds']
            self.feature_names = data['feature_names']


class SurrogateTreeExtractor:
    """Extract interpretable decision rules from ensemble predictor using surrogate tree."""
    
    def __init__(self, feature_names: List[str] = None, max_depth: int = 4):
        """Initialize surrogate tree extractor.
        
        Args:
            feature_names: List of feature names
            max_depth: Maximum tree depth
        """
        self.feature_names = feature_names or FEATURE_NAMES
        self.max_depth = max_depth
        self.surrogate_tree = None
        self.fidelity_score = None
        self.rules = []
        self.bool_features = BOOL_FEATURES
    
    def fit(self, X: np.ndarray, ensemble_predictor: EnsembleAnomalyPredictor,
            y_true: np.ndarray = None) -> Dict:
        """Train surrogate tree on ensemble's predictions.
        
        Args:
            X: Feature matrix
            ensemble_predictor: Trained ensemble predictor
            y_true: True labels (optional, for evaluation)
            
        Returns:
            Dictionary of metrics
        """
        # Get ensemble predictions as "teacher labels"
        y_ensemble = ensemble_predictor.predict(X)
        
        # Train surrogate tree on ensemble predictions
        self.surrogate_tree = DecisionTreeClassifier(
            max_depth=self.max_depth,
            min_samples_leaf=max(5, int(len(X) * 0.02)),
            min_samples_split=max(10, int(len(X) * 0.04)),
            class_weight='balanced',
            random_state=42
        )
        self.surrogate_tree.fit(X, y_ensemble)
        
        # Compute fidelity
        y_surrogate = self.surrogate_tree.predict(X)
        self.fidelity_score = accuracy_score(y_ensemble, y_surrogate)
        
        # Extract rules
        self.rules = self._extract_rules()
        
        metrics = {
            'fidelity': self.fidelity_score,
            'n_rules': len(self.rules),
            'tree_depth': self.surrogate_tree.get_depth(),
            'n_leaves': self.surrogate_tree.get_n_leaves()
        }
        
        if y_true is not None:
            p, r, f1, _ = precision_recall_fscore_support(
                y_true, y_surrogate, average='binary', zero_division=0
            )
            metrics.update({
                'precision': p,
                'recall': r,
                'f1': f1,
                'accuracy': accuracy_score(y_true, y_surrogate)
            })
        
        return metrics
    
    def _extract_rules(self) -> List[Dict]:
        """Extract all decision rules from the surrogate tree."""
        tree_ = self.surrogate_tree.tree_
        feature_name = [self.feature_names[i] if i != -2 else 'undefined'
                       for i in tree_.feature]
        rules = []
        
        def recurse(node, conditions, depth):
            if tree_.feature[node] != -2:  # Not a leaf
                name = feature_name[node]
                thresh = tree_.threshold[node]
                recurse(tree_.children_left[node],
                       conditions + [(name, '<=', thresh)], depth + 1)
                recurse(tree_.children_right[node],
                       conditions + [(name, '>', thresh)], depth + 1)
            else:  # Leaf node
                values = tree_.value[node].flatten()
                n_samples = tree_.n_node_samples[node]
                
                if len(values) >= 2:
                    prob_positive = values[1] / sum(values) if sum(values) > 0 else 0
                else:
                    prob_positive = 0.5
                
                if prob_positive >= 0.5 and n_samples >= 3:
                    rules.append({
                        'conditions': conditions,
                        'probability': prob_positive,
                        'support': n_samples,
                        'depth': depth,
                        'confidence': prob_positive
                    })
        
        recurse(0, [], 0)
        rules = sorted(rules, key=lambda x: (-x['confidence'], -x['support']))
        return rules
    
    def format_fol(self, rule: Dict, class_name: str) -> str:
        """Format rule as First-Order Logic expression."""
        conditions = rule['conditions']
        formatted = []
        
        for feat, op, thresh in conditions:
            if feat in self.bool_features:
                if op == '>':
                    formatted.append(f'{feat}(t)')
                else:
                    formatted.append(f'¬{feat}(t)')
            else:
                formatted.append(f'{feat}(t) {op} {thresh:.3f}')
        
        if not formatted:
            return f'∀t : TRUE ⇒ {class_name}'
        
        return f'∀t : {" ∧ ".join(formatted)} ⇒ {class_name}'
    
    def format_natural_language(self, rule: Dict, class_name: str) -> str:
        """Format rule as human-readable natural language."""
        conditions = rule['conditions']
        explanations = []
        
        for feat, op, thresh in conditions:
            feat_readable = feat.replace('_', ' ')
            
            if feat in self.bool_features:
                if op == '>':
                    explanations.append(f"robot is {feat_readable}")
                else:
                    explanations.append(f"robot is NOT {feat_readable}")
            else:
                if op == '>':
                    explanations.append(f"{feat_readable} > {thresh:.3f}")
                else:
                    explanations.append(f"{feat_readable} ≤ {thresh:.3f}")
        
        if not explanations:
            return f"Always predict {class_name}"
        
        return f"IF {' AND '.join(explanations)} THEN {class_name}"
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the surrogate tree."""
        if self.surrogate_tree is None:
            return np.zeros(len(X))
        return self.surrogate_tree.predict(X)
    
    def evaluate_rule_coverage(self, X: np.ndarray, y: np.ndarray, 
                               scenarios: List[str]) -> List[Dict]:
        """Evaluate each rule's coverage and performance."""
        evaluated_rules = []
        scen_arr = np.array(scenarios)
        total_scenarios = len(np.unique(scen_arr))
        
        for rule in self.rules:
            mask = np.ones(len(X), dtype=bool)
            for feat, op, thresh in rule['conditions']:
                feat_idx = self.feature_names.index(feat)
                if op == '>':
                    mask &= X[:, feat_idx] > thresh
                else:
                    mask &= X[:, feat_idx] <= thresh
            
            n_matches = sum(mask)
            if n_matches > 0:
                tp = int(np.sum((y == 1) & mask))
                fp = int(np.sum((y == 0) & mask))
                fn = int(np.sum((y == 1) & ~mask))
                tn = int(np.sum((y == 0) & ~mask))
                precision = tp / n_matches if n_matches > 0 else 0.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                coverage = n_matches / len(X)
                scen_hits = len(np.unique(scen_arr[mask]))
                scen_freq = scen_hits / total_scenarios if total_scenarios > 0 else 0.0
                
                evaluated_rules.append({
                    **rule,
                    'coverage': coverage,
                    'precision': precision,
                    'recall': recall,
                    'n_matches': n_matches,
                    'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
                    'scenario_hits': scen_hits,
                    'scenario_frequency': scen_freq
                })
        
        return evaluated_rules
    
    def save(self, path: Path) -> None:
        """Save surrogate tree to file."""
        with open(path, 'wb') as f:
            pickle.dump({
                'surrogate_tree': self.surrogate_tree,
                'fidelity_score': self.fidelity_score,
                'rules': self.rules,
                'feature_names': self.feature_names
            }, f)
    
    def load(self, path: Path) -> None:
        """Load surrogate tree from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.surrogate_tree = data['surrogate_tree']
            self.fidelity_score = data['fidelity_score']
            self.rules = data['rules']
            self.feature_names = data['feature_names']
