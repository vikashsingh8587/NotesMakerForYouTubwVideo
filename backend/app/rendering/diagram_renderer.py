from __future__ import annotations

from html import escape
from typing import List, Tuple

from app.ai.schemas import Diagram


# ---------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------

SVG_WIDTH = 980


def _esc(value: str) -> str:
    return escape(str(value or ""), quote=True)


def _wrap_text(text: str, max_chars: int = 22) -> List[str]:
    """
    Wrap a label into multiple short lines so that
    diagram boxes don't become unnecessarily wide.
    """
    words = str(text or "").split()

    if not words:
        return [""]

    lines = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = f"{current} {word}".strip()
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines[:4]


def _text_lines(
    lines: List[str],
    x: float,
    y: float,
    font_size: int = 17,
    line_height: int = 22,
    anchor: str = "middle",
    weight: str = "500",
) -> str:
    result = []

    start_y = y - ((len(lines) - 1) * line_height / 2)

    for index, line in enumerate(lines):
        yy = start_y + index * line_height

        result.append(
            f'<text x="{x}" y="{yy}" '
            f'text-anchor="{anchor}" '
            f'font-size="{font_size}px" '
            f'font-weight="{weight}" '
            f'fill="#202020">'
            f"{_esc(line)}"
            f"</text>"
        )

    return "\n".join(result)


# ---------------------------------------------------------
# SVG base
# ---------------------------------------------------------

def _svg_start(height: int) -> str:
    return f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 {SVG_WIDTH} {height}"
    width="100%"
    role="img"
    aria-label="Concept diagram"
>
    <defs>

        <marker
            id="arrow"
            markerWidth="10"
            markerHeight="10"
            refX="8"
            refY="5"
            orient="auto"
            markerUnits="strokeWidth"
        >
            <path
                d="M 0 0 L 10 5 L 0 10 z"
                fill="#444"
            />
        </marker>

        <filter
            id="shadow"
            x="-20%"
            y="-20%"
            width="140%"
            height="140%"
        >
            <feDropShadow
                dx="2"
                dy="3"
                stdDeviation="2"
                flood-opacity="0.16"
            />
        </filter>

    </defs>

    <rect
        x="8"
        y="8"
        width="{SVG_WIDTH - 16}"
        height="{height - 16}"
        rx="20"
        fill="#fffdf7"
        stroke="#d7d0c0"
        stroke-width="2"
    />
