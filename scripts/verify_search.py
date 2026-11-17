"""Скрипт проверки поисковой выдачи калькуляторов в GUI."""

from mcp_calc.network_client import discover_calculators_sync
from mcp_calc.translations import (
    get_tool_keywords,
    translate_specialty,
    translate_tool_name,
    translate_tool_purpose,
)

res = discover_calculators_sync(by="tools", limit=250)
raw_tools = res.get("tools", [])
enriched = []

for t in raw_tools:
    tid = t["tool_id"]
    ru_name = translate_tool_name(tid, t.get("name", tid))
    ru_purpose = translate_tool_purpose(tid, t.get("purpose", ""))
    keywords = get_tool_keywords(tid)
    specialties = [translate_specialty(s) for s in t.get("specialties", [])] + t.get("specialties", [])

    search_corpus = " ".join([
        tid,
        t.get("name", ""),
        ru_name,
        t.get("purpose", ""),
        ru_purpose,
        " ".join(keywords),
        " ".join(specialties),
    ]).lower()

    item = dict(t)
    item["ru_name"] = ru_name
    item["ru_purpose"] = ru_purpose
    item["search_corpus"] = search_corpus
    enriched.append(item)

for query in ["инф", "инфаркт", "инфекция", "инфузия", "сепсис", "почки"]:
    words = query.lower().split()
    filtered = [t for t in enriched if all(w in t["search_corpus"] for w in words)]
    print(f"=== Поиск: '{query}' (найдено: {len(filtered)}) ===")
    for f in filtered[:6]:
        print(f"  • {f['tool_id']}: {f['ru_name']}")
    if len(filtered) > 6:
        print(f"  ... и ещё {len(filtered)-6} калькуляторов")
    print()
