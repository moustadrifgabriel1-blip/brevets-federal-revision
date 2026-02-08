"""
Graphe visuel interactif des concepts — Brevet Fédéral
======================================================
Construit un graphe NetworkX à partir du concept_map, puis le rend
en Plotly pour une visualisation interactive dans Streamlit.
"""

import ast as _ast
import random
import math
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import networkx as nx
import plotly.graph_objects as go


# Palette de couleurs par module
MODULE_COLORS = {
    "AA01": "#e53935", "AA02": "#d81b60", "AA03": "#8e24aa", "AA04": "#5e35b1",
    "AA05": "#3949ab", "AA06": "#1e88e5", "AA07": "#039be5", "AA08": "#00acc1",
    "AA09": "#00897b", "AA10": "#43a047", "AA11": "#7cb342",
    "AE01": "#c0ca33", "AE02": "#fdd835", "AE03": "#ffb300", "AE04": "#fb8c00",
    "AE05": "#f4511e", "AE06": "#6d4c41", "AE07": "#757575", "AE09": "#546e7a",
    "AE10": "#26a69a", "AE11": "#66bb6a", "AE12": "#ef5350", "AE13": "#ab47bc",
}

IMPORTANCE_SIZE = {
    "critical": 20,
    "high": 14,
    "medium": 9,
    "low": 6,
}


def _safe_parse_list(val) -> List[str]:
    """Parse un champ qui peut être une string repr de liste ou une vraie liste."""
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        val = val.strip()
        if val.startswith("["):
            try:
                return _ast.literal_eval(val)
            except Exception:
                return []
        elif val:
            return [val]
    return []


def build_graph(nodes: List[Dict],
                modules_filter: List[str] = None,
                importance_filter: List[str] = None,
                max_nodes: int = 150) -> nx.Graph:
    """
    Construit un graphe NetworkX depuis les nœuds du concept_map.
    Les arêtes sont déduites des champs prerequisites / dependents.
    """
    # Filtrer
    filtered = nodes
    if modules_filter:
        filtered = [n for n in filtered if n.get('module') in modules_filter]
    if importance_filter:
        filtered = [n for n in filtered if n.get('importance') in importance_filter]

    # Limiter
    if len(filtered) > max_nodes:
        # Priorité aux critiques puis hauts
        priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        filtered.sort(key=lambda n: priority.get(n.get('importance', 'medium'), 2))
        filtered = filtered[:max_nodes]

    G = nx.Graph()

    # Index par nom (lowercase) pour résoudre les liens
    name_to_id = {}
    for n in filtered:
        nid = n.get('id', n.get('name', ''))
        name_to_id[n.get('name', '').lower()] = nid

    # Ajouter les nœuds
    for n in filtered:
        nid = n.get('id', n.get('name', ''))
        G.add_node(nid,
                   name=n.get('name', ''),
                   module=n.get('module', '?'),
                   category=n.get('category', ''),
                   importance=n.get('importance', 'medium'),
                   keywords=', '.join(n.get('keywords', []) if isinstance(n.get('keywords'), list) else []))

    # Construire les arêtes depuis prerequisites / dependents
    for n in filtered:
        nid = n.get('id', n.get('name', ''))

        for prereq in _safe_parse_list(n.get('prerequisites', [])):
            target = name_to_id.get(prereq.lower())
            if target and target != nid and target in G:
                G.add_edge(target, nid, relation="prerequisite")

        for dep in _safe_parse_list(n.get('dependents', [])):
            target = name_to_id.get(dep.lower())
            if target and target != nid and target in G:
                G.add_edge(nid, target, relation="dependent")

    # Ajouter des arêtes intra-module pour les nœuds isolés (même catégorie)
    isolates = list(nx.isolates(G))
    cat_groups = defaultdict(list)
    for iso in isolates:
        mod = G.nodes[iso].get('module', '')
        cat = G.nodes[iso].get('category', '')
        cat_groups[(mod, cat)].append(iso)

    for (mod, cat), group in cat_groups.items():
        if len(group) >= 2:
            # Connecter en chaîne les concepts de même catégorie+module
            for i in range(len(group) - 1):
                G.add_edge(group[i], group[i + 1], relation="same_category")

    return G


