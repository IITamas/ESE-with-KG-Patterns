from graph_explorer import GraphExplorer
from path_processor import PathProcessor
from query_generator import QueryGenerator
from config import (
    DEFAULT_FILTER_PATTERN,
    DEFAULT_PATH_LENGTH,
    DEFAULT_RIGHT_EXTENSIONS,
    DEFAULT_MIN_OR_NUM,
    DEFAULT_MAX_OR_NUM,
)


class CompositeGraphBasedSetExtension:
    def __init__(
        self,
        sparql_wrapper,
        path_length=DEFAULT_PATH_LENGTH,
        right_extensions=DEFAULT_RIGHT_EXTENSIONS,
        filter_pattern=DEFAULT_FILTER_PATTERN,
        min_entities_for_values_clause=DEFAULT_MIN_OR_NUM,
        max_entities_in_path_node=DEFAULT_MAX_OR_NUM,
    ):

        self.sparql = sparql_wrapper
        self.explorer = GraphExplorer(
            sparql_wrapper,
            filter_pattern,
            path_length,
            right_extensions,
            max_entities_in_path_node,
        )
        self.processor = PathProcessor(
            min_entities_for_values_clause, max_entities_in_path_node
        )
        self.generator = QueryGenerator(
            min_entities_for_values_clause, max_entities_in_path_node
        )

    def get_results(self, start_entities):
        if not start_entities or len(start_entities) < 1:
            print("Warning: At least one seed entity is required.")
            return [], "", []

        all_paths = self.explorer.get_expansion_graph(start_entities)

        if not all_paths:
            print("No expansion paths found.")
            return [], "", []

        all_variable_paths, entity_to_variable_map = (
            self.processor.get_all_variable_paths(all_paths, start_entities)
        )
        defined_prefixes = self.processor.get_optimal_prefixes_for_all_paths(
            all_variable_paths
        )
        transformed_paths_for_query = (
            self.processor.transform_variable_paths_with_prefixes(
                all_variable_paths, defined_prefixes
            )
        )
        query_triplets_map, values_clause_map = (
            self.generator.get_query_triplets_and_values(
                transformed_paths_for_query, defined_prefixes
            )
        )
        QUERY = self.generator.create_query_from_processed_paths(
            query_triplets_map, defined_prefixes, values_clause_map
        )

        if len(QUERY) > 7800:
            print(
                f"Warning: Generated query is too long ({len(QUERY)} chars). Skipping execution."
            )
            print(f"Query: {QUERY}")
            return [], QUERY, all_paths

        expanded_entities = []
        try:
            query_execution_results = self.sparql.run_query(QUERY)
            expanded_entities = [
                result["e"]["value"]
                for result in query_execution_results
                if "e" in result and result["e"]["type"] == "uri"
            ]
        except Exception as e:
            print(f"Error executing generated SPARQL query: {e}")
            print(f"Query: {QUERY}")

        return expanded_entities, QUERY, all_paths
