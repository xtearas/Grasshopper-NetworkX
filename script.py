import Grasshopper as gh
import networkx as nx
import ghpythonlib.treehelpers as th
import math

current_doc = ghenv.Component.OnPingDocument()
ghObjects = current_doc.Objects

G = nx.DiGraph()

for obj in ghObjects:
    a_Id = obj.InstanceGuid

    is_component = current_doc.FindComponent(a_Id)
    is_param = current_doc.FindParameter(a_Id)

    if is_component is not None or is_param is not None:
        a_X = obj.Attributes.Pivot.X
        a_Y = obj.Attributes.Pivot.Y

        a_Bounds = obj.Attributes.Bounds

        G.add_node(a_Id)
        G.nodes[a_Id]["pos"] = (a_X, a_Y)
        G.nodes[a_Id]["name"] = obj.Name
    else:
        continue

    if is_component is None and is_param is not None:
        for input_param in is_param.Sources:
            b_Id = input_param.Attributes.GetTopLevel.DocObject.InstanceGuid

            b_X = input_param.Attributes.GetTopLevel.DocObject.Attributes.Pivot.X
            b_Y = input_param.Attributes.GetTopLevel.DocObject.Attributes.Pivot.Y
            b_Bounds = input_param.Attributes.GetTopLevel.DocObject.Attributes.Bounds

            G.add_edge(b_Id, a_Id)

            G.nodes[b_Id]["pos"] = (b_X, b_Y)
            G.nodes[b_Id]["name"] = input_param.Attributes.GetTopLevel.DocObject.Name
        continue
    

    for param in is_component.Params:
        for input_param in param.Sources:
            b_Id = input_param.Attributes.GetTopLevel.DocObject.InstanceGuid

            b_X = input_param.Attributes.GetTopLevel.DocObject.Attributes.Pivot.X
            b_Y = input_param.Attributes.GetTopLevel.DocObject.Attributes.Pivot.Y
            b_Bounds = input_param.Attributes.GetTopLevel.DocObject.Attributes.Bounds

            G.add_edge(b_Id, a_Id)

            G.nodes[b_Id]["pos"] = (b_X, b_Y)
            G.nodes[b_Id]["name"] = input_param.Attributes.GetTopLevel.DocObject.Name


S = [G.subgraph(c).copy() for c in nx.weakly_connected_components(G)]

all_edges = []
all_nodes = []
original_nodes = []
original_edges = []
node_names = []
node_types = []
node_degrees = []
edge_degrees = []
node_levels = []

# move subraphs in Y direction to aoid overlap
total_Y = 0

for s in S:
    if len(s.edges) == 0:
        continue
    
    max_Y = 0
    min_Y = math.inf

    for layer, nodes in enumerate(nx.topological_generations(s)):
        # `multipartite_layout` expects the layer as a node attribute, so add the
        # numeric layer value as a node attribute
        for node in nodes:
            s.nodes[node]["layer"] = layer

    # Compute the multipartite_layout using the "layer" node attribute
    pos = nx.multipartite_layout(s, subset_key="layer")

    for key in pos:
        if pos[key][1] > max_Y:
            max_Y = pos[key][1]
        if pos[key][1] < min_Y:
            min_Y = pos[key][1]

    original_nodes_ = []
    node_degrees_ = []
    edge_degrees_ = []
    node_names_ = []
    node_types_ = []
    node_levels_ = []
    nodes = []

    for key in pos:
        original_nodes_.append([s.nodes[key]["pos"][0], -s.nodes[key]["pos"][1]])
        node_names_.append(s.nodes[key]["name"].replace(' ', '\n') )
        nodes.append([pos[key][0], pos[key][1] + total_Y + abs(min_Y)])
        node_degrees_.append(s.degree[key])
        node_levels_.append(s.nodes[key]["layer"])
        if s.out_degree[key] == 0:
            node_types_.append("#F04854")
        elif s.in_degree[key] == 0:
            node_types_.append("#41B0C1")
        else:
            node_types_.append("#505149")
    
    edges = []
    original_edges_ = []
    for e in s.edges:
        edges.append([
            [pos[e[0]][0], pos[e[0]][1] + total_Y + abs(min_Y)], 
            [pos[e[1]][0], pos[e[1]][1] + total_Y + abs(min_Y)]
            ])
        original_edges_.append([
            [s.nodes[e[0]]["pos"][0], -s.nodes[e[0]]["pos"][1]], 
            [s.nodes[e[1]]["pos"][0], -s.nodes[e[1]]["pos"][1]]
            ])
        edge_degrees_.append([
            s.degree[e[0]], 
            s.degree[e[1]]
            ])

    total_Y += max_Y + abs(min_Y) + 0.2

    all_edges.append(edges)
    all_nodes.append(nodes)
    original_nodes.append(original_nodes_)
    original_edges.append(original_edges_)
    node_names.append(node_names_)
    node_degrees.append(node_degrees_)
    edge_degrees.append(edge_degrees_)
    node_types.append(node_types_)
    node_levels.append(node_levels_)


all_edges = th.list_to_tree(all_edges)
all_nodes = th.list_to_tree(all_nodes)

original_nodes = th.list_to_tree(original_nodes)
original_edges = th.list_to_tree(original_edges)

node_names = th.list_to_tree(node_names)
node_degrees = th.list_to_tree(node_degrees)
edge_degrees = th.list_to_tree(edge_degrees)
node_types = th.list_to_tree(node_types)
node_levels = th.list_to_tree(node_levels)
