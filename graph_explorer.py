# graph_explorer.py
class GraphExplorer:
    def __init__(
        self,
        sparql_wrapper,
        filter_pattern,
        path_length=4,
        right_extensions=0,
        max_entities_in_path_node=5,
    ):
        self.sparql = sparql_wrapper
        self.path_length = path_length
        self.right_extensions = right_extensions
        # Store the raw filter pattern.
        # If the pattern itself could contain """ then it would need specific escaping for SPARQL.
        # For the current pattern, this is not an issue.
        self.filter_pattern_str = filter_pattern
        self.max_entities_in_path_node = max_entities_in_path_node

    def _build_regex_filter_sparql(self):
        # Escape backslashes and use single quotes which work better with SPARQL
        escaped_pattern = self.filter_pattern_str.replace("\\", "\\\\")
        return f"!regex(str(?edge), '{escaped_pattern}')"

    def get_left_resolved_neighbours_from_entities(self, entities):
        regex_filter = self._build_regex_filter_sparql()
        QUERY = f"""SELECT DISTINCT ?entity1 ?edge
                WHERE {{
                    VALUES ?entity {{ {" ".join([entity if "http" not in entity else "<"+entity+">" for entity in entities])} }}
                    ?entity ?edge ?entity1 .
                    FILTER (isURI(?entity1) && {regex_filter})
                }}
                GROUP BY ?edge ?entity1
                HAVING (COUNT(?entity) > {len(entities)-1})"""
        try:
            results = self.sparql.run_query(QUERY)
        except Exception as e:
            # print(f"Error in get_left_resolved_neighbours_from_entities: {e}\nQuery: {QUERY}")
            return []
        return [
            (result["edge"]["value"], result["entity1"]["value"]) for result in results
        ]

    def get_left_expandable_neighbours_from_entities(self, entities, resolved_edges):
        resolved_edges_filter_part = ""
        if resolved_edges:
            resolved_edges_filter_part = (
                "FILTER (?edge NOT IN ("
                + ",".join(["<" + edge + ">" for edge in resolved_edges])
                + "))"
            )

        regex_filter = self._build_regex_filter_sparql()

        QUERY = f"""SELECT DISTINCT ?entity1 ?edge ?entity2
                WHERE {{
                    VALUES ?entity1 {{ {" ".join([entity if "http" not in entity else "<"+entity+">" for entity in entities])} }}
                    {{?entity1 ?edge ?entity2}} .
                    {{
                        SELECT DISTINCT ?edge
                        WHERE {{
                            SELECT DISTINCT ?entity13 ?edge
                            WHERE {{
                                VALUES ?entity13 {{ {" ".join([entity if "http" not in entity else "<"+entity+">" for entity in entities])} }}
                                ?entity13 ?edge ?entity23 .
                                FILTER (isURI(?entity23))
                            }}
                            GROUP BY ?edge ?entity13
                        }}
                        GROUP BY ?edge
                        HAVING (COUNT(?entity13) > {len(entities)-1})
                    }}
                    {resolved_edges_filter_part}
                    FILTER (isURI(?entity2) && {regex_filter})
                }}
                """
        try:
            results = self.sparql.run_query(QUERY)
        except Exception as e:
            # print(f"Error in get_left_expandable_neighbours_from_entities: {e}\nQuery: {QUERY}")
            return []
        return [
            (
                result["entity1"]["value"],
                result["edge"]["value"],
                result["entity2"]["value"],
            )
            for result in results
        ]

    def get_right_resolved_neighbours_from_entities(self, entities):
        regex_filter = self._build_regex_filter_sparql()
        QUERY = f"""SELECT DISTINCT ?entity1 ?edge
                WHERE {{
                    VALUES ?entity {{ {" ".join([entity if "http" not in entity else "<"+entity+">" for entity in entities])} }}
                    ?entity1 ?edge ?entity .
                    FILTER (isURI(?entity1) && {regex_filter})
                }}
                GROUP BY ?edge ?entity1
                HAVING (COUNT(?entity) > {len(entities)-1})"""
        try:
            results = self.sparql.run_query(QUERY)
        except Exception as e:
            # print(f"Error in get_right_resolved_neighbours_from_entities: {e}\nQuery: {QUERY}")
            return []
        return [
            (result["edge"]["value"], result["entity1"]["value"]) for result in results
        ]

    # ... (The rest of GraphExplorer: get_left_neighbours_of_entities, get_right_neighbours_of_entities, get_expansion_graph, sort_... methods remain unchanged from the previous "cleaned comments" version)
    def get_left_neighbours_of_entities(self, entities):
        resolved_entities = self.get_left_resolved_neighbours_from_entities(entities)
        resolved_edges = {edge for edge, _ in resolved_entities}
        expandable_entities = self.get_left_expandable_neighbours_from_entities(
            entities, resolved_edges
        )
        resolved_entities_listed = []
        for edge_uri in resolved_edges:
            target_entities_for_edge = [
                entity for res_edge, entity in resolved_entities if res_edge == edge_uri
            ]
            if target_entities_for_edge:
                resolved_entities_listed.append(
                    (entities, edge_uri, target_entities_for_edge)
                )
        return resolved_entities_listed, expandable_entities

    def get_right_neighbours_of_entities(self, entities):
        resolved_entities = self.get_right_resolved_neighbours_from_entities(entities)
        resolved_edges = {edge for edge, _ in resolved_entities}
        resolved_entities_listed = []
        for edge_uri in resolved_edges:
            source_entities_for_edge = [
                entity for res_edge, entity in resolved_entities if res_edge == edge_uri
            ]
            if source_entities_for_edge:
                resolved_entities_listed.append(
                    (source_entities_for_edge, edge_uri, entities)
                )
        return resolved_entities_listed

    def get_expansion_graph(self, start_entities):
        found_paths = []
        stack = [(list(start_entities), [], 0)]

        while len(stack) != 0:
            current_entities, current_path_segments, path_length = stack.pop(0)

            if path_length >= self.path_length:
                continue

            all_entities_in_current_path = set()
            for seg_source_nodes, _, seg_target_nodes in current_path_segments:
                all_entities_in_current_path.update(seg_source_nodes)
                all_entities_in_current_path.update(seg_target_nodes)

            if path_length < self.right_extensions:
                resolved_right_segments = self.get_right_neighbours_of_entities(
                    current_entities
                )
                for source_nodes, edge_uri, target_nodes in resolved_right_segments:
                    if (
                        any(n in all_entities_in_current_path for n in source_nodes)
                        or len(source_nodes) >= self.max_entities_in_path_node
                    ):
                        continue
                    new_path_segment = (source_nodes, edge_uri, target_nodes)
                    found_paths.append(current_path_segments + [new_path_segment])

            resolved_left_segments, expandable_left_triplets = (
                self.get_left_neighbours_of_entities(current_entities)
            )

            for source_nodes, edge_uri, target_nodes in resolved_left_segments:
                if (
                    any(n in all_entities_in_current_path for n in target_nodes)
                    or len(target_nodes) >= self.max_entities_in_path_node
                ):
                    continue
                new_path_segment = (source_nodes, edge_uri, target_nodes)
                found_paths.append(current_path_segments + [new_path_segment])

            expandable_edges_map = {}
            for e1, edge, e2 in expandable_left_triplets:
                if edge not in expandable_edges_map:
                    expandable_edges_map[edge] = []
                if e2 not in expandable_edges_map[edge]:
                    expandable_edges_map[edge].append(e2)

            for edge_uri, target_nodes_list in expandable_edges_map.items():
                unique_target_nodes = list(set(target_nodes_list))
                if (
                    any(n in all_entities_in_current_path for n in unique_target_nodes)
                    or len(unique_target_nodes) == 0
                    or len(unique_target_nodes) >= self.max_entities_in_path_node
                ):
                    continue
                new_path_segment = (current_entities, edge_uri, unique_target_nodes)
                stack.append(
                    (
                        list(unique_target_nodes),
                        current_path_segments + [new_path_segment],
                        path_length + 1,
                    )
                )
        return found_paths

    def sort_edge_triplet(self, triplet):
        return (sorted(list(triplet[0])), triplet[1], sorted(list(triplet[2])))

    def sort_path_segments(self, path_segments):
        return [self.sort_edge_triplet(triplet) for triplet in path_segments]

    def sort_all_paths(self, all_paths):
        return [self.sort_path_segments(path_segments) for path_segments in all_paths]
