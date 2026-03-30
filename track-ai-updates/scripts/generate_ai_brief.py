import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

USER_AGENT = "Mozilla/5.0 (compatible; track-ai-updates/1.0; +https://openai.com)"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
MAX_SUMMARY = 180


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="抓取配置中的 RSS/Atom 源，并生成中文 AI 动态 HTML 简报。"
    )
    parser.add_argument("--config", type=Path, help="JSON 配置文件路径")
    parser.add_argument("--output", type=Path, help="输出 HTML 文件路径")
    parser.add_argument("--output-dir", type=Path, help="输出目录；脚本会自动按日期命名 HTML 文件")
    parser.add_argument("--filename-prefix", default="ai-brief", help="自动命名时的文件名前缀，默认 ai-brief")
    parser.add_argument("--days", type=int, default=7, help="仅保留最近 N 天内容，默认 7")
    parser.add_argument("--max-items", type=int, default=18, help="最终最多保留的条目数，默认 18")
    parser.add_argument("--demo", action="store_true", help="使用内置示例数据生成演示页面")
    args = parser.parse_args()
    if not args.output and not args.output_dir:
        parser.error("必须提供 --output 或 --output-dir 之一")
    return args


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_text(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def strip_html(raw: str | None) -> str:
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def shorten(text: str, limit: int = MAX_SUMMARY) -> str:
    text = strip_html(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def parse_date(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    value = value.strip()
    candidates = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ]
    for fmt in candidates:
        try:
            parsed = dt.datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=dt.timezone.utc)
            return parsed
        except ValueError:
            continue
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=dt.timezone.utc)
        return parsed
    except ValueError:
        return None


