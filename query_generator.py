import ast

class QueryGenerator:
    def __init__(self, min_or_num=3, max_or_num=5):
        self.min_or_num = min_or_num
        self.max_or_num = max_or_num
        
    def get_values_from_path(self, entity1, edge, entity2, values):
        """Process path entities into SPARQL query path elements"""
        paths = []
        if type(entity1) is str:
            entity1 = [entity1]
        if type(entity2) is str:
            entity2 = [entity2]
        if type(entity1) is list and str(entity1) in values:
            entity1 = [values[str(entity1)]]
        if type(entity2) is list and str(entity2) in values:
            entity2 = [values[str(entity2)]]
        for e1 in entity1:
            for e2 in entity2:
                paths.append((e1, edge, e2))
        return paths

    def get_values_from_paths(self, paths):
        """Extract variable values from paths"""
        values = {}
        value_paths = []
        for path in paths:
            for entities1, edge, entities2 in path:
                if (type(entities1) is list and len(entities1)>self.max_or_num) or (type(entities2) is list and len(entities2)>self.max_or_num):
                    continue
                if type(entities1) is list and len(entities1)>self.min_or_num:
                    values[str(entities1)] = "?v"+str(len(values))
                if type(entities2) is list and len(entities2)>self.min_or_num:
                    values[str(entities2)] = "?v"+str(len(values))
                value_paths = value_paths + self.get_values_from_path(entities1, edge, entities2, values)
        return value_paths, values

    def get_entity_paths(self, paths):
        """Organize paths by source entity"""
        entity_paths = {}
        for e1, e, e2 in paths:
            if e1 not in entity_paths:
                entity_paths[e1] = []
            if [e, e2] not in entity_paths[e1]:
                entity_paths[e1] = entity_paths[e1] + [[e, e2]]
        return entity_paths

    def create_query_from_paths(self, entity_paths, prefixes, values):
        """Generate complete SPARQL query from paths"""
        QUERY = "\n".join(["prefix "+prefixes[prefix]+" <"+prefix+("/" if prefix[-1]!="#" else "")+">" for prefix in prefixes if prefix!=""])+"""\nSELECT DISTINCT ?e
WHERE {
"""
        for value in values:
            QUERY += "VALUES "+values[str(value)]+" {"+" ".join(ast.literal_eval(value))+"}\n"
        for edge in entity_paths:
            QUERY += ""+edge+(";\n"+(" "*len(edge))).join([" "+e[0]+" "+e[1] for e in entity_paths[edge]])+".\n"
        return QUERY+"FILTER (isURI(?e))\n}"
