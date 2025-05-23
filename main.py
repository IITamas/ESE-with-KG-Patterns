from sparql_wrapper import SPARQLWrapperCache
from set_extension import CompositeGraphBasedSetExtension
from visualization import multiGraphVizualizationGraphviz
from experiment_runner import ExperimentRunner
import argparse
import os
from datetime import datetime


def run_simple_example(output_dir=None, visualize=False):
    # Initialize SPARQL wrapper with DBpedia endpoint
    sparql = SPARQLWrapperCache("http://dbpedia.org/sparql", "http://dbpedia.org", 180)

    # Define filter for edge types
    filter = '"(.*sameAs|.*wiki.*|.*seeAlso|.*wordnet_type|.*subdivision|.*subject|.*depiction|.*isPrimaryTopicOf|.*wasDerivedFrom|.*homepage|.*thumbnail|.*hypernym|.*exactMatch)"'

    # Initialize the set extension model
    model = CompositeGraphBasedSetExtension(
        sparql, path_length=3, right_extensions=1, filter=filter, min_or_num=2
    )

    # Example seed entities
    seed_entities = [
        "http://dbpedia.org/resource/Budapest",
        "http://dbpedia.org/resource/Szeged",
        "http://dbpedia.org/resource/Mátraverebély",
    ]

    # Run the entity set expansion
    print(f"Running entity set expansion with seed entities: {seed_entities}")
    results, query = model.get_results(seed_entities)

    # Display results
    print("\nGenerated SPARQL Query:")
    print(query)

    print("\nExpanded Entity Set:")
    for entity in results:
        print(f"- {entity}")

    # Calculate metrics
    if results:
        print(f"\nReturned {len(results)} entities")
    else:
        print("\nNo results returned")

    # Create visualization if requested
    if visualize and output_dir:
        from visualization_manager import VisualizationManager

        viz_manager = VisualizationManager(output_dir)

        # Get paths for visualization
        paths = model.explorer.get_expansion_graph(seed_entities)

        # Save visualizations
        if paths:
            viz_path = viz_manager.save_path_visualization(paths, "example", "example")
            if viz_path:
                print(f"Path visualization saved to: {viz_path}")

        viz_entities = viz_manager.save_expanded_entities_graph(
            seed_entities, results, "example", "example"
        )
        if viz_entities:
            print(f"Entities visualization saved to: {viz_entities}")


def run_experiments(
    database_path, output_dir, templates, sample_size, max_queries, visualize
):
    # Initialize experiment runner
    runner = ExperimentRunner(database_path, output_dir=output_dir, visualize=visualize)

    # Run experiments
    runner.run_experiments(templates, sample_size, max_queries)

    # Calculate and display overall metrics
    overall_metrics = runner.calculate_overall_metrics()
    print("\n=== Overall Metrics ===")
    print(f"Precision: {overall_metrics['precision']:.2f}")
    print(f"Recall: {overall_metrics['recall']:.2f}")
    print(f"F1: {overall_metrics['f1']:.2f}")
    print(f"Number of queries: {overall_metrics['count']}")

    # Save results
    results_path = runner.save_results()
    print(
        f"All results and visualizations have been saved to: {os.path.dirname(results_path)}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run entity set expansion experiments")
    parser.add_argument("--example", action="store_true", help="Run a simple example")
    parser.add_argument("--database", type=str, help="Path to the database JSON file")
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Directory to save results and visualizations",
    )
    parser.add_argument(
        "--templates",
        type=int,
        nargs="+",
        default=[1, 2, 301, 302],
        help="Template IDs to run experiments on",
    )
    parser.add_argument(
        "--sample_size", type=int, default=5, help="Number of seed entities to use"
    )
    parser.add_argument(
        "--max_queries",
        type=int,
        default=5,
        help="Maximum number of queries per template",
    )
    parser.add_argument(
        "--visualize", action="store_true", help="Generate and save visualizations"
    )

    args = parser.parse_args()

    if args.example or not args.database:
        run_simple_example(args.output, args.visualize)
    else:
        run_experiments(
            args.database,
            args.output,
            args.templates,
            args.sample_size,
            args.max_queries,
            args.visualize,
        )
