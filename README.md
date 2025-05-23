# Knowledge Graph Entity Set Expansion

This project implements an automated entity set expansion algorithm using knowledge graphs. Given a small set of seed entities, it identifies the common semantic patterns between them and uses those patterns to find similar entities.

## Overview

Entity set expansion (ESE) is the task of expanding a small set of seed entities into a more complete set based on their semantic similarity. This implementation uses knowledge graphs (specifically DBpedia) to find semantic paths between entities and generate SPARQL queries that capture these patterns.

## Installation

### Requirements
- Python 3.6+
- rdflib
- SPARQLWrapper
- networkx
- graphviz
- matplotlib (for visualization summaries)

Install the required packages:

```bash
pip install rdflib SPARQLWrapper networkx graphviz matplotlib
```

For visualization functionality, you also need to install the Graphviz executable:

```bash
# On Ubuntu/Debian
apt-get install libgraphviz-dev

# On macOS
brew install graphviz

# On Windows
# Download and install from https://graphviz.org/download/
```

## File Structure

### Core Components
- `sparql_wrapper.py`: Handles caching and execution of SPARQL queries
- `visualization.py`: Provides graph visualization utilities
- `graph_explorer.py`: Contains logic for exploring knowledge graph paths
- `path_processor.py`: Processes and normalizes semantic paths
- `query_generator.py`: Generates SPARQL queries from processed paths
- `set_extension.py`: Core class that orchestrates the entity set expansion process

### Evaluation and Experimentation
- `db_parser.py`: Parses and extracts information from a database of SPARQL queries
- `evaluation.py`: Calculates evaluation metrics (precision, recall, F1 score)
- `experiment_runner.py`: Runs experiments on a database of queries
- `visualization_manager.py`: Manages the creation and saving of visualizations
- `main.py`: Example script with support for both simple demos and full experiments

## Usage

### Basic Usage

```python
from sparql_wrapper import SPARQLWrapperCache
from set_extension import CompositeGraphBasedSetExtension

# Initialize SPARQL wrapper
sparql = SPARQLWrapperCache("http://dbpedia.org/sparql", "http://dbpedia.org", 180)

# Create entity set expansion model
filter_pattern = "\"(.*sameAs|.*wiki.*|.*seeAlso|.*wordnet_type|.*subdivision|.*subject|.*depiction|.*isPrimaryTopicOf|.*wasDerivedFrom|.*homepage|.*thumbnail|.*hypernym|.*exactMatch)\""
model = CompositeGraphBasedSetExtension(
    sparql, 
    path_length=3, 
    right_extensions=1, 
    filter=filter_pattern, 
    min_or_num=2
)

# Define seed entities
seed_entities = [
    "http://dbpedia.org/resource/Budapest",
    "http://dbpedia.org/resource/Szeged",
    "http://dbpedia.org/resource/Mátraverebély"
]

# Perform entity set expansion
results, query = model.get_results(seed_entities)
print(f"Found {len(results)} similar entities")
```

### Running Experiments

You can run experiments on a database of SPARQL queries using the `experiment_runner.py` module:

```python
from experiment_runner import ExperimentRunner

# Initialize experiment runner with database path and visualization enabled
runner = ExperimentRunner("path/to/database.json", output_dir="output", visualize=True)

# Run experiments on specific template IDs
template_ids = [1, 2, 301, 302]
results = runner.run_experiments(template_ids, sample_size=5, max_queries_per_template=5)

# Calculate overall metrics
metrics = runner.calculate_overall_metrics()
print(f"Overall precision: {metrics['precision']:.2f}")
print(f"Overall recall: {metrics['recall']:.2f}")
print(f"Overall F1 score: {metrics['f1']:.2f}")

# Save results to a file
runner.save_results()
```

### Command-Line Interface

The main.py script provides a command-line interface for running both simple examples and experiments:

```bash
# Run a simple example
python main.py --example

# Run a simple example with visualization
python main.py --example --visualize --output output_folder

# Run experiments on a database
python main.py --database path/to/database.json --output output_folder --templates 1 2 301 302 --sample_size 5 --max_queries 5 --visualize
```

Command-line arguments:
- `--example`: Run a simple demonstration with Hungarian cities
- `--database`: Path to the database JSON file containing SPARQL queries
- `--output`: Directory to save results and visualizations (default: output)
- `--templates`: Template IDs to run experiments on (default: [1, 2, 301, 302])
- `--sample_size`: Number of seed entities to use (default: 5)
- `--max_queries`: Maximum number of queries per template (default: 5)
- `--visualize`: Generate and save visualizations

## Output Structure

When running with visualizations enabled, the system creates an organized output directory:

```
output/
└── run_YYYYMMDD_HHMMSS/
    ├── results.json
    ├── performance_summary.png
    └── visualizations/
        ├── example/
        │   ├── paths_query_example.png
        │   └── entities_query_example.png
        ├── template_1/
        │   ├── paths_query_1234.png
        │   └── entities_query_1234.png
        └── template_301/
            ├── paths_query_5678.png
            └── entities_query_5678.png
```


Each run is timestamped to preserve results from multiple executions.

## Parameters

The `CompositeGraphBasedSetExtension` class accepts several parameters:

- `path_length`: Maximum path length to explore (default: 4)
- `right_extensions`: Maximum number of incoming connections to explore (default: 0)
- `filter`: Regex pattern for filtering irrelevant edge types
- `min_or_num`: Minimum entity count for creating VALUES clauses (default: 3)
- `max_or_num`: Maximum entity count to include in a path (default: 5)

## Evaluation Metrics

The system uses standard information retrieval metrics to evaluate performance:

- **Precision**: The proportion of retrieved entities that are relevant
- **Recall**: The proportion of relevant entities that are retrieved
- **F1 Score**: The harmonic mean of precision and recall

These metrics are calculated by the `EvaluationMetrics` class in evaluation.py.

## Visualizations

The system can generate several types of visualizations:

1. **Path Visualizations**: Show the semantic paths discovered between seed entities
2. **Entity Visualizations**: Display the relationships between seed entities and expanded results
3. **Performance Summary**: Bar charts showing precision, recall, and F1 scores by template

These visualizations help in understanding how the entity set expansion algorithm works and in analyzing its performance across different types of queries.
