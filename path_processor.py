import ast


class PathProcessor:
    def __init__(self, min_entities_for_values_clause=3, max_entities_in_path_node=5):
        self.min_entities_for_values_clause = min_entities_for_values_clause
        self.max_entities_in_path_node = max_entities_in_path_node

    def get_variable_for_entity_group(self, entity_group_str, entity_to_variable_map):
        if entity_group_str not in entity_to_variable_map:
            entity_to_variable_map[entity_group_str] = "?e" + str(
                len(entity_to_variable_map)
            )
        return entity_to_variable_map[entity_group_str]

    def get_variable_path_representation(
        self, path_segments, entity_to_variable_map, start_entities_str_repr
    ):
        variable_path = []
        if start_entities_str_repr not in entity_to_variable_map:
            entity_to_variable_map[start_entities_str_repr] = "?e"

        for source_nodes, edge_uri, target_nodes in path_segments:
            source_nodes_str = str(sorted(list(source_nodes)))
            target_nodes_str = str(sorted(list(target_nodes)))

            var_source = self.get_variable_for_entity_group(
                source_nodes_str, entity_to_variable_map
            )
            var_target = self.get_variable_for_entity_group(
                target_nodes_str, entity_to_variable_map
            )
            variable_path.append(
                ((source_nodes, var_source), edge_uri, (target_nodes, var_target))
            )
        return variable_path

    def get_all_variable_paths(self, all_paths, start_entities):
        entity_to_variable_map = {}
        start_entities_str_repr = str(sorted(list(start_entities)))
        entity_to_variable_map[start_entities_str_repr] = "?e"

        all_variable_paths_repr = []
        for path_segments in all_paths:
            all_variable_paths_repr.append(
                self.get_variable_path_representation(
                    path_segments, entity_to_variable_map, start_entities_str_repr
                )
            )
        return all_variable_paths_repr, entity_to_variable_map

    def get_optimal_prefix_from_number(self, number):
        res = chr(ord("a") + number % 26)
        number = number // 26
        while number != 0:
            res = chr(ord("a") + number % 26) + res
            number = number // 26
        return res + ":"

    def get_uri_namespace_prefix(self, url):
        if "http" not in str(url):
            return ""
        parts = str(url).split("/")
        if len(parts) < 2:
            return ""

        last_part = parts[-1]
        if "#" in last_part:
            return "/".join(parts[:-1]) + "/" + last_part.split("#")[0] + "#"
        else:
            if last_part:
                return "/".join(parts[:-1]) + "/"
            return str(url)

    def get_optimal_prefixes_for_all_paths(self, all_variable_paths):
        defined_prefixes = {"": ""}
        for var_path in all_variable_paths:
            for (
                (original_source_nodes, _),
                edge_uri,
                (original_target_nodes, _),
            ) in var_path:
                uris_to_prefix = [edge_uri]
                uris_to_prefix.extend(original_source_nodes)
                uris_to_prefix.extend(original_target_nodes)

                for uri in uris_to_prefix:
                    namespace = self.get_uri_namespace_prefix(uri)
                    if namespace and namespace not in defined_prefixes:
                        defined_prefixes[namespace] = (
                            self.get_optimal_prefix_from_number(
                                len(defined_prefixes) - 1
                            )
                        )
        return defined_prefixes

    # def get_prefixed_uri_or_variable(self, item, defined_prefixes):
    #     if isinstance(item, str) and item.startswith("?"):
    #         return item

    #     uri = str(item)
    #     namespace = self.get_uri_namespace_prefix(uri)
    #     if namespace and namespace in defined_prefixes and defined_prefixes[namespace]:
    #         local_name = uri.replace(namespace, "")
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
    #     return "<" + uri + ">"

    def get_prefixed_uri_or_variable(self, item, defined_prefixes):
        if isinstance(item, str) and item.startswith("?"):
            return item
        # Use angle brackets for all URIs to avoid SPARQL syntax issues
        return "<" + str(item) + ">"

    def transform_variable_paths_with_prefixes(
        self, all_variable_paths, defined_prefixes
    ):
        transformed_paths_for_query = []
        for var_path in all_variable_paths:
            current_transformed_path = []
            for (
                (original_source_nodes, var_source),
                edge_uri,
                (original_target_nodes, var_target),
            ) in var_path:
                prefixed_edge = self.get_prefixed_uri_or_variable(
                    edge_uri, defined_prefixes
                )
                current_transformed_path.append(
                    (
                        (original_source_nodes, var_source),
                        prefixed_edge,
                        (original_target_nodes, var_target),
                    )
                )
            transformed_paths_for_query.append(current_transformed_path)
        return transformed_paths_for_query