def graph_to_plotly(G: nx.Graph,
                    layout: str = "spring",
                    height: int = 700) -> go.Figure:
    """
    Convertit un graphe NetworkX en figure Plotly interactive.
    """
    if len(G.nodes) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Aucun concept à afficher", showarrow=False,
                           font=dict(size=20))
        fig.update_layout(height=400)
        return fig

    # Layout
    if layout == "spring":
        pos = nx.spring_layout(G, k=2.5 / math.sqrt(len(G.nodes)), iterations=60, seed=42)
    elif layout == "kamada_kawai" and len(G.nodes) <= 200:
        try:
            pos = nx.kamada_kawai_layout(G)
        except Exception:
            pos = nx.spring_layout(G, k=2.5 / math.sqrt(len(G.nodes)), iterations=60, seed=42)
    elif layout == "circular":
        pos = nx.circular_layout(G)
    elif layout == "shell":
        # Group by module for shell layout
        shells = defaultdict(list)
        for node in G.nodes:
            mod = G.nodes[node].get('module', '?')
            shells[mod].append(node)
        shell_list = list(shells.values())
        pos = nx.shell_layout(G, nlist=shell_list if len(shell_list) > 1 else None)
    else:
        pos = nx.spring_layout(G, k=2.5 / math.sqrt(len(G.nodes)), iterations=60, seed=42)

    # --- ARÊTES ---
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.8, color='rgba(150,150,150,0.4)'),
        hoverinfo='none',
        mode='lines',
        name='Liens'
    )

    # --- NŒUDS ---
    node_x, node_y = [], []
    node_text, node_hover, node_color, node_size = [], [], [], []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        data = G.nodes[node]
        name = data.get('name', node)
        module = data.get('module', '?')
        importance = data.get('importance', 'medium')
        category = data.get('category', '')
        keywords = data.get('keywords', '')
        degree = G.degree(node)

        # Tronquer le nom pour l'affichage
        short_name = name[:25] + "…" if len(name) > 25 else name
        node_text.append(short_name)

        hover = (
            f"<b>{name}</b><br>"
            f"Module: {module}<br>"
            f"Importance: {importance}<br>"
            f"Catégorie: {category}<br>"
            f"Connexions: {degree}<br>"
            f"Mots-clés: {keywords}"
        )
        node_hover.append(hover)

        color = MODULE_COLORS.get(module, '#999999')
        node_color.append(color)

        size = IMPORTANCE_SIZE.get(importance, 9)
        # Bonus pour les nœuds très connectés
        size += min(degree * 1.5, 10)
        node_size.append(size)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        hovertext=node_hover,
        text=node_text,
        textposition="top center",
        textfont=dict(size=7, color='rgba(50,50,50,0.8)'),
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=1, color='white'),
            opacity=0.85,
        ),
        name='Concepts'
    )

    # --- FIGURE ---
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False,
        hovermode='closest',
        height=height,
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    return fig


def get_graph_stats(G: nx.Graph) -> Dict:
    """Calcule des statistiques sur le graphe."""
    if len(G.nodes) == 0:
        return {"nodes": 0, "edges": 0, "components": 0,
                "density": 0, "hub_nodes": [], "isolated": 0}

    components = nx.number_connected_components(G)
    density = nx.density(G)
    degrees = dict(G.degree())

    # Top 5 hubs (nœuds les plus connectés)
    top_hubs = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
    hub_info = []
    for nid, deg in top_hubs:
        name = G.nodes[nid].get('name', nid)
        module = G.nodes[nid].get('module', '?')
        hub_info.append({"name": name, "module": module, "connections": deg})

    isolated = len(list(nx.isolates(G)))

    # Modules represented
    mod_counts = defaultdict(int)
    for n in G.nodes:
        mod_counts[G.nodes[n].get('module') or '?'] += 1

    return {
        "nodes": len(G.nodes),
        "edges": len(G.edges),
        "components": components,
        "density": round(density, 4),
        "hub_nodes": hub_info,
        "isolated": isolated,
        "modules": dict(sorted(mod_counts.items(), key=lambda x: str(x[0]))),
    }
