import os
from datetime import datetime
from pathlib import Path
import networkx as nx
from visualization import (
    multiGraphVizualizationGraphviz,
    create_graph_for_viz_from_path,
)


class VisualizationManager:
    def __init__(self, output_dir="output"):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_output_dir = Path(output_dir)
        self.output_dir_for_run = self.base_output_dir / f"run_{self.timestamp}"
        self.viz_dir = self.output_dir_for_run / "visualizations"
        self._ensure_directories()

    def _ensure_directories(self):
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir_for_run.mkdir(exist_ok=True)
        self.viz_dir.mkdir(exist_ok=True)

    def get_results_path(self, filename="results.json"):
        return self.output_dir_for_run / filename

    def save_path_visualization(self, paths_data, query_id, template_id_str):
        if not paths_data:
            return None

        template_dir = self.viz_dir / str(template_id_str)
        template_dir.mkdir(exist_ok=True)

        try:
            graph = create_graph_for_viz_from_path(paths_data)
            if not graph.edges():
                print(
                    f"No edges in graph for query {query_id}, template {template_id_str}. Skipping path viz."
                )
                return None
            viz = multiGraphVizualizationGraphviz(graph)
            output_file_path = template_dir / f"paths_query_{query_id}"
            saved_filename = viz.render(
                filename=str(output_file_path), format="png", cleanup=True, quiet=True
            )
            return saved_filename
        except Exception as e:
            print(
                f"Error creating path visualization for query {query_id}, template {template_id_str}: {e}"
            )
            return None

    def save_expanded_entities_graph(
        self, seed_entities, expanded_entities, query_id, template_id_str
    ):
        if not expanded_entities and not seed_entities:
            return None

        template_dir = self.viz_dir / str(template_id_str)
        template_dir.mkdir(exist_ok=True)

        try:
            from graphviz import Digraph

            dot = Digraph(comment=f"Expanded entities for query {query_id}")
            dot.node("Seed Entities", color="blue", shape="box")
            for entity in seed_entities:
                entity_name = entity.split("/")[-1]
                dot.node(entity_name, color="green", shape="ellipse")
                dot.edge("Seed Entities", entity_name)

            newly_expanded = [e for e in expanded_entities if e not in seed_entities]
            if newly_expanded:
                dot.node("Expanded Results", color="red", shape="box")
                dot.edge("Seed Entities", "Expanded Results")
                for entity in newly_expanded:
                    entity_name = entity.split("/")[-1]
                    dot.node(entity_name, color="gray", shape="ellipse")
                    dot.edge("Expanded Results", entity_name)
            elif expanded_entities:
                dot.node("Expanded (Same as Seeds)", color="orange", shape="box")
                dot.edge("Seed Entities", "Expanded (Same as Seeds)")

            output_file_path = template_dir / f"entities_query_{query_id}"
            saved_filename = dot.render(
                filename=str(output_file_path), format="png", cleanup=True, quiet=True
            )
            return saved_filename
        except Exception as e:
            print(
                f"Error creating entities visualization for query {query_id}, template {template_id_str}: {e}"
            )
            return None

    def save_summary_visualization(self, metrics_by_template):
        if not metrics_by_template:
            return None
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            plt.figure(figsize=(15, 8))
            template_names = list(metrics_by_template.keys())
            precision = [
                metrics_by_template[t].get("precision", 0) for t in template_names
            ]
            recall = [metrics_by_template[t].get("recall", 0) for t in template_names]
            f1 = [metrics_by_template[t].get("f1", 0) for t in template_names]

            x = np.arange(len(template_names))
            width = 0.25

            rects1 = plt.bar(x - width, precision, width, label="Precision")
            rects2 = plt.bar(x, recall, width, label="Recall")
            rects3 = plt.bar(x + width, f1, width, label="F1 Score")

            plt.xlabel("Template Category")
            plt.ylabel("Score")
            plt.title("Performance Metrics by Template Category")
            plt.xticks(x, template_names, rotation=45, ha="right")
            plt.legend()
            plt.ylim(0, 1.05)
            plt.tight_layout()

            def autolabel(rects):
                for rect in rects:
                    height = rect.get_height()
                    plt.annotate(
                        f"{height:.2f}",
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                    )

            autolabel(rects1)
            autolabel(rects2)
            autolabel(rects3)

            summary_file_path = self.output_dir_for_run / "performance_summary.png"
            plt.savefig(str(summary_file_path))
            plt.close()
            return str(summary_file_path)
        except Exception as e:
            print(f"Error creating summary visualization: {e}")
            return None
