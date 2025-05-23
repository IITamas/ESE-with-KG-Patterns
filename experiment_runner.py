import json
import random
from db_parser import DatabaseParser
from sparql_wrapper import SPARQLWrapperCache
from set_extension import CompositeGraphBasedSetExtension
from evaluation import EvaluationMetrics
from visualization_manager import VisualizationManager
from config import DEFAULT_SPARQL_ENDPOINT, DEFAULT_GRAPH, DEFAULT_TIMEOUT


class ExperimentRunner:
    def __init__(
        self,
        database_path,
        sparql_endpoint=DEFAULT_SPARQL_ENDPOINT,
        default_graph=DEFAULT_GRAPH,
        timeout=DEFAULT_TIMEOUT,
        output_dir="output",
        visualize=False,
    ):

        self.sparql_wrapper = SPARQLWrapperCache(
            sparql_endpoint, default_graph, timeout
        )
        self.db_parser = DatabaseParser(
            database_path, sparql_wrapper=self.sparql_wrapper
        )
        self.filter_pattern = '"(.*sameAs|.*wiki.*|.*seeAlso|.*wordnet_type|.*subdivision|.*subject|.*depiction|.*isPrimaryTopicOf|.*wasDerivedFrom|.*property.*|.*homepage|.*thumbnail|.*hypernym|.*exactMatch)"'
        self.results_by_template = {}
        self.visualize = visualize
        self.viz_manager = VisualizationManager(output_dir) if visualize else None

    def create_model(
        self,
        path_length=3,
        right_extensions=1,
        min_entities_for_values_clause=2,
        max_entities_in_path_node=5,
    ):
        return CompositeGraphBasedSetExtension(
            self.sparql_wrapper,
            path_length=path_length,
            right_extensions=right_extensions,
            filter_pattern=self.filter_pattern,
            min_entities_for_values_clause=min_entities_for_values_clause,
            max_entities_in_path_node=max_entities_in_path_node,
        )

    def run_experiment_on_query(
        self, query_item, sample_size=5, template_id_for_viz=None
    ):
        query_id = query_item.get("_id", "unknown_id")
        print(
            f"Processing query {query_id}: {query_item.get('corrected_question', 'N/A')[:100]}..."
        )

        original_sparql_query = query_item.get("sparql_query")
        actual_entities_ground_truth = []

        if "query_results" in query_item and isinstance(
            query_item["query_results"], list
        ):
            actual_entities_ground_truth = query_item["query_results"]
        elif original_sparql_query:
            print(
                f"  Query {query_id}: No pre-defined results, executing original query to get 'actual' entities."
            )
            try:
                bindings = self.sparql_wrapper.run_query(original_sparql_query)
                for binding in bindings:
                    for var_name in binding:
                        if (
                            binding[var_name]["type"] == "uri"
                            and "http://dbpedia.org/resource/"
                            in binding[var_name]["value"]
                        ):
                            actual_entities_ground_truth.append(
                                binding[var_name]["value"]
                            )
                            break
                actual_entities_ground_truth = list(set(actual_entities_ground_truth))
            except Exception as e:
                print(f"  Error running original query for {query_id}: {e}")

        seed_entities = self.db_parser.get_seed_entities(query_item, sample_size)
        print(seed_entities)

        if len(seed_entities) < 1:
            print(
                f"  Query {query_id}: Not enough seed entities ({len(seed_entities)}). Skipping."
            )
            return None

        model = self.create_model()
        expanded_entities = []
        generated_query_str = ""
        paths_for_viz = []

        try:
            expanded_entities, generated_query_str, paths_for_viz = model.get_results(
                seed_entities
            )
        except Exception as e:
            print(f"  Error in entity set expansion for query {query_id}: {e}")

        precision = EvaluationMetrics.get_precision(
            actual_entities_ground_truth, expanded_entities, seed_entities
        )
        recall = EvaluationMetrics.get_recall(
            actual_entities_ground_truth, expanded_entities, seed_entities
        )
        f1 = EvaluationMetrics.get_f1_score(
            actual_entities_ground_truth, expanded_entities, seed_entities
        )

        viz_paths_file = None
        viz_entities_file = None
        if self.visualize and self.viz_manager and template_id_for_viz is not None:
            if paths_for_viz:
                viz_paths_file = self.viz_manager.save_path_visualization(
                    paths_for_viz, query_id, str(template_id_for_viz)
                )
            viz_entities_file = self.viz_manager.save_expanded_entities_graph(
                seed_entities, expanded_entities, query_id, str(template_id_for_viz)
            )

        result_summary = {
            "query_id": query_id,
            "question": query_item.get("corrected_question"),
            "original_sparql_query": original_sparql_query,
            "seed_entities": seed_entities,
            "actual_entities_ground_truth": actual_entities_ground_truth,
            "expanded_entities": expanded_entities,
            "generated_query": generated_query_str,
            "metrics": {"precision": precision, "recall": recall, "f1": f1},
            "visualizations": (
                {"paths": viz_paths_file, "entities": viz_entities_file}
                if self.visualize
                else {}
            ),
        }
        print(
            f"  Query {query_id} Metrics: P={precision:.2f}, R={recall:.2f}, F1={f1:.2f}"
        )
        return result_summary

    def run_experiments_by_template(
        self, template_id, sample_size=5, max_queries_per_template=10
    ):
        queries_for_template = self.db_parser.get_queries_by_template(template_id)
        if not queries_for_template:
            print(f"No queries found for template ID: {template_id}")
            return []

        selected_queries = queries_for_template
        if (
            max_queries_per_template
            and len(queries_for_template) > max_queries_per_template
        ):
            selected_queries = random.sample(
                queries_for_template, max_queries_per_template
            )
            print(
                f"Selected {len(selected_queries)} random queries for template {template_id}."
            )
        else:
            print(
                f"Using all {len(selected_queries)} queries for template {template_id}."
            )

        template_run_results = []
        for query_item in selected_queries:
            single_query_result = self.run_experiment_on_query(
                query_item, sample_size, template_id_for_viz=template_id
            )
            if single_query_result:
                template_run_results.append(single_query_result)

        self.results_by_template[str(template_id)] = template_run_results
        return template_run_results

    def run_all_experiments(
        self, template_ids_list, sample_size=5, max_queries_per_template=5
    ):
        metrics_summary_for_viz = {}
        for tid in template_ids_list:
            print(f"\n===== Running experiments for Template ID: {tid} =====")
            template_results = self.run_experiments_by_template(
                tid, sample_size, max_queries_per_template
            )
            if template_results:
                avg_p = sum(r["metrics"]["precision"] for r in template_results) / len(
                    template_results
                )
                avg_r = sum(r["metrics"]["recall"] for r in template_results) / len(
                    template_results
                )
                avg_f1 = sum(r["metrics"]["f1"] for r in template_results) / len(
                    template_results
                )
                metrics_summary_for_viz[f"template_{tid}"] = {
                    "precision": avg_p,
                    "recall": avg_r,
                    "f1": avg_f1,
                    "count": len(template_results),
                }
                print(
                    f"Template {tid} Average: P={avg_p:.2f}, R={avg_r:.2f}, F1={avg_f1:.2f} (from {len(template_results)} queries)"
                )

        if self.visualize and self.viz_manager and metrics_summary_for_viz:
            summary_viz_path = self.viz_manager.save_summary_visualization(
                metrics_summary_for_viz
            )
            if summary_viz_path:
                print(
                    f"Overall performance summary visualization saved to: {summary_viz_path}"
                )
        return self.results_by_template

    def save_results(self, filename="experiment_results.json"):
        output_path = filename
        if self.visualize and self.viz_manager:
            output_path = self.viz_manager.get_results_path(filename)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self.results_by_template, f, indent=2)
            print(f"Experiment results saved to {output_path}")
        except Exception as e:
            print(f"Error saving results to {output_path}: {e}")
        return str(output_path)

    def calculate_overall_metrics_across_all_templates(self):
        all_precisions = []
        all_recalls = []
        all_f1s = []
        total_queries = 0

        for template_id, results_list in self.results_by_template.items():
            for result in results_list:
                metrics = result.get("metrics", {})
                all_precisions.append(metrics.get("precision", 0))
                all_recalls.append(metrics.get("recall", 0))
                all_f1s.append(metrics.get("f1", 0))
                total_queries += 1

        if total_queries == 0:
            return {"precision": 0, "recall": 0, "f1": 0, "count": 0}

        avg_precision = sum(all_precisions) / total_queries if all_precisions else 0
        avg_recall = sum(all_recalls) / total_queries if all_recalls else 0
        avg_f1 = sum(all_f1s) / total_queries if all_f1s else 0

        return {
            "precision": avg_precision,
            "recall": avg_recall,
            "f1": avg_f1,
            "count": total_queries,
        }
