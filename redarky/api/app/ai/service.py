from collections import Counter, defaultdict

from app.models import DataItem


def researcher_agent(items: list[DataItem]) -> dict:
    source_counts = Counter(item.source for item in items)
    top_titles = [item.title for item in sorted(items, key=lambda i: i.score or 0, reverse=True)[:10] if item.title]
    return {
        "item_count": len(items),
        "source_distribution": dict(source_counts),
        "top_titles": top_titles,
    }


def gap_finder_agent(items: list[DataItem]) -> list[dict]:
    grouped: dict[str, list[DataItem]] = defaultdict(list)
    for item in items:
        grouped[item.classification or "general"].append(item)

    gaps: list[dict] = []
    for classification, group_items in grouped.items():
        avg_score = sum(i.score or 0 for i in group_items) / max(1, len(group_items))
        if avg_score >= 10:
            gaps.append(
                {
                    "title": f"High-demand gap in {classification}",
                    "description": f"Strong audience signal detected with average score {avg_score:.2f}.",
                    "confidence": min(0.95, 0.3 + (avg_score / 100)),
                    "evidence": [i.url for i in group_items[:5] if i.url],
                }
            )
    return gaps


def supervisor_agent(research_result: dict, gaps: list[dict]) -> dict:
    priority = "high" if gaps else "normal"
    return {
        "mission_health": "ready_for_report",
        "priority": priority,
        "research_summary": research_result,
        "gaps_found": len(gaps),
    }
