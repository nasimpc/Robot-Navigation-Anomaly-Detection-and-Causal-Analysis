"""
Command-line interface for the anomaly detection pipeline.
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Anomaly Detection Pipeline for Robot Navigation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train models on dataset
  python -m anomaly_detection train --dataset ws25_aia_complete_data --maps maps_details.json

  # Scenario-based prediction (predict from scenario description only)
  python -m anomaly_detection predict-scenario \\
      --scenario path/to/scenario.config \\
      --env maps_details.json \\
      --output results.json

  # Log-based prediction (detect from actual run logs)
  python -m anomaly_detection predict-logs \\
      --run path/to/run_directory \\
      --env maps_details.json \\
      --output results.json

  # Generate visualizations
  python -m anomaly_detection visualize --output images/
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train models on dataset')
    train_parser.add_argument('--dataset', type=str, default='ws25_aia_complete_data',
                             help='Path to dataset directory')
    train_parser.add_argument('--maps', type=str, default='maps_details.json',
                             help='Path to maps_details.json')
    train_parser.add_argument('--models', type=str, default='models',
                             help='Directory to save trained models')
    train_parser.add_argument('--max-scenarios', type=int, default=None,
                             help='Maximum number of scenarios to process')
    train_parser.add_argument('--quiet', action='store_true',
                             help='Suppress progress output')
    
    # Scenario-based prediction
    scenario_parser = subparsers.add_parser('predict-scenario',
                                            help='Predict anomalies from scenario description')
    scenario_parser.add_argument('--scenario', type=str, required=True,
                                help='Path to scenario.config file')
    scenario_parser.add_argument('--env', type=str, default='maps_details.json',
                                help='Path to maps_details.json')
    scenario_parser.add_argument('--models', type=str, default='models',
                                help='Directory containing trained models')
    scenario_parser.add_argument('--output', type=str, default=None,
                                help='Output JSON file for predictions')
    
    # Log-based prediction
    logs_parser = subparsers.add_parser('predict-logs',
                                        help='Detect anomalies from run logs')
    logs_parser.add_argument('--run', type=str, required=True,
                            help='Path to run directory')
    logs_parser.add_argument('--scenario', type=str, default=None,
                            help='Path to scenario.config (optional, looks in run dir)')
    logs_parser.add_argument('--env', type=str, default='maps_details.json',
                            help='Path to maps_details.json')
    logs_parser.add_argument('--models', type=str, default='models',
                            help='Directory containing trained models')
    logs_parser.add_argument('--output', type=str, default=None,
                            help='Output JSON file for predictions')
    
    # Visualize command
    viz_parser = subparsers.add_parser('visualize', help='Generate visualizations')
    viz_parser.add_argument('--dataset', type=str, default='ws25_aia_complete_data',
                           help='Path to dataset directory')
    viz_parser.add_argument('--maps', type=str, default='maps_details.json',
                           help='Path to maps_details.json')
    viz_parser.add_argument('--models', type=str, default='models',
                           help='Directory containing trained models')
    viz_parser.add_argument('--output', type=str, default='images',
                           help='Directory to save visualizations')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Import pipeline here to avoid slow startup for --help
    from .pipeline import AnomalyDetectionPipeline
    
    if args.command == 'train':
        pipeline = AnomalyDetectionPipeline(
            dataset_path=args.dataset,
            maps_path=args.maps,
            models_path=args.models
        )
        results = pipeline.train(
            max_scenarios=args.max_scenarios,
            verbose=not args.quiet
        )
        print(f"\nTraining complete. Models saved to: {args.models}")
        print(f"Log models trained for: {', '.join(results.get('log_models_trained', []))}")
        print(f"Scenario models trained for: {', '.join(results.get('scenario_models_trained', []))}")
    
    elif args.command == 'predict-scenario':
        pipeline = AnomalyDetectionPipeline(
            maps_path=args.env,
            models_path=args.models
        )
        
        result = pipeline.predict_scenario(
            scenario_config_path=Path(args.scenario),
            env_json_path=Path(args.env) if args.env else None
        )
        
        output_dict = result.to_dict()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output_dict, f, indent=2)
            print(f"Predictions saved to: {args.output}")
        else:
            print("\n" + "=" * 60)
            print("SCENARIO-BASED PREDICTION RESULTS")
            print("=" * 60)
            print(f"\nScenario: {result.scenario_name}")
            print(f"Mode: {result.mode}")
            print(f"Confidence: {result.confidence:.2%}")
            print(f"\nPredicted Anomalies: {', '.join(result.predicted_anomalies) or 'None'}")
            
            if result.explanations:
                print("\nExplanations:")
                for anom, explanation in result.explanations.items():
                    print(f"  {anom}: {explanation}")
            
            if result.fol_rules:
                print("\nFOL Rules:")
                for anom, rule in result.fol_rules.items():
                    print(f"  {anom}: {rule}")
    
    elif args.command == 'predict-logs':
        pipeline = AnomalyDetectionPipeline(
            maps_path=args.env,
            models_path=args.models
        )
        
        result = pipeline.predict_logs(
            run_path=Path(args.run),
            scenario_config_path=Path(args.scenario) if args.scenario else None,
            env_json_path=Path(args.env) if args.env else None
        )
        
        output_dict = result.to_dict()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output_dict, f, indent=2)
            print(f"Predictions saved to: {args.output}")
        else:
            print("\n" + "=" * 60)
            print("LOG-BASED PREDICTION RESULTS")
            print("=" * 60)
            print(f"\nScenario: {result.scenario_name}")
            print(f"Run ID: {result.run_id}")
            print(f"Mode: {result.mode}")
            print(f"Confidence: {result.confidence:.2%}")
            print(f"\nDetected Anomalies: {', '.join(result.predicted_anomalies) or 'None'}")
            
            if result.metrics:
                print(f"\nMetrics:")
                print(f"  Mean Position Error: {result.metrics.mean_pos_error:.4f} m")
                print(f"  RMSE Position: {result.metrics.rmse_pos:.4f} m")
                print(f"  Mean Yaw Error: {result.metrics.mean_yaw_error:.4f} rad")
                print(f"  Path Efficiency: {result.metrics.path_efficiency:.2%}")
                print(f"  Duration: {result.metrics.duration:.2f} s")
                print(f"  Mean AMCL Uncertainty: {result.metrics.mean_amcl_uncertainty:.4f}")
            
            if result.explanations:
                print("\nExplanations:")
                for anom, explanation in result.explanations.items():
                    print(f"  {anom}: {explanation}")
    
    elif args.command == 'visualize':
        pipeline = AnomalyDetectionPipeline(
            dataset_path=args.dataset,
            maps_path=args.maps,
            models_path=args.models,
            images_path=args.output
        )
        
        # Load models to get metrics
        if not pipeline._load_models():
            print("Warning: Could not load trained models. Some visualizations may be missing.")
        
        pipeline.generate_visualizations(output_dir=Path(args.output))


if __name__ == '__main__':
    main()