"""


def _svg_end() -> str:
    return "</svg>"


# ---------------------------------------------------------
# Title
# ---------------------------------------------------------

def _title(title: str) -> str:
    return f"""
    <text
        x="{SVG_WIDTH / 2}"
        y="42"
        text-anchor="middle"
        font-size="22px"
        font-weight="700"
        fill="#1d1d1d"
    >
        {_esc(title)}
    </text>
    """


# ---------------------------------------------------------
# Flowchart / Process
# ---------------------------------------------------------

def _render_flowchart(diagram: Diagram) -> str:

    nodes = diagram.nodes[:9]

    if not nodes:
        return ""

    node_width = 360
    node_height = 72

    gap = 34

    top = 78

    total_height = (
        top
        + len(nodes) * node_height
        + max(0, len(nodes) - 1) * gap
        + 50
    )

    svg = _svg_start(total_height)

    svg += _title(diagram.title)

    positions = {}

    x = SVG_WIDTH / 2

    for index, node in enumerate(nodes):

        y = top + index * (node_height + gap)

        positions[node.id] = (
            x,
            y,
            node_width,
            node_height,
        )

    # arrows first so boxes appear above them
    for edge in diagram.edges:

        if edge.source not in positions:
            continue

        if edge.target not in positions:
            continue

        sx, sy, sw, sh = positions[edge.source]
        tx, ty, tw, th = positions[edge.target]

        x1 = sx
        y1 = sy + sh

        x2 = tx
        y2 = ty

        svg += f"""
        <line
            x1="{x1}"
            y1="{y1}"
            x2="{x2}"
            y2="{y2 - 7}"
            stroke="#444"
            stroke-width="2.5"
            marker-end="url(#arrow)"
        />
        """

        if edge.label:
            label_y = (y1 + y2) / 2

            svg += f"""
            <rect
                x="{x1 - 48}"
                y="{label_y - 12}"
                width="96"
                height="24"
                rx="8"
                fill="#fffdf7"
            />

            <text
                x="{x1}"
                y="{label_y + 5}"
                text-anchor="middle"
                font-size="13px"
                fill="#555"
            >
                {_esc(edge.label)}
            </text>
            """

    for index, node in enumerate(nodes):

        x, y, width, height = positions[node.id]

        fill = "#fff"
        
        if index == 0:
            fill = "#eef7ff"
        elif index == len(nodes) - 1:
            fill = "#effaf0"

        svg += f"""
        <rect
            x="{x - width / 2}"
            y="{y}"
            width="{width}"
            height="{height}"
            rx="16"
            fill="{fill}"
            stroke="#444"
            stroke-width="2"
            filter="url(#shadow)"
        />
        """

        lines = _wrap_text(node.label, 30)

        svg += _text_lines(
            lines,
            x,
            y + height / 2,
            font_size=17,
            line_height=21,
            weight="600",
        )

    svg += _svg_end()

    return svg


# ---------------------------------------------------------
# Tree
# ---------------------------------------------------------

def _render_tree(diagram: Diagram) -> str:

    nodes = diagram.nodes[:12]

    if not nodes:
        return ""

    total_height = 560

    svg = _svg_start(total_height)

    svg += _title(diagram.title)

    # Build adjacency
    children = {}

    for edge in diagram.edges:

        children.setdefault(edge.source, []).append(edge.target)

    # Find root
    targets = {edge.target for edge in diagram.edges}

    root = None

    for node in nodes:
        if node.id not in targets:
            root = node
            break

    if root is None:
        root = nodes[0]

    node_map = {node.id: node for node in nodes}

    # Determine levels using BFS
    levels = {}
    queue = [(root.id, 0)]
    visited = set()

    while queue:

        current, level = queue.pop(0)

        if current in visited:
            continue

        visited.add(current)

        levels.setdefault(level, []).append(current)

        for child in children.get(current, []):
            if child in node_map:
                queue.append((child, level + 1))

    # Fallback if structure is incomplete
    if not levels:
        levels = {0: [root.id]}

    max_level = max(levels.keys())

    positions = {}

    level_y = {
        level: 95 + level * 120
        for level in range(max_level + 1)
    }

    for level, ids in levels.items():

        count = len(ids)

        if count == 1:
            xs = [SVG_WIDTH / 2]

        else:
            left = 130
            right = SVG_WIDTH - 130

            step = (right - left) / (count - 1)

            xs = [
                left + i * step
                for i in range(count)
            ]

        for x, node_id in zip(xs, ids):

            positions[node_id] = (
                x,
                level_y[level],
            )

    # Draw edges first
    for edge in diagram.edges:

        if edge.source not in positions:
            continue

        if edge.target not in positions:
            continue

        sx, sy = positions[edge.source]
        tx, ty = positions[edge.target]

        svg += f"""
        <line
            x1="{sx}"
            y1="{sy + 35}"
            x2="{tx}"
            y2="{ty - 35}"
            stroke="#444"
            stroke-width="2.5"
            marker-end="url(#arrow)"
        />
        """

    # Draw nodes
    for node in nodes:

        if node.id not in positions:
            continue

        x, y = positions[node.id]

        width = 150
        height = 70

        svg += f"""
        <rect
            x="{x - width / 2}"
            y="{y - height / 2}"
            width="{width}"
            height="{height}"
            rx="14"
            fill="#fff"
            stroke="#444"
            stroke-width="2"
            filter="url(#shadow)"
        />
        """

        lines = _wrap_text(node.label, 18)

        svg += _text_lines(
            lines,
            x,
            y,
            font_size=16,
            line_height=20,
            weight="600",
        )

    svg += _svg_end()

    return svg


# ---------------------------------------------------------
# Graph
# ---------------------------------------------------------

def _render_graph(diagram: Diagram) -> str:

    nodes = diagram.nodes[:12]

    if not nodes:
        return ""

    height = 560

    svg = _svg_start(height)

    svg += _title(diagram.title)

    center_x = SVG_WIDTH / 2
    center_y = 310

    radius_x = 310
    radius_y = 180

    positions = {}

    import math

    count = len(nodes)

    for index, node in enumerate(nodes):

        angle = (
            -math.pi / 2
            + (2 * math.pi * index / count)
        )

        x = center_x + radius_x * math.cos(angle)
        y = center_y + radius_y * math.sin(angle)

        positions[node.id] = (x, y)

    # Edges
    for edge in diagram.edges:

        if edge.source not in positions:
            continue

        if edge.target not in positions:
            continue

        sx, sy = positions[edge.source]
        tx, ty = positions[edge.target]

        # Shorten line so it doesn't enter node box too much
        dx = tx - sx
        dy = ty - sy

        distance = max(
            1,
            (dx * dx + dy * dy) ** 0.5
        )

        offset = 35

        sx2 = sx + dx / distance * offset
        sy2 = sy + dy / distance * offset

        tx2 = tx - dx / distance * offset
        ty2 = ty - dy / distance * offset

        svg += f"""
        <line
            x1="{sx2}"
            y1="{sy2}"
            x2="{tx2}"
            y2="{ty2}"
            stroke="#555"
            stroke-width="2.5"
            marker-end="url(#arrow)"
        />
        """

        if edge.label:

            mx = (sx + tx) / 2
            my = (sy + ty) / 2

            svg += f"""
            <rect
                x="{mx - 40}"
                y="{my - 14}"
                width="80"
                height="28"
                rx="8"
                fill="#fffdf7"
            />

            <text
                x="{mx}"
                y="{my + 5}"
                text-anchor="middle"
                font-size="13px"
                fill="#555"
            >
                {_esc(edge.label)}
            </text>
            """

    # Nodes
    for node in nodes:

        x, y = positions[node.id]

        radius = 42

        svg += f"""
        <circle
            cx="{x}"
            cy="{y}"
            r="{radius}"
            fill="#fff"
            stroke="#444"
            stroke-width="2"
            filter="url(#shadow)"
        />
        """

        lines = _wrap_text(node.label, 12)

        svg += _text_lines(
            lines,
            x,
            y,
            font_size=14,
            line_height=18,
            weight="600",
        )

    svg += _svg_end()

    return svg


# ---------------------------------------------------------
# Architecture
# ---------------------------------------------------------

def _render_architecture(diagram: Diagram) -> str:

    nodes = diagram.nodes[:10]

    if not nodes:
        return ""

    box_width = 190
    box_height = 80

    horizontal_gap = 50

    total_width = (
        len(nodes) * box_width
        + max(0, len(nodes) - 1) * horizontal_gap
        + 100
    )

    # Keep SVG reasonably sized
    total_width = max(SVG_WIDTH, total_width)

    height = 300

    svg = f"""
    <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 {total_width} {height}"
        width="100%"
        role="img"
        aria-label="Architecture diagram"
    >

        <defs>

            <marker
                id="arrow"
                markerWidth="10"
                markerHeight="10"
                refX="8"
                refY="5"
                orient="auto"
            >
                <path
                    d="M 0 0 L 10 5 L 0 10 z"
                    fill="#444"
                />
            </marker>

            <filter
                id="shadow"
                x="-20%"
                y="-20%"
                width="140%"
                height="140%"
            >
                <feDropShadow
                    dx="2"
                    dy="3"
                    stdDeviation="2"
                    flood-opacity="0.16"
                />
            </filter>

        </defs>

        <rect
            x="8"
            y="8"
            width="{total_width - 16}"
            height="{height - 16}"
            rx="20"
            fill="#fffdf7"
            stroke="#d7d0c0"
            stroke-width="2"
        />

        <text
            x="{total_width / 2}"
            y="42"
            text-anchor="middle"
            font-size="22px"
            font-weight="700"
            fill="#1d1d1d"
        >
            {_esc(diagram.title)}
        </text>
    """

    positions = {}

    y = 130

    start_x = 60

    for index, node in enumerate(nodes):

        x = start_x + index * (
            box_width + horizontal_gap
        )

        positions[node.id] = (
            x,
            y,
            box_width,
            box_height,
        )

    # arrows
    for edge in diagram.edges:

        if edge.source not in positions:
            continue

        if edge.target not in positions:
            continue

        sx, sy, sw, sh = positions[edge.source]
        tx, ty, tw, th = positions[edge.target]

        x1 = sx + sw
        y1 = sy + sh / 2

        x2 = tx
        y2 = ty + th / 2

        svg += f"""
        <line
            x1="{x1}"
            y1="{y1}"
            x2="{x2 - 8}"
            y2="{y2}"
            stroke="#444"
            stroke-width="2.5"
            marker-end="url(#arrow)"
        />
        """

        if edge.label:

            label_x = (x1 + x2) / 2
            label_y = y1 - 10

            svg += f"""
            <text
                x="{label_x}"
                y="{label_y}"
                text-anchor="middle"
                font-size="13px"
                fill="#555"
            >
                {_esc(edge.label)}
            </text>
            """

    # boxes
    for index, node in enumerate(nodes):

        x, y, width, height = positions[node.id]

        fill = "#fff"

        if index == 0:
            fill = "#eef7ff"

        if index == len(nodes) - 1:
            fill = "#effaf0"

        svg += f"""
        <rect
            x="{x}"
            y="{y}"
            width="{width}"
            height="{height}"
            rx="16"
            fill="{fill}"
            stroke="#444"
            stroke-width="2"
            filter="url(#shadow)"
        />
        """

        lines = _wrap_text(node.label, 20)

        svg += _text_lines(
            lines,
            x + width / 2,
            y + height / 2,
            font_size=15,
            line_height=19,
            weight="600",
        )

    svg += _svg_end()

    return svg


# ---------------------------------------------------------
# Comparison
# ---------------------------------------------------------

def _render_comparison(diagram: Diagram) -> str:

    nodes = diagram.nodes[:6]

    if not nodes:
        return ""

    columns = min(len(nodes), 3)

    card_width = 250
    card_height = 150

    gap = 45

    total_width = (
        columns * card_width
        + (columns - 1) * gap
        + 80
    )

    total_width = max(total_width, SVG_WIDTH)

    rows = (
        len(nodes) + columns - 1
    ) // columns

    height = (
        90
        + rows * card_height
        + (rows - 1) * 35
        + 50
    )

    svg = f"""
    <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 {total_width} {height}"
        width="100%"
        role="img"
        aria-label="Comparison diagram"
    >

        <defs>

            <filter
                id="shadow"
                x="-20%"
                y="-20%"
                width="140%"
                height="140%"
            >
                <feDropShadow
                    dx="2"
                    dy="3"
                    stdDeviation="2"
                    flood-opacity="0.16"
                />
            </filter>

        </defs>

        <rect
            x="8"
            y="8"
            width="{total_width - 16}"
            height="{height - 16}"
            rx="20"
            fill="#fffdf7"
            stroke="#d7d0c0"
            stroke-width="2"
        />

        <text
            x="{total_width / 2}"
            y="45"
            text-anchor="middle"
            font-size="22px"
            font-weight="700"
            fill="#1d1d1d"
        >
            {_esc(diagram.title)}
        </text>
    """

    for index, node in enumerate(nodes):

        row = index // columns
        column = index % columns

        x = (
            (total_width - (
                columns * card_width
                + (columns - 1) * gap
            )) / 2
            + column * (card_width + gap)
        )

        y = (
            75
            + row * (card_height + 35)
        )

        svg += f"""
        <rect
            x="{x}"
            y="{y}"
            width="{card_width}"
            height="{card_height}"
            rx="18"
            fill="#fff"
            stroke="#444"
            stroke-width="2"
            filter="url(#shadow)"
        />
        """

        lines = _wrap_text(node.label, 25)

        svg += _text_lines(
            lines,
            x + card_width / 2,
            y + card_height / 2,
            font_size=17,
            line_height=22,
            weight="600",
        )

    svg += _svg_end()

    return svg


# ---------------------------------------------------------
# Public renderer
# ---------------------------------------------------------

def render_diagram(diagram: Diagram | None) -> str:

    if not diagram:
        return ""

    diagram_type = (
        str(diagram.type or "")
        .strip()
        .lower()
    )

    if diagram_type in {
        "flowchart",
        "process",
    }:
        return _render_flowchart(diagram)

    if diagram_type == "tree":
        return _render_tree(diagram)

    if diagram_type == "graph":
        return _render_graph(diagram)

    if diagram_type == "architecture":
        return _render_architecture(diagram)

    if diagram_type == "comparison":
        return _render_comparison(diagram)

    # Safe fallback
    return _render_flowchart(diagram)