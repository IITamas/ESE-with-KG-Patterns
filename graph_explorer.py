class GraphExplorer:
    def __init__(self, sparql_wrapper, filter_pattern, path_length=4, right_extensions=0, max_entities=5):
        self.sparql = sparql_wrapper
        self.path_length = path_length
        self.right_extensions = right_extensions
        self.filter = filter_pattern
        self.max_entities = max_entities

    def get_left_resolved_neighbours_from_entities(self, entities):
        """Find all entities that are connected to all input entities via the same outgoing edge"""
        QUERY = """SELECT DISTINCT ?entity1 ?edge
                WHERE {
                    VALUES ?entity {"""+" ".join([entity if "http" not in entity else "<"+entity+">" for entity in entities])+"""}
                    ?entity ?edge ?entity1
                    FILTER (isURI(?entity1)&&
                            !regex(str(?edge),"""+self.filter+"""))
                }
                GROUP BY ?edge ?entity1
                HAVING (COUNT(?entity)>"""+str(len(entities)-1)+""")"""
        try:
            results = self.sparql.run_query(QUERY)
        except:
            return []
        return [(result['edge']['value'],result['entity1']['value']) for result in results]

    def get_left_expandable_neighbours_from_entities(self, entities, resolved_edges):
        """Find all entities that can be reached from input entities via edges not in resolved_edges"""
        if not resolved_edges:
            resolved_edges = ["http://example.org/dummy"]
        
        QUERY = """SELECT DISTINCT ?entity1 ?edge ?entity2
                WHERE
                {
                    VALUES ?entity1 {"""+" ".join([entity if "http" not in entity else "<"+entity+">" for entity in entities])+"""}
                    {?entity1 ?edge ?entity2}
                    .
                    {
                        SELECT DISTINCT ?edge
                        WHERE
                        {
                            SELECT DISTINCT ?entity13 ?edge
                            WHERE {
                                VALUES ?entity13 {"""+" ".join([entity if "http" not in entity else "<"+entity+">" for entity in entities])+"""}
                                ?entity13 ?edge ?entity23
                                FILTER (isURI(?entity23))
                            }
                            GROUP BY ?edge ?entity13
                        }
                        GROUP BY ?edge
                        HAVING (COUNT(?entity13)>"""+str(len(entities)-1)+""")
                    }
                    FILTER (?edge NOT IN (
                        """+",".join(["<"+edge+">" for edge in resolved_edges])+"""))
                    FILTER (isURI(?entity2)&&
                            !regex(str(?edge),"""+self.filter+"""))
                }
                """
        try:
            results = self.sparql.run_query(QUERY)
        except:
            return []
        return [(result['entity1']['value'], result['edge']['value'],result['entity2']['value']) for result in results]

    def get_left_neighbours_of_entities(self, entities):
        """Get both resolved and expandable neighbors in the outgoing direction"""
        try:
            resolved_entities = self.get_left_resolved_neighbours_from_entities(entities)
        except:
            resolved_entities = []
        resolved_edges = {edge for edge, _ in resolved_entities}
        try:
            expandable_entities = self.get_left_expandable_neighbours_from_entities(entities, resolved_edges)
        except:
            expandable_entities = []
        resolved_entities_listed = []
        for edge in resolved_edges:
            resolved_entities_listed.append((entities, edge, [entity for e, entity in resolved_entities if edge == e]))
        return resolved_entities_listed, expandable_entities

    def get_right_resolved_neighbours_from_entities(self, entities):
        """Find all entities that connect to all input entities via the same incoming edge"""
        QUERY = """SELECT DISTINCT ?entity1 ?edge
                WHERE {
                    VALUES ?entity {"""+" ".join([entity if "http" not in entity else "<"+entity+">" for entity in entities])+"""}
                    ?entity1 ?edge ?entity
                    FILTER (isURI(?entity1)&&
                           !regex(str(?edge),"""+self.filter+"""))
                }
                GROUP BY ?edge ?entity1
                HAVING (COUNT(?entity)>"""+str(len(entities)-1)+")"
        try:
            results = self.sparql.run_query(QUERY)
        except:
            return []
        return [(result['edge']['value'],result['entity1']['value']) for result in results]

    def get_right_neighbours_of_entities(self, entities):
        """Get resolved neighbors in the incoming direction"""
        try:
            resolved_entities = self.get_right_resolved_neighbours_from_entities(entities)
        except:
            resolved_entities = []
        resolved_edges = {edge for edge, _ in resolved_entities}
        resolved_entities_listed = []
        for edge in resolved_edges:
            resolved_entities_listed.append(([entity for e, entity in resolved_entities if edge == e], edge, entities))
        return resolved_entities_listed

    def get_expansion_graph(self, start_entities):
        """Explore the graph to find semantic paths between entities"""
        paths = []
        stack = [(start_entities, [], 0)]
        while len(stack)!=0:
            entities, path, path_length = stack.pop(0)

            if path_length == self.path_length:
                continue

            all_entities_in_path = [entity for entities,_,_ in path for entity in entities]

            # Handle incoming edges if within right_extensions limit
            if path_length < self.right_extensions:
                resolved_entities = self.get_right_neighbours_of_entities(entities)
                for edge in resolved_entities:
                    is_valid = True
                    for entity in edge[0]:
                        if entity in all_entities_in_path:
                            is_valid = False
                            continue
                    if is_valid and len(edge[0]) < self.max_entities:
                        paths.append(path+[edge])

            # Handle outgoing edges
            resolved_entities, expandable_entities = self.get_left_neighbours_of_entities(entities)
            for edge in resolved_entities:
                is_valid = True
                for entity in edge[2]:
                    if entity in all_entities_in_path:
                        is_valid = False
                        continue
                if is_valid and len(edge[2]) < self.max_entities:
                    paths.append(path+[edge])

            # Explore expandable edges
            for edge in {edge for _, edge, _ in expandable_entities}:
                is_valid = True
                expandable_entity_list = list({entity2 for _, e, entity2 in expandable_entities if e == edge})
                for entity in expandable_entity_list:
                    if entity in all_entities_in_path:
                        is_valid = False
                        continue
                if is_valid:
                    stack.append((expandable_entity_list, path+[(entities, edge, expandable_entity_list)], path_length+1))
        return paths

    def sort_edge(self, triplet):
        """Sort entities in an edge for consistent representation"""
        return (sorted(triplet[0]), triplet[1], sorted(triplet[2]))

    def sort_path(self, path):
        """Sort all edges in a path"""
        return [self.sort_edge(triplet) for triplet in path]

    def sort_paths(self, paths):
        """Sort all paths"""
        return [self.sort_path(path) for path in paths]
