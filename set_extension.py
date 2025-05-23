from graph_explorer import GraphExplorer
from path_processor import PathProcessor
from query_generator import QueryGenerator

class CompositeGraphBasedSetExtension:
    def __init__(self, sparql, path_length=4, right_extensions=0, accept_not_full_path=False, 
                filter = "\"(.*sameAs|.*wiki.*|.*seeAlso|.*wordnet_type|.*subdivision|.*subject|.*w3.*type|.*depiction|.*isPrimaryTopicOf|.*wasDerivedFrom|.*property.*|.*homepage|.*thumbnail|.*hypernym|.*exactMatch)\"", 
                min_or_num=3, max_or_num=5):
        self.sparql = sparql
        self.explorer = GraphExplorer(sparql, filter, path_length, right_extensions, max_or_num)
        self.processor = PathProcessor(min_or_num, max_or_num)
        self.generator = QueryGenerator(min_or_num, max_or_num)
        self.accept_not_full_path = accept_not_full_path

    def get_results(self, entities):
        # Step 1: Find semantic paths in the knowledge graph
        paths = self.explorer.get_expansion_graph(entities)
        if len(paths) == 0:
            return [], ""
            
        # Step 2: Process and normalize the paths
        sorted_paths = self.explorer.sort_paths(paths)
        variable_path = self.processor.get_variable_paths(paths, entities)
        prefixes = self.processor.get_optimal_prefixes_from_path(variable_path)
        transformed_path = self.processor.transform_path_with_prefixes(variable_path, prefixes)
        
        # Step 3: Generate SPARQL query
        value_paths, values = self.generator.get_values_from_paths(transformed_path)
        entity_paths = self.generator.get_entity_paths(value_paths)
        QUERY = self.generator.create_query_from_paths(entity_paths, prefixes, values)
        
        # Step 4: Execute query if not too large
        if len(QUERY) > 7000:
            print("Query too long (>7000 chars)")
            return [], QUERY
            
        results = self.sparql.run_query(QUERY)
        results = [result['e']['value'] for result in results]
        return results, QUERY
