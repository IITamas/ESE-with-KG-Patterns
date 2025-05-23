import argparse
from pathlib import Path
from sparql_wrapper import SPARQLWrapperCache
from set_extension import CompositeGraphBasedSetExtension
from experiment_runner import ExperimentRunner
from visualization_manager import VisualizationManager
from config import (
    DEFAULT_SPARQL_ENDPOINT,
    DEFAULT_GRAPH,
    DEFAULT_TIMEOUT,
    DEFAULT_FILTER_PATTERN,
)


def run_simple_expansion_example(output_base_dir="output", visualize=False):
    print("Running a simple entity expansion example...")
    sparql = SPARQLWrapperCache(DEFAULT_SPARQL_ENDPOINT, DEFAULT_GRAPH, DEFAULT_TIMEOUT)
    model = CompositeGraphBasedSetExtension(
        sparql,
        path_length=3,
        right_extensions=1,
        filter_pattern=DEFAULT_FILTER_PATTERN,
        min_entities_for_values_clause=2,
        max_entities_in_path_node=5,
    )
    seed_entities = [
        "http://dbpedia.org/resource/Budapest",
        "http://dbpedia.org/resource/Szeged",
        "http://dbpedia.org/resource/Mátraverebély",
    ]
    print(f"Seed entities: {seed_entities}")
    expanded_entities, generated_query, paths_for_viz = model.get_results(seed_entities)

    print("\nGenerated SPARQL Query:")
    print(generated_query)
    print(f"\nExpanded Entity Set (found {len(expanded_entities)}):")
    for i, entity in enumerate(expanded_entities[:10]):
        print(f"- {entity}")
    if len(expanded_entities) > 10:
        print("  ... and more.")

    if visualize:
        print(f"\nGenerating visualizations in base directory: {output_base_dir}")
        viz_manager = VisualizationManager(output_dir=output_base_dir)

        if paths_for_viz:
            path_viz_file = viz_manager.save_path_visualization(
                paths_for_viz, "simple_example", "example_template"
            )
            if path_viz_file:
                print(f"Path visualization saved: {path_viz_file}")
        entity_viz_file = viz_manager.save_expanded_entities_graph(
            seed_entities, expanded_entities, "simple_example", "example_template"
        )
        if entity_viz_file:
            print(f"Entity visualization saved: {entity_viz_file}")
        print(f"Check visualizations in: {viz_manager.output_dir_for_run}")


def run_full_experiments(
    database_file,
    output_base_dir,
    template_ids_list,
    num_seed_entities,
    max_queries,
    create_visualizations,
):
    print(
        f"Starting full experiments. Database: {database_file}, Output base: {output_base_dir}"
    )
    if not Path(database_file).exists():
        print(f"Error: Database file not found at '{database_file}'")
        return

    runner = ExperimentRunner(
        database_path=database_file,
        output_dir=output_base_dir,
        visualize=create_visualizations,
    )
    runner.run_all_experiments(
        template_ids_list=template_ids_list,
        sample_size=num_seed_entities,
        max_queries_per_template=max_queries,
    )
    overall_metrics = runner.calculate_overall_metrics_across_all_templates()
    print("\n===== Overall Experiment Metrics =====")
    if overall_metrics["count"] > 0:
        print(f"  Average Precision: {overall_metrics['precision']:.3f}")
        print(f"  Average Recall:    {overall_metrics['recall']:.3f}")
        print(f"  Average F1-Score:  {overall_metrics['f1']:.3f}")
        print(f"  Total Queries Evaluated: {overall_metrics['count']}")
    else:
        print("  No queries were successfully processed to calculate overall metrics.")

    saved_results_path = runner.save_results(filename="all_experiment_results.json")
    print(
        f"All experiment results and visualizations (if enabled) are in the run directory within: {output_base_dir}"
    )
    print(f"Main results JSON saved at: {saved_results_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Knowledge Graph Entity Set Expansion CLI"
    )
    parser.add_argument(
        "--example", action="store_true", help="Run a simple demonstration example."
    )
    parser.add_argument(
        "--database",
        type=str,
        help="Path to the JSON database file for full experiments.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="output",
        help="Base directory for all outputs (results, visualizations). Default: 'output'",
    )
    parser.add_argument(
        "--templates",
        type=int,
        nargs="+",
        default=[1, 2, 301, 302, 303],
        help="List of template IDs to run experiments on. Default: [1, 2, 301, 302, 303]",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=5,
        help="Number of seed entities to sample for experiments. Default: 5",
    )
    parser.add_argument(
        "--max_queries",
        type=int,
        default=3,
        help="Maximum number of queries to run per template ID for experiments. Default: 3",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Enable generation of visualizations for experiments and examples.",
    )

    args = parser.parse_args()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    if args.example:
        run_simple_expansion_example(
            output_base_dir=args.output_dir, visualize=args.visualize
        )
    elif args.database:
        run_full_experiments(
            database_file=args.database,
            output_base_dir=args.output_dir,
            template_ids_list=args.templates,
            num_seed_entities=args.seeds,
            max_queries=args.max_queries,
            create_visualizations=args.visualize,
        )
    else:
        print("Please specify either --example or --database <path_to_db.json> to run.")
        parser.print_help()
