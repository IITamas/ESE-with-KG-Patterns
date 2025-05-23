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
        sparql.addExtraURITag("timeout", str(self.timeout*1000))
        sparql.setQuery(QUERY + "\nLIMIT "+str(limit)+"\nOFFSET "+str(offset))
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()

    def run_query(self, QUERY):
        if QUERY in self.QUERY_RESULTS:
            return self.QUERY_RESULTS[QUERY]
        results = []
        limit = 10000
        offset = 0
        while len(results)%10000!=0 or len(results)==0:
            try:
                result = self.run_query_with_limits(QUERY, limit, offset)
            except:
                raise Exception("Query execution failed")
            results = results + result["results"]["bindings"]
            offset += limit
            if (len(result["results"]["bindings"])==0):
                break
        self.QUERY_RESULTS[QUERY] = results
        return results
