"""ECharts 关系图谱数据格式化工具。

该模块只负责把人物、关系、社交网络数据转换为 ECharts force graph
可直接使用的 nodes、links、categories 结构，不参与人物统计计算。
"""

from __future__ import annotations

from collections import Counter
from math import sqrt
from typing import Any


def normalize_node_size(value: int | float, min_size: int = 18, max_size: int = 68) -> int:
    """根据节点权重计算 ECharts 节点大小。"""
    if value <= 0:
        return min_size
    size = int(sqrt(value) * 2.4)
    return max(min_size, min(max_size, size))


def build_categories(nodes: list[dict[str, Any]], category_key: str = "category") -> list[dict[str, str]]:
    """根据节点中的分类字段生成 ECharts categories。"""
    category_names = []
    for node in nodes:
        category = node.get(category_key) or "其他"
        if category not in category_names:
            category_names.append(category)
    return [{"name": category} for category in category_names]


def format_graph_node(
    name: str,
    value: int | float = 0,
    category: str = "其他",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """格式化单个人物节点，适配 ECharts graph series.data。"""
    node = {
        "name": name,
        "value": value,
        "category": category,
        "symbolSize": normalize_node_size(value),
        "label": {"show": True},
    }
    if extra:
        node.update(extra)
    return node


def format_graph_link(
    source: str,
    target: str,
    value: int | float = 1,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """格式化单条人物关系边，适配 ECharts graph series.links。"""
    link = {
        "source": source,
        "target": target,
        "value": value,
        "lineStyle": {"width": max(1, min(8, int(value)))},
    }
    if extra:
        link.update(extra)
    return link


def format_force_graph(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    category_key: str = "category",
) -> dict[str, Any]:
    """封装完整 ECharts 力导向图数据结构。"""
    formatted_nodes = [
        format_graph_node(
            name=node["name"],
            value=node.get("value", 0),
            category=node.get(category_key, "其他"),
            extra={key: value for key, value in node.items() if key not in {"name", "value", category_key}},
        )
        for node in nodes
    ]
    formatted_links = [
        format_graph_link(
            source=link["source"],
            target=link["target"],
            value=link.get("value", 1),
            extra={key: value for key, value in link.items() if key not in {"source", "target", "value"}},
        )
        for link in links
    ]
    return {
        "nodes": formatted_nodes,
        "links": formatted_links,
        "categories": build_categories(formatted_nodes, category_key=category_key),
    }


def build_relation_links_from_chapter_names(chapter_name_groups: list[list[str]]) -> list[dict[str, Any]]:
    """根据每章出现的人物名称列表生成人物共现关系边。"""
    relation_counter: Counter[tuple[str, str]] = Counter()
    for names in chapter_name_groups:
        unique_names = sorted(set(names))
        for index, source in enumerate(unique_names):
            for target in unique_names[index + 1:]:
                relation_counter[(source, target)] += 1
    return [
        format_graph_link(source=source, target=target, value=value)
        for (source, target), value in relation_counter.most_common()
    ]


def build_social_graph(
    character_records: list[dict[str, Any]],
    relation_links: list[dict[str, Any]],
    family_key: str = "family",
) -> dict[str, Any]:
    """将人物记录和关系边转换为社交网络图数据。"""
    nodes = [
        {
            "name": item["name"],
            "value": item.get("mentionCount", item.get("value", 0)),
            "category": item.get(family_key, "其他"),
            "role": item.get("role", ""),
        }
        for item in character_records
    ]
    return format_force_graph(nodes, relation_links)

