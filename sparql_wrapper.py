from SPARQLWrapper import SPARQLWrapper, JSON


class SPARQLWrapperCache:
    def __init__(self, endpoint, default_graph, timeout=30):
        self.endpoint = endpoint
        self.default_graph = default_graph
        self.timeout = timeout
        self.QUERY_RESULTS = {}

    def run_query_with_limits(self, QUERY, limit, offset):
        sparql = SPARQLWrapper(self.endpoint)
        sparql.addDefaultGraph(self.default_graph)
        sparql.setTimeout(self.timeout)
        sparql.setQuery(f"{QUERY}\nLIMIT {limit}\nOFFSET {offset}")
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()

    def run_query(self, QUERY):
        if QUERY in self.QUERY_RESULTS:
            return self.QUERY_RESULTS[QUERY]
        results = []
        limit = 10000
        offset = 0
        while True:
            try:
                result_page = self.run_query_with_limits(QUERY, limit, offset)
            except Exception as e:
                print(f"SPARQL query failed: {e}")
                print(f"Query: {QUERY}")
                return []

            current_bindings = result_page["results"]["bindings"]
            results.extend(current_bindings)

            if len(current_bindings) < limit:
                break
            offset += limit
            if not current_bindings and offset > 0:
                break
        self.QUERY_RESULTS[QUERY] = results
        return results
