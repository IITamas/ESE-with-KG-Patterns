import json
import re


class DatabaseParser:
    """Parse and manage SPARQL queries from a database."""

    def __init__(self, database_path=None):
        """Initialize with optional database path."""
        self.data = []
        if database_path:
            self.load_database(database_path)

    def load_database(self, database_path):
        """Load database from JSON file."""
        with open(database_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        return self.data

    def extract_entities_from_query(self, query):
        """Extract DBpedia resource URIs from a SPARQL query."""
        resource_pattern = r"<(http://dbpedia\.org/resource/[^>]+)>"
        entities = re.findall(resource_pattern, query)
        return entities

    def get_query_by_id(self, query_id):
        """Get a query by its ID."""
        for item in self.data:
            if item.get("_id") == str(query_id):
                return item
        return None

    def get_queries_by_template(self, template_id):
        """Get all queries with a specific template ID."""
        return [
            item for item in self.data if item.get("sparql_template_id") == template_id
        ]

    def get_seed_entities(self, query_item, sample_size=5):
        """Extract seed entities from a query item."""
        query = query_item.get("sparql_query", "")
        entities = self.extract_entities_from_query(query)

        if len(entities) < sample_size:
            return entities

        import random

        if len(entities) > sample_size:
            return random.sample(entities, sample_size)
        return entities
