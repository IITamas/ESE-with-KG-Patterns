import json
import re
import random


class DatabaseParser:
    def __init__(self, database_path=None, sparql_wrapper=None):
        self.data = []
        self.sparql_wrapper = sparql_wrapper
        if database_path:
            self.load_database(database_path)

    def load_database(self, database_path):
        try:
            with open(database_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Database file not found at {database_path}")
            self.data = []
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {database_path}")
            self.data = []
        return self.data

    def _extract_uris_from_query_string(self, query):
        resource_pattern = r"<http://dbpedia\.org/resource/[^>]+>"
        entities_with_brackets = re.findall(resource_pattern, query)
        entities = [
            uri.replace("<", "").replace(">", "") for uri in entities_with_brackets
        ]
        return list(set(entities))

    def _fetch_entities_by_executing_query(self, sparql_query):
        if not self.sparql_wrapper:
            print(
                "Warning: SPARQL wrapper not provided to DatabaseParser. Cannot execute query to fetch seed entities."
            )
            return []
        if not sparql_query:
            return []

        print(f"Executing query to fetch seed entities: {sparql_query[:200]}...")
        fetched_entities = []
        try:
            query_results_bindings = self.sparql_wrapper.run_query(sparql_query)

            if query_results_bindings:
                first_result = query_results_bindings[0]
                for var_name in first_result.keys():
                    is_dbpedia_resource_var = all(
                        binding[var_name]["type"] == "uri"
                        and "http://dbpedia.org/resource/" in binding[var_name]["value"]
                        for binding in query_results_bindings
                        if var_name in binding and binding[var_name]
                    )
                    if is_dbpedia_resource_var:
                        for binding in query_results_bindings:
                            if (
                                var_name in binding
                                and binding[var_name]
                                and binding[var_name]["type"] == "uri"
                            ):
                                fetched_entities.append(binding[var_name]["value"])
                        break
                if not fetched_entities:
                    for binding in query_results_bindings:
                        for var_name in binding.keys():
                            if binding[var_name]["type"] == "uri":
                                fetched_entities.append(binding[var_name]["value"])
                                break
            return list(set(fetched_entities))
        except Exception as e:
            print(f"Error executing SPARQL query for seed entities: {e}")
            return []

    def get_query_by_id(self, query_id):
        for item in self.data:
            if item.get("_id") == str(query_id):
                return item
        return None

    def get_queries_by_template(self, template_id):
        return [
            item for item in self.data if item.get("sparql_template_id") == template_id
        ]

    def get_seed_entities(self, query_item, sample_size=5):
        current_entities = []
        if (
            "query_results_for_seeds" in query_item
            and query_item["query_results_for_seeds"]
        ):
            current_entities = list(set(query_item["query_results_for_seeds"]))

        sparql_query_str = query_item.get("sparql_query", "")
        entities_from_string = self._extract_uris_from_query_string(sparql_query_str)
        current_entities.extend(entities_from_string)
        current_entities = list(set(current_entities))

        if (
            len(current_entities) < sample_size
            and self.sparql_wrapper
            and sparql_query_str
        ):
            print(
                f"Query {query_item.get('_id')}: Not enough entities from string/predefined ({len(current_entities)}), trying to execute query."
            )
            entities_from_execution = self._fetch_entities_by_executing_query(
                sparql_query_str
            )
            current_entities.extend(entities_from_execution)
            current_entities = list(set(current_entities))

        if not current_entities:
            print(
                f"Warning: No seed entities could be obtained for query {query_item.get('_id')}"
            )
            return []

        if len(current_entities) > sample_size:
            return random.sample(current_entities, sample_size)
        return current_entities
