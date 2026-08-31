"""Structured step-list -> Mermaid-style definition -> SVG (ADR-0006).

Rendering is a small hand-rolled layered-box layout rather than an
external Mermaid renderer (no `mermaid-cli`/Node, no hosted mermaid.ink
API): ADR-0006 limits this block type to linear/branching step sequences,
which a plain layered layout draws just fine, and pulling in Node or a
network-dependent rendering service would undercut ADR-0010's reasoning
for a lightweight, offline, Python-only render path.
"""

from __future__ import annotations

from qms_incub.documents.blocks import FlowchartStep

_BOX_WIDTH = 200
_BOX_HEIGHT = 56
_H_GAP = 40
_V_GAP = 60
_MARGIN = 20


def steps_to_mermaid(steps: list[FlowchartStep]) -> str:
    """Compile the step list to a Mermaid-style flowchart definition."""
    lines = ["flowchart TD"]
    for step in steps:
        label = step.label.replace('"', "'")
        lines.append(f'    {step.id}["{label}"]')
    for step in steps:
        for target in step.next:
            lines.append(f"    {step.id} --> {target}")
    return "\n".join(lines)


def _layer_steps(steps: list[FlowchartStep]) -> list[list[FlowchartStep]]:
    """Layer steps top-to-bottom by longest-path depth from a root."""
    by_id = {step.id: step for step in steps}
    incoming: dict[str, int] = {step.id: 0 for step in steps}
    for step in steps:
        for target in step.next:
            incoming[target] = incoming.get(target, 0) + 1

    depth: dict[str, int] = {}

    def compute_depth(step_id: str, seen: frozenset[str]) -> int:
        if step_id in depth:
            return depth[step_id]
        if step_id in seen:
            # Cycle guard — treat as depth 0 rather than recursing forever.
            return 0
        preds = [s for s in steps if step_id in s.next]
        if not preds:
            depth[step_id] = 0
        else:
            depth[step_id] = 1 + max(
                compute_depth(p.id, seen | {step_id}) for p in preds
            )
        return depth[step_id]

    for step in steps:
        compute_depth(step.id, frozenset())

    max_depth = max(depth.values(), default=0)
    layers: list[list[FlowchartStep]] = [[] for _ in range(max_depth + 1)]
    for step in steps:
        layers[depth[step.id]].append(by_id[step.id])
    return layers


def render_flowchart_svg(steps: list[FlowchartStep]) -> str:
    """Render the step list to a standalone SVG flowchart diagram."""
    if not steps:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>'

    layers = _layer_steps(steps)
    positions: dict[str, tuple[float, float]] = {}
    max_layer_width = max(len(layer) for layer in layers)
    total_width = _MARGIN * 2 + max_layer_width * _BOX_WIDTH + (max_layer_width - 1) * _H_GAP
    total_height = _MARGIN * 2 + len(layers) * _BOX_HEIGHT + (len(layers) - 1) * _V_GAP

    for layer_index, layer in enumerate(layers):
        layer_width = len(layer) * _BOX_WIDTH + (len(layer) - 1) * _H_GAP
        start_x = (total_width - layer_width) / 2
        layer_y = float(_MARGIN + layer_index * (_BOX_HEIGHT + _V_GAP))
        for i, step in enumerate(layer):
            box_x = start_x + i * (_BOX_WIDTH + _H_GAP)
            positions[step.id] = (box_x, layer_y)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" '
        f'height="{total_height}" viewBox="0 0 {total_width} {total_height}">',
        "<defs>",
        '  <marker id="arrowhead" markerWidth="10" markerHeight="7" '
        'refX="9" refY="3.5" orient="auto">',
        '    <polygon points="0 0, 10 3.5, 0 7" fill="#334155" />',
        "  </marker>",
        "</defs>",
    ]

    for step in steps:
        x0, y0 = positions[step.id]
        for target_id in step.next:
            if target_id not in positions:
                continue
            x1, y1 = positions[target_id]
            start = (x0 + _BOX_WIDTH / 2, y0 + _BOX_HEIGHT)
            end = (x1 + _BOX_WIDTH / 2, y1)
            parts.append(
                f'<line x1="{start[0]}" y1="{start[1]}" x2="{end[0]}" y2="{end[1]}" '
                'stroke="#334155" stroke-width="2" marker-end="url(#arrowhead)" />'
            )

    for step in steps:
        x, y = positions[step.id]
        label = (
            step.label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        parts.append(
            f'<rect x="{x}" y="{y}" width="{_BOX_WIDTH}" height="{_BOX_HEIGHT}" '
            'rx="8" fill="#eef2ff" stroke="#4338ca" stroke-width="1.5" />'
        )
        parts.append(
            f'<text x="{x + _BOX_WIDTH / 2}" y="{y + _BOX_HEIGHT / 2}" '
            'text-anchor="middle" dominant-baseline="middle" '
            'font-family="sans-serif" font-size="13" fill="#1e1b4b">'
            f"{label}</text>"
        )

    parts.append("</svg>")
    return "\n".join(parts)
