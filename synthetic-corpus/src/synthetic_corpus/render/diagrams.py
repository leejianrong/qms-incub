"""SVG renderers for flowchart and swim-lane diagram blocks, written from
scratch (no shared code with the backend's now-deleted diagram engine —
ADR-0012).

Both block types share one layout primitive: steps are laid out top-to-
bottom in list order (row = index in `steps`); a swim-lane block additionally
places each step's column (x-position) by its lane, and draws lane-header
columns. A lane-free flowchart is the same layout with a single implicit
column.
"""

from __future__ import annotations

from dataclasses import dataclass

from synthetic_corpus.blocks import DiagramStep, DiagramTransition, FlowchartBlock, SwimLaneBlock

_BOX_WIDTH = 200
_BOX_HEIGHT = 56
_ROW_HEIGHT = 110
_COL_WIDTH = 240
_LANE_HEADER_HEIGHT = 40
_MARGIN = 30
_FONT_SIZE = 13
_MAX_CHARS_PER_LINE = 24


@dataclass(frozen=True)
class _BoxPosition:
    x: float
    y: float


def render_flowchart_svg(block: FlowchartBlock) -> str:
    """Lane-free: every step in a single top-to-bottom column."""
    positions = {
        step.id: _BoxPosition(x=_MARGIN, y=_MARGIN + i * _ROW_HEIGHT)
        for i, step in enumerate(block.steps)
    }
    width = _MARGIN * 2 + _BOX_WIDTH
    height = _MARGIN * 2 + max(len(block.steps), 1) * _ROW_HEIGHT - (_ROW_HEIGHT - _BOX_HEIGHT)
    body = _render_boxes_and_arrows(block.steps, block.transitions, positions)
    return _wrap_svg(width, height, body)


def render_swimlane_svg(block: SwimLaneBlock) -> str:
    """Steps assigned to lanes: x-position (column) comes from the step's
    lane, y-position (row) from its order in the step list."""
    lane_index = {lane: i for i, lane in enumerate(block.lanes)}
    top = _MARGIN + _LANE_HEADER_HEIGHT
    positions = {
        step.id: _BoxPosition(
            x=_MARGIN + lane_index[step.lane] * _COL_WIDTH,  # type: ignore[index]
            y=top + i * _ROW_HEIGHT,
        )
        for i, step in enumerate(block.steps)
    }
    width = _MARGIN * 2 + len(block.lanes) * _COL_WIDTH
    height = top + max(len(block.steps), 1) * _ROW_HEIGHT - (_ROW_HEIGHT - _BOX_HEIGHT) + _MARGIN

    lane_header_svg = "".join(
        f'<rect x="{_MARGIN + i * _COL_WIDTH}" y="{_MARGIN}" '
        f'width="{_COL_WIDTH - 10}" height="{_LANE_HEADER_HEIGHT - 8}" '
        f'fill="#e8e8e8" stroke="#888"/>'
        f'<text x="{_MARGIN + i * _COL_WIDTH + (_COL_WIDTH - 10) / 2}" '
        f'y="{_MARGIN + (_LANE_HEADER_HEIGHT - 8) / 2 + 4}" '
        f'font-size="{_FONT_SIZE}" font-weight="bold" text-anchor="middle" '
        f'font-family="Times New Roman, Times, serif">{_escape(lane)}</text>'
        f'<line x1="{_MARGIN + i * _COL_WIDTH}" y1="{_MARGIN}" '
        f'x2="{_MARGIN + i * _COL_WIDTH}" y2="{height - _MARGIN}" '
        f'stroke="#ccc" stroke-dasharray="4,3"/>'
        for i, lane in enumerate(block.lanes)
    )
    lane_header_svg += (
        f'<line x1="{_MARGIN + len(block.lanes) * _COL_WIDTH}" y1="{_MARGIN}" '
        f'x2="{_MARGIN + len(block.lanes) * _COL_WIDTH}" y2="{height - _MARGIN}" '
        f'stroke="#ccc" stroke-dasharray="4,3"/>'
    )

    body = lane_header_svg + _render_boxes_and_arrows(block.steps, block.transitions, positions)
    return _wrap_svg(width, height, body)


def _render_boxes_and_arrows(
    steps: list[DiagramStep],
    transitions: list[DiagramTransition],
    positions: dict[str, _BoxPosition],
) -> str:
    boxes = "".join(_render_box(step, positions[step.id]) for step in steps)
    arrows = "".join(
        _render_arrow(positions[from_id], positions[to_id]) for from_id, to_id in transitions
    )
    # Boxes drawn after arrows so arrowheads don't overlap box borders.
    return arrows + boxes


def _render_box(step: DiagramStep, pos: _BoxPosition) -> str:
    lines = _wrap_text(step.label, _MAX_CHARS_PER_LINE)
    line_height = _FONT_SIZE + 4
    text_block_height = len(lines) * line_height
    first_line_y = pos.y + _BOX_HEIGHT / 2 - text_block_height / 2 + _FONT_SIZE
    tspans = "".join(
        f'<tspan x="{pos.x + _BOX_WIDTH / 2}" y="{first_line_y + i * line_height}">'
        f"{_escape(line)}</tspan>"
        for i, line in enumerate(lines)
    )
    return (
        f'<rect x="{pos.x}" y="{pos.y}" width="{_BOX_WIDTH}" height="{_BOX_HEIGHT}" '
        f'rx="6" fill="#fff" stroke="#333" stroke-width="1.5"/>'
        f'<text text-anchor="middle" font-size="{_FONT_SIZE}" '
        f'font-family="Times New Roman, Times, serif">{tspans}</text>'
    )


def _render_arrow(start: _BoxPosition, end: _BoxPosition) -> str:
    x1, y1 = start.x + _BOX_WIDTH / 2, start.y + _BOX_HEIGHT
    x2, y2 = end.x + _BOX_WIDTH / 2, end.y
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="#333" stroke-width="1.5" marker-end="url(#arrowhead)"/>'
    )


def _wrap_svg(width: float, height: float, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f"<defs><marker id=\"arrowhead\" markerWidth=\"8\" markerHeight=\"8\" "
        f'refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#333"/>'
        f"</marker></defs>"
        f"{body}</svg>"
    )


def _wrap_text(text: str, max_chars_per_line: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= max_chars_per_line:
            current += " " + word
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
