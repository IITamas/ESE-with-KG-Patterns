import ast


class QueryGenerator:
    def __init__(self, min_entities_for_values_clause=3, max_entities_in_path_node=5):
        self.min_entities_for_values_clause = min_entities_for_values_clause
        self.max_entities_in_path_node = max_entities_in_path_node

    def _format_node_for_query(
        self, original_nodes_list, node_variable, defined_prefixes, values_clause_map
    ):
        if (
            len(original_nodes_list) >= self.min_entities_for_values_clause
            and len(original_nodes_list) <= self.max_entities_in_path_node
        ):
            sorted_uris_str_key = str(sorted(list(original_nodes_list)))
            if sorted_uris_str_key not in values_clause_map:
                values_clause_map[sorted_uris_str_key] = (
                    node_variable,
                    [
                        self._get_prefixed_uri_for_values(uri, defined_prefixes)
                        for uri in original_nodes_list
                    ],
                )
            return node_variable
        elif len(original_nodes_list) == 1:
            return self._get_prefixed_uri_for_values(
                original_nodes_list[0], defined_prefixes
            )
        return node_variable

    def _get_prefixed_uri_for_values(self, uri, defined_prefixes):
        return "<" + str(uri) + ">"

    # def _get_prefixed_uri_for_values(self, uri, defined_prefixes):
    #     namespace = "/".join(str(uri).split("/")[:-1]) + (
    #         "/" + str(uri).split("/")[-1].split("#")[0] + "#"
    #         if "#" in str(uri).split("/")[-1]
    #         else "/"
    #     )
    #     if namespace in defined_prefixes and defined_prefixes[namespace]:
    #         local_name = str(uri).replace(namespace, "")
    #         # Add check for ANY special characters that would cause SPARQL syntax issues
    #         if (
    #             local_name
    #             and not local_name[0] in ".-0123456789"
    #             and not any(
    #                 c in local_name
    #                 for c in [
    #                     "(",
    #                     "+",
    #                     ")",
    #                     ",",
    #                     "'",
    #                     " ",
    #                     "/",
    #                     "&",
    #                     "=",
    #                     "?",
    #                     "#",
    #                     "%",
    #                     "$",
    #                     "@",
    #                 ]
    #             )
    #         ):
    #             return defined_prefixes[namespace] + local_name
    #     return "<" + str(uri) + ">"

    def get_query_triplets_and_values(
        self, transformed_paths_for_query, defined_prefixes
    ):
        query_triplets_map = {}
        values_clause_map = {}

        for var_path in transformed_paths_for_query:
            for (
                (original_source_nodes, var_source),
                prefixed_edge,
                (original_target_nodes, var_target),
            ) in var_path:
                formatted_source = self._format_node_for_query(
                    original_source_nodes,
                    var_source,
                    defined_prefixes,
                    values_clause_map,
                )
                formatted_target = self._format_node_for_query(
                    original_target_nodes,
                    var_target,
                    defined_prefixes,
                    values_clause_map,
                )

                if formatted_source not in query_triplets_map:
                    query_triplets_map[formatted_source] = []
                if (prefixed_edge, formatted_target) not in query_triplets_map[
                    formatted_source
                ]:
                    query_triplets_map[formatted_source].append(
                        (prefixed_edge, formatted_target)
                    )
        return query_triplets_map, values_clause_map

    def create_query_from_processed_paths(
        self, query_triplets_map, defined_prefixes, values_clause_map
    ):
        prefix_declarations = "\n".join(
            [
                f"PREFIX {defined_prefixes[ns]} <{ns}>"
                for ns in defined_prefixes
                if ns and defined_prefixes[ns]
            ]
        )
        query_string = f"{prefix_declarations}\nSELECT DISTINCT ?e\nWHERE {{\n"

        # Skip the VALUES clause for ?e (seed entities)
        for key, (var_for_pattern, uri_list_for_values) in values_clause_map.items():
            if var_for_pattern != "?e":  # Skip the seed entities
                query_string += f"  VALUES {var_for_pattern} {{ {' '.join(uri_list_for_values)} }}\n"

        for subject_var, po_pairs in query_triplets_map.items():
            if not po_pairs:
                continue
            patterns_str = " ;\n    ".join([f"{pred} {obj}" for pred, obj in po_pairs])
            query_string += f"  {subject_var} {patterns_str} .\n"

        query_string += "  FILTER (isURI(?e))\n}"
        return query_string