def parse_rss(xml_text: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    items: list[dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "无标题").strip()
        link = (item.findtext("link") or source.get("url") or "").strip()
        summary = item.findtext("description") or item.findtext("content") or ""
        published = parse_date(item.findtext("pubDate") or item.findtext("published"))
        items.append(
            {
                "title": title,
                "link": link,
                "summary": shorten(summary),
                "published": published,
                "platform": source.get("platform", source.get("name", "未知来源")),
                "source_name": source.get("name", "未命名来源"),
                "priority": int(source.get("priority", 1)),
            }
        )
    return items


def parse_atom(xml_text: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    items: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title = (entry.findtext("atom:title", default="无标题", namespaces=ATOM_NS) or "无标题").strip()
        link = source.get("url") or ""
        link_node = entry.find("atom:link", ATOM_NS)
        if link_node is not None and link_node.attrib.get("href"):
            link = link_node.attrib["href"].strip()
        summary = (
            entry.findtext("atom:summary", default="", namespaces=ATOM_NS)
            or entry.findtext("atom:content", default="", namespaces=ATOM_NS)
            or ""
        )
        published = parse_date(
            entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
            or entry.findtext("atom:published", default="", namespaces=ATOM_NS)
        )
        items.append(
            {
                "title": title,
                "link": link,
                "summary": shorten(summary),
                "published": published,
                "platform": source.get("platform", source.get("name", "未知来源")),
                "source_name": source.get("name", "未命名来源"),
                "priority": int(source.get("priority", 1)),
            }
        )
    return items


def collect_items(config: dict[str, Any], days: int) -> tuple[list[dict[str, Any]], list[str]]:
    threshold = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    keywords = [k.lower() for k in config.get("keywords", []) if k.strip()]
    items: list[dict[str, Any]] = []
    errors: list[str] = []

    for source in config.get("sources", []):
        source_type = (source.get("type") or "rss").lower()
        url = source.get("url")
        if not url:
            errors.append(f"来源 {source.get('name', '未命名来源')} 缺少 url")
            continue
        try:
            xml_text = fetch_text(url)
            parsed = parse_atom(xml_text, source) if source_type == "atom" else parse_rss(xml_text, source)
        except (urllib.error.URLError, TimeoutError, ET.ParseError, ValueError) as exc:
            errors.append(f"{source.get('name', url)} 抓取失败: {exc}")
            continue

        for item in parsed:
            if item["published"] and item["published"] < threshold:
                continue
            haystack = f"{item['title']} {item['summary']}".lower()
            score = item["priority"] * 10
            if keywords:
                matches = sum(1 for keyword in keywords if keyword in haystack)
                if matches == 0 and source.get("keyword_strict"):
                    continue
                score += matches * 4
            if any(token in haystack for token in ["release", "launch", "model", "agent", "benchmark", "space"]):
                score += 2
            item["score"] = score
            items.append(item)

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    min_dt = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    for item in sorted(items, key=lambda x: (x.get("published") or min_dt, x["score"]), reverse=True):
        key = (item["link"] or item["title"]).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped, errors


def demo_items() -> tuple[list[dict[str, Any]], list[str]]:
    now = dt.datetime.now(dt.timezone.utc)
    items = [
        {
            "title": "推理模型新版本开放测试",
            "link": "https://example.com/reasoning-model",
            "summary": "某团队开放了更长上下文和更稳定工具调用的新模型测试入口，社区重点关注编码与复杂推理表现。",
            "published": now - dt.timedelta(hours=6),
            "platform": "官方博客",
            "source_name": "示例实验室",
            "priority": 3,
            "score": 32,
        },
        {
            "title": "Hugging Face 上线新的 Agent Demo Space",
            "link": "https://huggingface.co/spaces/example/agent-demo",
            "summary": "该 Space 演示了浏览器操作与多工具编排能力，短时间内获得较高关注。",
            "published": now - dt.timedelta(days=1, hours=2),
            "platform": "Hugging Face",
            "source_name": "Hugging Face Spaces",
            "priority": 2,
            "score": 24,
        },
        {
            "title": "开源视频生成仓库发布首个稳定版本",
            "link": "https://github.com/example/video-gen/releases/tag/v1.0.0",
            "summary": "仓库新增推理脚本、示例视频与部署文档，说明项目开始从实验演示走向可复现使用。",
            "published": now - dt.timedelta(days=2),
            "platform": "GitHub",
            "source_name": "GitHub Releases",
            "priority": 2,
            "score": 22,
        },
    ]
    return items, []


def format_date(value: dt.datetime | None) -> str:
    if value is None:
        return "日期未知"
    return value.astimezone().strftime("%Y-%m-%d")


def build_summary(items: list[dict[str, Any]]) -> str:
    if not items:
        return "本期未抓取到符合条件的 AI 动态。"
    top = items[0]
    return f"最近的高信号动态主要集中在 {top['platform']} 等渠道，重点围绕模型发布、能力升级和开源工具演进。"


def resolve_output_path(args: argparse.Namespace, now: dt.datetime) -> Path:
    if args.output:
        return args.output
    filename = f"{args.filename_prefix}-{now.strftime('%Y-%m-%d')}.html"
    return args.output_dir / filename


def render_item(item: dict[str, Any], compact: bool = False) -> str:
    title_html = html.escape(item["title"])
    summary_html = html.escape(item["summary"])
    link_html = html.escape(item["link"])
    platform_html = html.escape(item["platform"])
    source_html = html.escape(item["source_name"])
    date_html = html.escape(format_date(item["published"]))
    class_name = "timeline-item compact" if compact else "timeline-item"
    return f"""
    <article class=\"{class_name}\">
      <div class=\"tag\">{date_html} · {platform_html}</div>
      <h3>{title_html}</h3>
      <p class=\"muted\">{summary_html}</p>
      <div class=\"meta-line\">来源：{source_html}</div>
      <a class=\"source-link\" href=\"{link_html}\" target=\"_blank\" rel=\"noreferrer\">查看来源</a>
    </article>
    """


def render_html(config: dict[str, Any], items: list[dict[str, Any]], errors: list[str], generated_at: dt.datetime) -> str:
    title = config.get("title") or "AI 动态中文简报"
    subtitle = config.get("subtitle") or build_summary(items)
    period = config.get("period") or (
        f"{format_date(items[-1]['published'])} 至 {format_date(items[0]['published'])}" if items else "最近一段时间"
    )
    top_items = items[:3]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(item["platform"], []).append(item)

    key_signal_html = "\n".join(render_item(item, compact=True) for item in top_items)
    timeline_html = "\n".join(render_item(item) for item in items)
    platform_sections = []
    for platform, group_items in grouped.items():
        block = "\n".join(render_item(item, compact=True) for item in group_items[:4])
        platform_sections.append(
            f"<section class=\"platform-block\"><h3>{html.escape(platform)}</h3><div class=\"platform-list\">{block}</div></section>"
        )
    platform_html = "\n".join(platform_sections) or "<p class=\"muted\">暂无平台数据。</p>"
    error_html = "".join(f"<li>{html.escape(err)}</li>" for err in errors)
    error_block = (
        f"<section><h2 class=\"section-title\">抓取备注</h2><ul class=\"notes\">{error_html}</ul></section>"
        if errors
        else ""
    )
    count = len(items)
    source_count = len(config.get("sources", [])) if config.get("sources") else len(grouped)
    generated_text = generated_at.strftime("%Y-%m-%d %H:%M %Z")
    timeline_fallback = '<p class="muted">暂无符合条件的条目。</p>'

    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #0a0d12;
      --panel: rgba(255,255,255,0.04);
      --panel-strong: rgba(255,255,255,0.06);
      --text: #f5f7fb;
      --muted: #99a4b3;
      --accent: #67e8f9;
      --accent-2: #fbbf24;
      --line: rgba(255,255,255,0.12);
      --max: 1180px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--text);
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(103,232,249,0.18), transparent 25%),
        radial-gradient(circle at 85% 0%, rgba(251,191,36,0.10), transparent 30%),
        linear-gradient(180deg, #0a0d12 0%, #0f141b 100%);
    }}
    a {{ color: inherit; text-decoration: none; }}
    .page {{ max-width: var(--max); margin: 0 auto; padding: 28px 18px 64px; }}
    .hero {{ padding: 54px 0 28px; border-bottom: 1px solid var(--line); }}
    .eyebrow {{ display: inline-flex; padding: 7px 12px; border: 1px solid var(--line); border-radius: 999px; color: var(--accent); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; }}
    h1 {{ margin: 18px 0 14px; font-size: clamp(38px, 7vw, 76px); line-height: .95; letter-spacing: -0.05em; max-width: 10ch; }}
    .lead {{ max-width: 760px; color: var(--muted); font-size: 18px; line-height: 1.75; }}
    .meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-top: 28px; }}
    .meta-item {{ background: var(--panel); border: 1px solid var(--line); padding: 14px 16px; }}
    section {{ padding-top: 30px; }}
    .section-title {{ margin: 0 0 16px; font-size: 25px; letter-spacing: -0.03em; }}
    .signals, .platform-columns {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
    .timeline {{ display: grid; gap: 14px; }}
    .timeline-item {{ background: var(--panel); border: 1px solid var(--line); padding: 18px; transition: transform .18s ease, border-color .18s ease, background .18s ease; }}
    .timeline-item:hover {{ transform: translateY(-2px); border-color: rgba(103,232,249,0.4); background: var(--panel-strong); }}
    .timeline-item.compact {{ min-height: 100%; }}
    .timeline-item h3 {{ margin: 0 0 10px; font-size: 20px; line-height: 1.25; }}
    .tag {{ display: inline-block; margin-bottom: 10px; color: var(--accent-2); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; }}
    .muted {{ color: var(--muted); line-height: 1.7; }}
    .meta-line {{ margin-top: 12px; color: var(--muted); font-size: 13px; }}
    .source-link {{ display: inline-block; margin-top: 14px; color: var(--accent); font-size: 14px; }}
    .platform-block {{ border-top: 1px solid var(--line); padding-top: 14px; }}
    .platform-block h3 {{ margin: 0 0 12px; font-size: 20px; }}
    .platform-list {{ display: grid; gap: 12px; }}
    .notes {{ margin: 0; padding-left: 20px; color: var(--muted); line-height: 1.7; }}
    footer {{ margin-top: 46px; padding-top: 18px; border-top: 1px solid var(--line); color: var(--muted); font-size: 14px; }}
    @media (max-width: 640px) {{
      .page {{ padding: 20px 16px 48px; }}
      .hero {{ padding-top: 34px; }}
      .lead {{ font-size: 16px; }}
    }}
  </style>
</head>
<body>
  <main class=\"page\">
    <header class=\"hero\">
      <span class=\"eyebrow\">AI Tracking Brief</span>
      <h1>{html.escape(title)}</h1>
      <p class=\"lead\">{html.escape(subtitle)}</p>
      <div class=\"meta-grid\">
        <div class=\"meta-item\"><strong>时间范围</strong><div class=\"muted\">{html.escape(period)}</div></div>
        <div class=\"meta-item\"><strong>收录条目</strong><div class=\"muted\">{count} 条</div></div>
        <div class=\"meta-item\"><strong>抓取来源</strong><div class=\"muted\">{source_count} 个</div></div>
      </div>
    </header>

    <section>
      <h2 class=\"section-title\">重点摘要</h2>
      <div class=\"signals\">{key_signal_html}</div>
    </section>

    <section>
      <h2 class=\"section-title\">动态时间线</h2>
      <div class=\"timeline\">{timeline_html or timeline_fallback}</div>
    </section>

    <section>
      <h2 class=\"section-title\">平台分布</h2>
      <div class=\"platform-columns\">{platform_html}</div>
    </section>

    {error_block}

    <footer>生成时间：{html.escape(generated_text)}。建议对关键结论继续回到原始链接核实。</footer>
  </main>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    if not args.demo and not args.config:
        print("错误：请提供 --config，或使用 --demo 生成演示页面。", file=sys.stderr)
        return 2

    config = load_config(args.config)
    if args.demo:
        items, errors = demo_items()
        config.setdefault("title", "AI 动态简报 Demo")
        config.setdefault("subtitle", "这是一个离线演示页面，用于验证 HTML 输出链路。")
    else:
        items, errors = collect_items(config, args.days)

    min_dt = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    items = sorted(
        items,
        key=lambda x: (x.get("published") or min_dt, x.get("score", 0)),
        reverse=True,
    )[: args.max_items]

    now = dt.datetime.now().astimezone()
    output_path = resolve_output_path(args, now)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_html(config, items, errors, generated_at=now),
        encoding="utf-8",
    )
    print(f"已生成 HTML 简报: {output_path}")
    if errors:
        print("部分来源抓取失败：")
        for err in errors:
            print(f"- {err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
