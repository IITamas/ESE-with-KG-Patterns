import os
from datetime import datetime
from pathlib import Path
import networkx as nx
from visualization import (
    multiGraphVizualizationGraphviz,
    create_graph_for_viz_from_path,
)


class VisualizationManager:
    """Manage the creation and saving of visualizations."""

    def __init__(self, output_dir="output"):
        """Initialize with output directory."""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_output_dir = output_dir
        self.output_dir = os.path.join(output_dir, f"run_{self.timestamp}")
        self.viz_dir = os.path.join(self.output_dir, "visualizations")
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure all required directories exist."""
        Path(self.base_output_dir).mkdir(exist_ok=True)
        Path(self.output_dir).mkdir(exist_ok=True)
        Path(self.viz_dir).mkdir(exist_ok=True)

    def get_results_path(self, filename="results.json"):
        """Get the full path for saving results."""
        return os.path.join(self.output_dir, filename)

    def save_path_visualization(self, paths, query_id, template_id):
        """Save visualization of semantic paths."""
        if not paths:
            return None

        # Create a subdirectory for this template
        template_dir = os.path.join(self.viz_dir, f"template_{template_id}")
        Path(template_dir).mkdir(exist_ok=True)

        # Create graph and render visualization
        try:
            graph = create_graph_for_viz_from_path(paths)
            viz = multiGraphVizualizationGraphviz(graph)

            # Save visualization
            output_file = os.path.join(template_dir, f"paths_query_{query_id}")
            viz.render(filename=output_file, format="png", cleanup=True)
            return output_file + ".png"
        except Exception as e:
            print(f"Error creating visualization for query {query_id}: {e}")
            return None

    def save_expanded_entities_graph(
        self, seed_entities, expanded_entities, query_id, template_id
    ):
        """Create and save a graph visualization showing seed and expanded entities."""
        if not expanded_entities:
            return None

        # Create a subdirectory for this template
        template_dir = os.path.join(self.viz_dir, f"template_{template_id}")
        Path(template_dir).mkdir(exist_ok=True)

        try:
            # Create a simple graph with seed entities in one color and expanded in another
            G = nx.DiGraph()

            # Add a central "Seed Entities" node
            G.add_node("Seed Entities", color="blue")

            # Add seed entities
            for entity in seed_entities:
                entity_name = entity.split("/")[-1]
                G.add_node(entity_name, color="green")
                G.add_edge("Seed Entities", entity_name)

            # Add expanded entities
            for entity in expanded_entities:
                if entity not in seed_entities:
                    entity_name = entity.split("/")[-1]
                    G.add_node(entity_name, color="gray")
                    G.add_edge("Results", entity_name)

            # Add a "Results" node
            G.add_node("Results", color="red")
            G.add_edge("Seed Entities", "Results")

            # Create visualization
            from graphviz import Digraph

            dot = Digraph(comment=f"Expanded entities for query {query_id}")

            # Add nodes with color
            for node, attrs in G.nodes(data=True):
                dot.node(str(node), color=attrs.get("color", "black"))

            # Add edges
            for u, v in G.edges():
                dot.edge(str(u), str(v))

            # Save visualization
            output_file = os.path.join(template_dir, f"entities_query_{query_id}")
            dot.render(filename=output_file, format="png", cleanup=True)
            return output_file + ".png"
        except Exception as e:
            print(f"Error creating entities visualization for query {query_id}: {e}")
            return None

    def save_summary_visualization(self, metrics_by_template):
        """Create and save summary visualizations of the experiment results."""
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            # Create metrics visualization
            plt.figure(figsize=(12, 8))

            templates = list(metrics_by_template.keys())
            precision = [metrics_by_template[t].get("precision", 0) for t in templates]
            recall = [metrics_by_template[t].get("recall", 0) for t in templates]
            f1 = [metrics_by_template[t].get("f1", 0) for t in templates]

            x = np.arange(len(templates))
            width = 0.25

            plt.bar(x - width, precision, width, label="Precision")
            plt.bar(x, recall, width, label="Recall")
            plt.bar(x + width, f1, width, label="F1 Score")

            plt.xlabel("Template ID")
            plt.ylabel("Score")
            plt.title("Performance by Template")
            plt.xticks(x, templates)
            plt.legend()
            plt.ylim(0, 1.0)

            # Add values on top of bars
            for i, v in enumerate(precision):
                plt.text(i - width, v + 0.02, f"{v:.2f}", ha="center")
            for i, v in enumerate(recall):
                plt.text(i, v + 0.02, f"{v:.2f}", ha="center")
            for i, v in enumerate(f1):
                plt.text(i + width, v + 0.02, f"{v:.2f}", ha="center")

            # Save figure
            summary_file = os.path.join(self.output_dir, "performance_summary.png")
            plt.savefig(summary_file)
            plt.close()

            return summary_file
        except Exception as e:
            print(f"Error creating summary visualization: {e}")
            return None
