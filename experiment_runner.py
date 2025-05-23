import json
import random
from db_parser import DatabaseParser
from sparql_wrapper import SPARQLWrapperCache
from set_extension import CompositeGraphBasedSetExtension
from evaluation import EvaluationMetrics
from visualization_manager import VisualizationManager


class ExperimentRunner:
    """Run entity set expansion experiments on a database of queries."""

    def __init__(
        self,
        database_path,
        sparql_endpoint="http://dbpedia.org/sparql",
        default_graph="http://dbpedia.org",
        timeout=180,
        output_dir="output",
        visualize=False,
    ):
        """Initialize the experiment runner."""
        self.db_parser = DatabaseParser(database_path)
        self.sparql = SPARQLWrapperCache(sparql_endpoint, default_graph, timeout)
        self.filter_pattern = '"(.*sameAs|.*wiki.*|.*seeAlso|.*wordnet_type|.*subdivision|.*subject|.*depiction|.*isPrimaryTopicOf|.*wasDerivedFrom|.*homepage|.*thumbnail|.*hypernym|.*exactMatch)"'
        self.results = {}
        self.visualize = visualize
        self.viz_manager = VisualizationManager(output_dir) if visualize else None

    def create_model(
        self, path_length=3, right_extensions=1, min_or_num=2, max_or_num=5
    ):
        """Create an entity set expansion model with the given parameters."""
        return CompositeGraphBasedSetExtension(
            self.sparql,
            path_length=path_length,
            right_extensions=right_extensions,
            filter=self.filter_pattern,
            min_or_num=min_or_num,
            max_or_num=max_or_num,
        )

    def run_experiment_by_template(self, template_id, sample_size=5, max_queries=10):
        """Run experiment on queries with a specific template ID."""
        # Get queries with the given template
        queries = self.db_parser.get_queries_by_template(template_id)

        # Limit number of queries if needed
        if max_queries and len(queries) > max_queries:
            queries = random.sample(queries, max_queries)

        results = []
        for query in queries:
            result = self.run_experiment_on_query(query, sample_size, template_id)
            if result:
                results.append(result)

        # Store results by template
        self.results[f"template_{template_id}"] = results
        return results

    def run_experiment_on_query(self, query_item, sample_size=5, template_id=None):
        """Run experiment on a single query."""
        query_id = query_item.get("_id")
        print(f"Processing query {query_id}: {query_item.get('corrected_question')}")

        # Get actual results by running the original query
        original_query = query_item.get("sparql_query")
        try:
            actual_results = [
                result["uri"]["value"]
                for result in self.sparql.run_query(original_query)
                if "uri" in result
            ]
        except Exception as e:
            print(f"Error running original query: {e}")
            return None

        # Get seed entities
        seed_entities = self.db_parser.get_seed_entities(query_item, sample_size)
        print(seed_entities)

        if len(seed_entities) < 2:
            print(f"Not enough seed entities found in query {query_id}")
            return None

        # Run entity set expansion
        model = self.create_model()
        try:
            expanded_entities, generated_query = model.get_results(seed_entities)

            # Get paths for visualization if needed
            paths = None
            if self.visualize:
                paths = model.explorer.get_expansion_graph(seed_entities)
        except Exception as e:
            print(f"Error in entity set expansion: {e}")
            return None

        # Calculate metrics
        precision = EvaluationMetrics.get_precision(
            actual_results, expanded_entities, seed_entities
        )
        recall = EvaluationMetrics.get_recall(
            actual_results, expanded_entities, seed_entities
        )
        f1 = EvaluationMetrics.get_f1_score(
            actual_results, expanded_entities, seed_entities
        )

        # Generate visualizations if enabled
        viz_paths = None
        viz_entities = None
        if self.visualize and template_id is not None:
            if paths:
                viz_paths = self.viz_manager.save_path_visualization(
                    paths, query_id, template_id
                )
            viz_entities = self.viz_manager.save_expanded_entities_graph(
                seed_entities, expanded_entities, query_id, template_id
            )

        # Format and return result
        result = {
            "query_id": query_id,
            "question": query_item.get("corrected_question"),
            "original_query": original_query,
            "seed_entities": seed_entities,
            "actual_entities": actual_results,
            "expanded_entities": expanded_entities,
            "generated_query": generated_query,
            "metrics": {"precision": precision, "recall": recall, "f1": f1},
            "visualizations": (
                {"paths": viz_paths, "entities": viz_entities} if self.visualize else {}
            ),
        }

        print(f"Results for query {query_id}:")
        print(f"  Precision: {precision:.2f}")
        print(f"  Recall: {recall:.2f}")
        print(f"  F1: {f1:.2f}")

        return result

    def run_experiments(self, template_ids, sample_size=5, max_queries_per_template=5):
        """Run experiments on multiple template IDs."""
        all_results = {}
        metrics_by_template = {}

        for template_id in template_ids:
            print(f"\n=== Running experiments for template {template_id} ===")
            template_results = self.run_experiment_by_template(
                template_id, sample_size, max_queries_per_template
            )

            # Calculate average metrics for this template
            if template_results:
                avg_precision = sum(
                    r["metrics"]["precision"] for r in template_results
                ) / len(template_results)
                avg_recall = sum(
                    r["metrics"]["recall"] for r in template_results
                ) / len(template_results)
                avg_f1 = sum(r["metrics"]["f1"] for r in template_results) / len(
                    template_results
                )

                metrics_by_template[f"template_{template_id}"] = {
                    "precision": avg_precision,
                    "recall": avg_recall,
                    "f1": avg_f1,
                    "count": len(template_results),
                }

                print(f"\nTemplate {template_id} average metrics:")
                print(f"  Precision: {avg_precision:.2f}")
                print(f"  Recall: {avg_recall:.2f}")
                print(f"  F1: {avg_f1:.2f}")

            all_results[f"template_{template_id}"] = template_results

        # Create summary visualization if enabled
        if self.visualize:
            summary_viz = self.viz_manager.save_summary_visualization(
                metrics_by_template
            )
            if summary_viz:
                print(f"Summary visualization saved to: {summary_viz}")

        self.results = all_results
        return all_results

    def save_results(self, filename="results.json"):
        """Save experiment results to a JSON file."""
        output_path = (
            self.viz_manager.get_results_path(filename) if self.visualize else filename
        )
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
        print(f"Results saved to {output_path}")
        return output_path

    def calculate_overall_metrics(self):
        """Calculate overall metrics across all experiments."""
        total_precision = 0
        total_recall = 0
        total_f1 = 0
        count = 0

        for template, results in self.results.items():
            for result in results:
                metrics = result.get("metrics", {})
                total_precision += metrics.get("precision", 0)
                total_recall += metrics.get("recall", 0)
                total_f1 += metrics.get("f1", 0)
                count += 1

        if count == 0:
            return {"precision": 0, "recall": 0, "f1": 0, "count": 0}

        return {
            "precision": total_precision / count,
            "recall": total_recall / count,
            "f1": total_f1 / count,
            "count": count,
        }
