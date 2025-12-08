from __future__ import annotations
from typing import List
from jinja2 import Environment, PackageLoader, select_autoescape
from .types import Newsletter, SelectedItem

env = Environment(
    loader=PackageLoader("newsletter_agent", "prompts"),
    autoescape=select_autoescape(["html", "xml"])
)

def render_newsletter(subject: str, items: List[SelectedItem]) -> Newsletter:
    tpl = env.get_template("newsletter.html.jinja")
    html = tpl.render(subject=subject, items=items)
    text_lines = [subject, ""]
    for i, it in enumerate(items, start=1):
        text_lines += [
            f"{i}. {it.title} ({it.source})",
            f"   {it.url}",
            f"   Why it matters: {it.why_it_matters}",
            f"   Summary: {it.summary}",
            ""
        ]
    return Newsletter(subject=subject, html=html, text="\n".join(text_lines).strip(), items=items)
