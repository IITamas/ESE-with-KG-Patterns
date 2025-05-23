# config.py
DEFAULT_SPARQL_ENDPOINT = "http://dbpedia.org/sparql"
DEFAULT_GRAPH = "http://dbpedia.org"
DEFAULT_TIMEOUT = 180

# In config.py
DEFAULT_FILTER_PATTERN = (
    ".*sameAs|.*wikiPageWikiLink|.*wikiPageExternalLink|.*wikiPageRedirects|"
    ".*seeAlso|.*wordnet_type|.*subdivision|.*subject|"
    ".*w3.org/1999/02/22-rdf-syntax-ns#type|.*depiction|.*isPrimaryTopicOf|"
    ".*wasDerivedFrom|.*xmlns.com/foaf/0.1/page|.*xmlns.com/foaf/0.1/primaryTopic|"
    ".*property.*|.*homepage|.*thumbnail|.*hypernym|.*exactMatch|"
    "owl#differentFrom|dbpedia.org/ontology/abstract"
)

DEFAULT_PATH_LENGTH = 3
DEFAULT_RIGHT_EXTENSIONS = 1
DEFAULT_MIN_OR_NUM = 2
DEFAULT_MAX_OR_NUM = 5

DEFAULT_OUTPUT_DIR = "output"
DEFAULT_SAMPLE_SIZE_SEEDS = 5
DEFAULT_MAX_QUERIES_PER_TEMPLATE = 10
