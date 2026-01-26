"""
Main pipeline orchestration for the anomaly detection and prediction system.
Provides unified interface for training, prediction, and visualization.
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from .config import ANOM_LABELS, FEATURE_NAMES, STATIC_FEATURE_NAMES, configure_matplotlib
from .data_structures import RunData, ScenarioConfig, PredictionResult
from .data_loading import DatasetLoader
from .preprocessing import DataPreprocessor
from .metrics import MetricCalculator
from .anomaly_detection import RuleBasedAnomalyDetector, MLAnomalyDetector
from .feature_engineering import MapGeometry, ComputableFunctions, AtomicRelations, FeatureExtractor
from .models import EnsembleAnomalyPredictor, SurrogateTreeExtractor


class AnomalyDetectionPipeline:
    """Main pipeline for anomaly detection and prediction with training and prediction modes."""
    
    def __init__(self, dataset_path: Path = None, maps_path: Path = None, 
                 models_path: Path = None, images_path: Path = None):
        """Initialize the pipeline.
        
        Args:
            dataset_path: Path to the dataset directory
            maps_path: Path to maps_details.json
            models_path: Path to save/load trained models
            images_path: Path to save visualizations
        """
        self.dataset_path = Path(dataset_path) if dataset_path else Path('ws25_aia_complete_data')
        self.maps_path = Path(maps_path) if maps_path else Path('maps_details.json')
        self.models_path = Path(models_path) if models_path else Path('models')
        self.images_path = Path(images_path) if images_path else Path('images')
        
        # Create directories if needed
        self.models_path.mkdir(exist_ok=True)
        self.images_path.mkdir(exist_ok=True)
        
        # Initialize components
        self.loader = None
        self.preprocessor = DataPreprocessor()
        self.metric_calculator = MetricCalculator()
        self.rule_detector = RuleBasedAnomalyDetector()
        self.ml_detector = MLAnomalyDetector(contamination=0.15)
        
        # Feature engineering
        self.map_geometry = None
        self.functions = None
        self.relations = None
        self.extractor = None
        
        # Trained models - SCENARIO-BASED (static features only)
        self.scenario_ensemble: Dict[str, EnsembleAnomalyPredictor] = {}
        self.scenario_surrogate: Dict[str, SurrogateTreeExtractor] = {}
        self.scenario_metrics: Dict[str, Dict] = {}
        
        # Trained models - LOG-BASED (all features)
        self.log_ensemble: Dict[str, EnsembleAnomalyPredictor] = {}
        self.log_surrogate: Dict[str, SurrogateTreeExtractor] = {}
        self.log_metrics: Dict[str, Dict] = {}
        
        # Legacy references for backward compatibility
        self.ensemble_predictors = self.log_ensemble
        self.surrogate_extractors = self.log_surrogate
        self.surrogate_metrics = self.log_metrics
        
        # Training data
        self.valid_runs: List[RunData] = []
        self.feature_matrix: Optional[np.ndarray] = None
        self.static_feature_matrix: Optional[np.ndarray] = None
        self.per_anomaly_labels: Dict[str, np.ndarray] = {}
        
        self._initialize_feature_engineering()
    
    def _initialize_feature_engineering(self) -> None:
        """Initialize feature engineering components."""
        if self.maps_path.exists():
            self.map_geometry = MapGeometry(self.maps_path)
            self.functions = ComputableFunctions(self.map_geometry)
            self.relations = AtomicRelations(self.functions)
            self.extractor = FeatureExtractor(self.map_geometry, self.relations, self.functions)
    
    def train(self, max_scenarios: int = None, verbose: bool = True) -> Dict:
        """Train all models on the dataset.
        
        Args:
            max_scenarios: Maximum number of scenarios to use (None for all)
            verbose: Print progress information
            
        Returns:
            Dictionary with training results
        """
        configure_matplotlib()
        
        if verbose:
            print("=" * 60)
            print("ANOMALY DETECTION PIPELINE - TRAINING")
            print("=" * 60)
        
        # Load data
        if verbose:
            print("\n[1/6] Loading dataset...")
        self.loader = DatasetLoader(self.dataset_path)
        all_runs = self.loader.load_all_runs(max_scenarios=max_scenarios, show_progress=verbose)
        
        if verbose:
            print(f"Loaded {len(all_runs)} total runs")
        
        # Preprocess
        if verbose:
            print("\n[2/6] Preprocessing...")
        for run in tqdm(all_runs, desc='Preprocessing', disable=not verbose):
            self.preprocessor.preprocess(run)
        
        self.valid_runs = [r for r in all_runs if r.is_valid]
        if verbose:
            print(f"Valid runs after preprocessing: {len(self.valid_runs)}")
        
        # Compute metrics
        if verbose:
            print("\n[3/6] Computing metrics...")
        for run in tqdm(self.valid_runs, desc='Computing metrics', disable=not verbose):
            self.metric_calculator.compute_metrics(run)
        
        # Detect anomalies
        if verbose:
            print("\n[4/6] Detecting anomalies...")
        self.rule_detector.compute_global_stats(self.valid_runs)
        self.ml_detector.fit(self.valid_runs)
        
        for run in self.valid_runs:
            run.anomalies = self.rule_detector.detect_all(run)
            if self.ml_detector.predict(run):
                run.anomalies.append('Isolation Forest')
        
        # Extract features
        if verbose:
            print("\n[5/6] Extracting features...")
        feature_data = []
        run_info = []
        
        for run in tqdm(self.valid_runs, desc='Extracting features', disable=not verbose):
            features = self.extractor.extract_features(run)
            if features is not None:
                feature_data.append(features)
                run_info.append({
                    'scenario': run.scenario_name,
                    'run_id': run.run_id,
                    'anomalies': run.anomalies,
                    'outcome': run.outcome
                })
        
        self.feature_matrix = np.array(feature_data)
        if verbose:
            print(f"Full feature matrix shape: {self.feature_matrix.shape}")
        
        # Also extract STATIC features only (for scenario-based models)
        static_feature_data = []
        for run in self.valid_runs:
            static_features = self.extractor.extract_scenario_features(run.config, run.scenario_name)
            if static_features is not None:
                static_feature_data.append(static_features)
        
        self.static_feature_matrix = np.array(static_feature_data) if static_feature_data else None
        if verbose and self.static_feature_matrix is not None:
            print(f"Static feature matrix shape: {self.static_feature_matrix.shape}")
        
        # Create per-anomaly labels
        self.per_anomaly_labels = {
            anom: np.array([1 if anom in r['anomalies'] else 0 for r in run_info])
            for anom in ANOM_LABELS
        }
        
        # Train models for both modes
        if verbose:
            print("\n[6/7] Training LOG-BASED models (all 27 features)...")
        
        for anom in ANOM_LABELS:
            y_anom = self.per_anomaly_labels[anom]
            n_positive = sum(y_anom)
            
            if n_positive < 5:
                if verbose:
                    print(f"  {anom}: Skipped (only {n_positive} positive samples)")
                continue
            
            if verbose:
                print(f"\n  Training LOG model for {anom} ({n_positive} positive samples)...")
            
            # Train LOG ensemble (all features)
            log_predictor = EnsembleAnomalyPredictor(FEATURE_NAMES)
            log_predictor.fit(self.feature_matrix, y_anom)
            self.log_ensemble[anom] = log_predictor
            
            # Train LOG surrogate tree
            log_surrogate = SurrogateTreeExtractor(FEATURE_NAMES, max_depth=4)
            log_metrics = log_surrogate.fit(self.feature_matrix, log_predictor, y_true=y_anom)
            self.log_surrogate[anom] = log_surrogate
            self.log_metrics[anom] = log_metrics
            
            if verbose:
                print(f"    Best model: {log_predictor.best_model_name}")
                print(f"    Surrogate fidelity: {log_metrics['fidelity']:.3f}, F1: {log_metrics.get('f1', 0):.3f}")
        
        # Train SCENARIO-BASED models (static features only)
        if verbose:
            print("\n[7/7] Training SCENARIO-BASED models (static features only)...")
        
        if self.static_feature_matrix is not None and len(self.static_feature_matrix) > 0:
            for anom in ANOM_LABELS:
                y_anom = self.per_anomaly_labels[anom]
                n_positive = sum(y_anom)
                
                if n_positive < 5:
                    continue
                
                if verbose:
                    print(f"\n  Training SCENARIO model for {anom}...")
                
                # Train SCENARIO ensemble (static features only)
                scenario_predictor = EnsembleAnomalyPredictor(STATIC_FEATURE_NAMES)
                scenario_predictor.fit(self.static_feature_matrix, y_anom)
                self.scenario_ensemble[anom] = scenario_predictor
                
                # Train SCENARIO surrogate tree
                scenario_surrogate = SurrogateTreeExtractor(STATIC_FEATURE_NAMES, max_depth=4)
                scenario_metrics = scenario_surrogate.fit(self.static_feature_matrix, scenario_predictor, y_true=y_anom)
                self.scenario_surrogate[anom] = scenario_surrogate
                self.scenario_metrics[anom] = scenario_metrics
                
                if verbose:
                    print(f"    Best model: {scenario_predictor.best_model_name}")
                    print(f"    Surrogate fidelity: {scenario_metrics['fidelity']:.3f}, F1: {scenario_metrics.get('f1', 0):.3f}")
        # visualizations_all
        from . import visualization as viz
        
        output_dir = self.images_path
        output_dir.mkdir(exist_ok=True)
        
        configure_matplotlib()
        
        viz.plot_anomaly_distribution(self.valid_runs, output_dir / 'anomaly_by_category.png')

            # Supporting visualizations (available data overview)
        viz.plot_supporting_visualizations(
                self.valid_runs,
                output_dir,
                feature_names=None,  # keep best-effort (don’t assume engineered feature columns exist)
            )
        # Save models
        self._save_models()
        
        # Extract and save top 3 FOL rules from both model types
        top_rules = self._extract_and_save_top_fol_rules(verbose=verbose)
        
        if verbose:
            print("\n" + "=" * 60)
            print("TRAINING COMPLETE")
            print(f"  Log models trained: {len(self.log_ensemble)}")
            print(f"  Scenario models trained: {len(self.scenario_ensemble)}")
            print("=" * 60)
        
        return {
            'n_runs': len(self.valid_runs),
            'n_features': self.feature_matrix.shape[1] if self.feature_matrix is not None else 0,
            'n_static_features': self.static_feature_matrix.shape[1] if self.static_feature_matrix is not None else 0,
            'log_models_trained': list(self.log_ensemble.keys()),
            'scenario_models_trained': list(self.scenario_ensemble.keys()),
            'log_metrics': self.log_metrics,
            'scenario_metrics': self.scenario_metrics
        }
    
    def _save_models(self) -> None:
        """Save all trained models to disk."""
        # Save LOG models
        for anom, predictor in self.log_ensemble.items():
            predictor.save(self.models_path / f'log_ensemble_{anom}.pkl')
        
        for anom, surrogate in self.log_surrogate.items():
            surrogate.save(self.models_path / f'log_surrogate_{anom}.pkl')
        
        # Save SCENARIO models
        for anom, predictor in self.scenario_ensemble.items():
            predictor.save(self.models_path / f'scenario_ensemble_{anom}.pkl')
        
        for anom, surrogate in self.scenario_surrogate.items():
            surrogate.save(self.models_path / f'scenario_surrogate_{anom}.pkl')
        
        # Convert numpy types to native Python for JSON serialization
        def convert_to_native(obj):
            if isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(v) for v in obj]
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        # Save metadata
        with open(self.models_path / 'metadata.json', 'w') as f:
            json.dump(convert_to_native({
                'log_anomaly_types': list(self.log_ensemble.keys()),
                'scenario_anomaly_types': list(self.scenario_ensemble.keys()),
                'log_metrics': self.log_metrics,
                'scenario_metrics': self.scenario_metrics,
                'feature_names': FEATURE_NAMES,
                'static_feature_names': STATIC_FEATURE_NAMES
            }), f, indent=2)
    
    def _extract_and_save_top_fol_rules(self, verbose: bool = True) -> Dict:
        """Extract top 3 FOL rules from both scenario-based and log-based models.
        
        Args:
            verbose: Print rules to terminal
            
        Returns:
            Dictionary containing top rules for each model type
        """
        top_rules = {
            'scenario_based': {},
            'log_based': {}
        }
        
        rules_output = []
        rules_output.append("=" * 70)
        rules_output.append("TOP 3 FOL RULES FROM TRAINED MODELS")
        rules_output.append("=" * 70)
        
        # Extract from SCENARIO-BASED models
        rules_output.append("\n" + "-" * 70)
        rules_output.append("SCENARIO-BASED MODELS (Static Features Only)")
        rules_output.append("-" * 70)
        
        if self.scenario_surrogate:
            for anom, surrogate in self.scenario_surrogate.items():
                if surrogate.rules:
                    rules_output.append(f"\n[{anom}]")
                    top_3_rules = surrogate.rules[:3]  # Get top 3
                    top_rules['scenario_based'][anom] = []
                    
                    for i, rule in enumerate(top_3_rules, 1):
                        fol = surrogate.format_fol(rule, anom)
                        confidence = rule.get('confidence', rule.get('probability', 0))
                        support = rule.get('support', 0)
                        
                        rule_entry = {
                            'fol': fol,
                            'confidence': float(confidence),
                            'support': int(support)
                        }
                        top_rules['scenario_based'][anom].append(rule_entry)
                        
                        rules_output.append(f"  Rule {i}: {fol}")
                        rules_output.append(f"          Confidence: {confidence:.3f}, Support: {support} samples")
        else:
            rules_output.append("  No scenario-based models trained.")
        
        # Extract from LOG-BASED models
        rules_output.append("\n" + "-" * 70)
        rules_output.append("LOG-BASED MODELS (All Features)")
        rules_output.append("-" * 70)
        
        if self.log_surrogate:
            for anom, surrogate in self.log_surrogate.items():
                if surrogate.rules:
                    rules_output.append(f"\n[{anom}]")
                    top_3_rules = surrogate.rules[:3]  # Get top 3
                    top_rules['log_based'][anom] = []
                    
                    for i, rule in enumerate(top_3_rules, 1):
                        fol = surrogate.format_fol(rule, anom)
                        confidence = rule.get('confidence', rule.get('probability', 0))
                        support = rule.get('support', 0)
                        
                        rule_entry = {
                            'fol': fol,
                            'confidence': float(confidence),
                            'support': int(support)
                        }
                        top_rules['log_based'][anom].append(rule_entry)
                        
                        rules_output.append(f"  Rule {i}: {fol}")
                        rules_output.append(f"          Confidence: {confidence:.3f}, Support: {support} samples")
        else:
            rules_output.append("  No log-based models trained.")
        
        rules_output.append("\n" + "=" * 70)
        
        # Print to terminal
        if verbose:
            print("\n")
            for line in rules_output:
                print(line)
        
        # Save to file
        rules_file = self.models_path.parent / 'fol_rules.txt'
        with open(rules_file, 'w') as f:
            f.write('\n'.join(rules_output))
        
        if verbose:
            print(f"\nFOL rules saved to: {rules_file}")
        
        return top_rules

    def _load_models(self) -> bool:
        """Load trained models from disk."""
        metadata_path = self.models_path / 'metadata.json'
        if not metadata_path.exists():
            return False
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Load LOG models
        log_anomalies = metadata.get('log_anomaly_types', metadata.get('anomaly_types', []))
        for anom in log_anomalies:
            # Try new naming first, fallback to old naming
            ensemble_path = self.models_path / f'log_ensemble_{anom}.pkl'
            if not ensemble_path.exists():
                ensemble_path = self.models_path / f'ensemble_{anom}.pkl'
            
            surrogate_path = self.models_path / f'log_surrogate_{anom}.pkl'
            if not surrogate_path.exists():
                surrogate_path = self.models_path / f'surrogate_{anom}.pkl'
            
            if ensemble_path.exists():
                predictor = EnsembleAnomalyPredictor(FEATURE_NAMES)
                predictor.load(ensemble_path)
                self.log_ensemble[anom] = predictor
            
            if surrogate_path.exists():
                surrogate = SurrogateTreeExtractor(FEATURE_NAMES)
                surrogate.load(surrogate_path)
                self.log_surrogate[anom] = surrogate
        
        # Load SCENARIO models
        scenario_anomalies = metadata.get('scenario_anomaly_types', [])
        for anom in scenario_anomalies:
            ensemble_path = self.models_path / f'scenario_ensemble_{anom}.pkl'
            surrogate_path = self.models_path / f'scenario_surrogate_{anom}.pkl'
            
            if ensemble_path.exists():
                predictor = EnsembleAnomalyPredictor(STATIC_FEATURE_NAMES)
                predictor.load(ensemble_path)
                self.scenario_ensemble[anom] = predictor
            
            if surrogate_path.exists():
                surrogate = SurrogateTreeExtractor(STATIC_FEATURE_NAMES)
                surrogate.load(surrogate_path)
                self.scenario_surrogate[anom] = surrogate
        
        self.log_metrics = metadata.get('log_metrics', metadata.get('surrogate_metrics', {}))
        self.scenario_metrics = metadata.get('scenario_metrics', {})
        
        return len(self.log_ensemble) > 0 or len(self.scenario_ensemble) > 0
    
    def predict_scenario(self, scenario_config_path: Path, 
                         env_json_path: Path = None) -> PredictionResult:
        """Predict potential anomalies from scenario description only.
        
        Uses SCENARIO models trained on static features only (27 features).
        
        Args:
            scenario_config_path: Path to scenario.config file
            env_json_path: Path to maps_details.json (optional, uses default if not provided)
            
        Returns:
            PredictionResult with predictions and explanations
        """
        # Ensure models are loaded
        if not self.scenario_ensemble and not self.log_ensemble:
            if not self._load_models():
                raise RuntimeError("No trained models found. Run train() first.")
        
        # Check if we have scenario-specific models
        use_scenario_models = len(self.scenario_ensemble) > 0
        
        # Ensure feature engineering is initialized
        if env_json_path and env_json_path.exists():
            self.maps_path = env_json_path
            self._initialize_feature_engineering()
        
        if self.extractor is None:
            raise RuntimeError("Feature extractor not initialized. Check maps_details.json path.")
        
        # Load scenario config
        loader = DatasetLoader(Path('.'))
        config = loader.parse_scenario_config(scenario_config_path)
        
        if config is None:
            raise ValueError(f"Failed to parse scenario config: {scenario_config_path}")
        
        # Get scenario name from path
        scenario_name = scenario_config_path.parent.parent.name
        
        # Extract STATIC features only
        features = self.extractor.extract_scenario_features(config, scenario_name)
        if features is None:
            raise ValueError("Failed to extract features from scenario")
        
        features = features.reshape(1, -1)
        
        # Predict anomalies using SCENARIO models (or fallback to LOG models)
        predicted_anomalies = []
        anomaly_probabilities = {}
        explanations = {}
        fol_rules = {}
        
        models = self.scenario_ensemble if use_scenario_models else self.log_ensemble
        surrogates = self.scenario_surrogate if use_scenario_models else self.log_surrogate
        
        for anom, predictor in models.items():
            proba = predictor.predict_proba(features)[0]
            prob_anomaly = proba[1] if len(proba) > 1 else proba[0]
            anomaly_probabilities[anom] = float(prob_anomaly)
            
            if prob_anomaly >= 0.5:
                predicted_anomalies.append(anom)
                
                # Get explanation from surrogate tree
                if anom in surrogates:
                    surrogate = surrogates[anom]
                    if surrogate.rules:
                        explanations[anom] = surrogate.format_natural_language(
                            surrogate.rules[0], anom
                        )
                        fol_rules[anom] = surrogate.format_fol(surrogate.rules[0], anom)
        
        # Calculate confidence as mean probability of predicted anomalies
        confidence = np.mean([anomaly_probabilities[a] for a in predicted_anomalies]) if predicted_anomalies else 0.0
        
        return PredictionResult(
            scenario_name=scenario_name,
            mode='scenario',
            predicted_anomalies=predicted_anomalies,
            anomaly_probabilities=anomaly_probabilities,
            explanations=explanations,
            fol_rules=fol_rules,
            confidence=float(confidence)
        )
    
    def predict_logs(self, run_path: Path, scenario_config_path: Path = None,
                     env_json_path: Path = None) -> PredictionResult:
        """Detect anomalies from actual run logs.
        
        Uses LOG models trained on all 27 features including runtime metrics.
        
        Args:
            run_path: Path to the run directory
            scenario_config_path: Path to scenario.config (optional, looks in run_path if not provided)
            env_json_path: Path to maps_details.json (optional)
            
        Returns:
            PredictionResult with detected anomalies and explanations
        """
        # Ensure models are loaded
        if not self.log_ensemble:
            if not self._load_models():
                raise RuntimeError("No trained models found. Run train() first.")
        
        # Ensure feature engineering is initialized
        if env_json_path and env_json_path.exists():
            self.maps_path = env_json_path
            self._initialize_feature_engineering()
        
        run_path = Path(run_path)
        scenario_config_path = scenario_config_path or (run_path / 'scenario.config')
        
        # Load run data
        loader = DatasetLoader(run_path.parent.parent)
        scenario_name = run_path.parent.name
        run_id = int(run_path.name) if run_path.name.isdigit() else 0
        
        run = loader.load_run(run_path, scenario_name, run_id)
        
        if not run.is_valid:
            raise ValueError(f"Invalid run data: {run.error_msg}")
        
        # Preprocess and compute metrics
        run = self.preprocessor.preprocess(run)
        if not run.is_valid:
            raise ValueError(f"Preprocessing failed: {run.error_msg}")
        
        run = self.metric_calculator.compute_metrics(run)
        
        # Detect rule-based anomalies
        run.anomalies = self.rule_detector.detect_all(run)
        if self.ml_detector.is_fitted and self.ml_detector.predict(run):
            run.anomalies.append('Isolation Forest')
        
        # Extract ALL features for ensemble prediction (including runtime metrics)
        features = self.extractor.extract_features(run)
        if features is None:
            raise ValueError("Failed to extract features from run")
        
        features = features.reshape(1, -1)
        
        # Combine rule-based and LOG ensemble predictions
        predicted_anomalies = list(run.anomalies)  # Start with rule-based detections
        anomaly_probabilities = {}
        explanations = {}
        fol_rules = {}
        
        for anom, predictor in self.log_ensemble.items():
            proba = predictor.predict_proba(features)[0]
            prob_anomaly = proba[1] if len(proba) > 1 else proba[0]
            anomaly_probabilities[anom] = float(prob_anomaly)
            
            # Add to predictions if not already detected by rules
            if prob_anomaly >= 0.5 and anom not in predicted_anomalies:
                predicted_anomalies.append(anom)
            
            # Get explanation for all detected anomalies
            if anom in predicted_anomalies and anom in self.log_surrogate:
                surrogate = self.log_surrogate[anom]
                if surrogate.rules:
                    explanations[anom] = surrogate.format_natural_language(
                        surrogate.rules[0], anom
                    )
                    fol_rules[anom] = surrogate.format_fol(surrogate.rules[0], anom)
        
        confidence = np.mean([anomaly_probabilities.get(a, 1.0) for a in predicted_anomalies]) if predicted_anomalies else 0.0
        
        return PredictionResult(
            scenario_name=scenario_name,
            run_id=run_id,
            mode='log',
            predicted_anomalies=predicted_anomalies,
            anomaly_probabilities=anomaly_probabilities,
            explanations=explanations,
            fol_rules=fol_rules,
            metrics=run.metrics,
            confidence=float(confidence)
        )
    
    def generate_visualizations(self, output_dir: Path = None) -> None:
        """Generate all visualizations.
        
        Args:
            output_dir: Directory to save visualizations
        """
        from . import visualization as viz
        
        output_dir = Path(output_dir) if output_dir else self.images_path
        output_dir.mkdir(exist_ok=True)
        
        configure_matplotlib()
        
        print("Generating visualizations...")
        
        # Anomaly distribution
        if self.valid_runs:
            viz.plot_anomaly_distribution(self.valid_runs, output_dir / 'anomaly_by_category.png')

            # Supporting visualizations (available data overview)
            viz.plot_supporting_visualizations(
                self.valid_runs,
                output_dir / "supporting",
                feature_names=None,  # keep best-effort (don’t assume engineered feature columns exist)
            )

        # Surrogate trees - LOG models
        if self.log_surrogate:
            viz.plot_surrogate_trees(
                self.log_surrogate, 
                self.log_metrics,
                FEATURE_NAMES,
                output_dir / 'log_surrogate_trees.png'
            )
            
            viz.plot_feature_importance(
                self.log_surrogate,
                FEATURE_NAMES,
                output_dir / 'log_feature_importance.png'
            )
        
        # Surrogate trees - SCENARIO models
        if self.scenario_surrogate:
            viz.plot_surrogate_trees(
                self.scenario_surrogate, 
                self.scenario_metrics,
                STATIC_FEATURE_NAMES,
                output_dir / 'scenario_surrogate_trees.png'
            )
            
            viz.plot_feature_importance(
                self.scenario_surrogate,
                STATIC_FEATURE_NAMES,
                output_dir / 'scenario_feature_importance.png'
            )
        
        # Model comparison - LOG
        if self.log_metrics:
            gen_data = []
            for anom, metrics in self.log_metrics.items():
                gen_data.append({
                    'Anomaly': anom,
                    'Fidelity': metrics.get('fidelity', 0),
                    'Accuracy': metrics.get('accuracy', 0),
                    'Precision': metrics.get('precision', 0),
                    'Recall': metrics.get('recall', 0),
                    'F1': metrics.get('f1', 0)
                })
            if gen_data:
                gen_df = pd.DataFrame(gen_data)
                viz.plot_generalization_summary(gen_df, output_dir / 'log_model_performance.png')
        
        # Model comparison - SCENARIO
        if self.scenario_metrics:
            gen_data = []
            for anom, metrics in self.scenario_metrics.items():
                gen_data.append({
                    'Anomaly': anom,
                    'Fidelity': metrics.get('fidelity', 0),
                    'Accuracy': metrics.get('accuracy', 0),
                    'Precision': metrics.get('precision', 0),
                    'Recall': metrics.get('recall', 0),
                    'F1': metrics.get('f1', 0)
                })
            if gen_data:
                gen_df = pd.DataFrame(gen_data)
                viz.plot_generalization_summary(gen_df, output_dir / 'scenario_model_performance.png')
        
        
        print(f"Visualizations saved to {output_dir}")
