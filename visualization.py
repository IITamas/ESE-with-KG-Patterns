from graphviz import Digraph
import networkx as nx

def remove_fluff(s):
    return ", ".join([a.split(":")[-1] if "http" not in a else a.split('/')[-1].split(":")[-1] for a in s.split(', ')])

def get_sorted_list_in_str(l):
    sorted_l = sorted(l)
    return ", ".join([remove_fluff(e) for e in sorted_l])

def multiGraphVizualizationGraphviz(G):
    dot = Digraph()
    for a, b, k in G.edges(data=True):
        dot.edge(remove_fluff(a),
                remove_fluff(b),
                label=k['name'].split('/')[-1].split(":")[-1])
    return dot

def multi_graph_viz_from_path(paths):
    dot = Digraph()
    g = {}
    for index, path in enumerate(paths[0]):
        for index2, (entity1, edge, entity2) in enumerate(path):
            if get_sorted_list_in_str(entity1)+"-"+get_sorted_list_in_str(entity2) not in g or edge not in g[get_sorted_list_in_str(entity1)+"-"+get_sorted_list_in_str(entity2)]:
                g[get_sorted_list_in_str(entity1)+"-"+get_sorted_list_in_str(entity2)] = edge
                dot.edge(get_sorted_list_in_str(entity1),
                        get_sorted_list_in_str(entity2),
                        label=remove_fluff(edge))
            if index2 == len(path)-1:
                color1 = "black"
                color2 = "black"
                if (len(path)==1 and get_sorted_list_in_str(entity1) == get_sorted_list_in_str(paths[3])) or (len(path)>1 and get_sorted_list_in_str(entity1) == get_sorted_list_in_str(paths[2])):
                    color2 = "green"
                    if index == len(paths[0])-1:
                        color2 = "green" if paths[1] else "blue"
                else:
                    color1 = "green"
                    if index == len(paths[0])-1:
                        color1 = "green" if paths[1] else "blue"
                dot.node(get_sorted_list_in_str(entity1), color=color1)
                dot.node(get_sorted_list_in_str(entity2), color=color2)
    return dot

def create_graph_for_viz_from_path(paths):
    M = nx.MultiDiGraph()
    for path in paths:
        for entity1, edge, entity2 in path:
            M.add_edge(get_sorted_list_in_str(entity1), get_sorted_list_in_str(entity2), name=edge, key=edge)
    return M
