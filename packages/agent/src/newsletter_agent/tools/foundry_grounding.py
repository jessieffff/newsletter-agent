from __future__ import annotations
from typing import List, Optional
import os
import re
import hashlib
from ..types import Candidate

def _stable_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]

async def grounded_search_via_foundry(query: str, freshness: str = "7d", count: int = 8) -> List[Candidate]:
    """
    Uses Azure AI Foundry Agents "Grounding with Bing Search" (via azure-ai-projects SDK) to get fresh links.
    Requires:
      - FOUNDRY_PROJECT_ENDPOINT
      - FOUNDRY_MODEL_DEPLOYMENT_NAME
      - FOUNDRY_BING_CONNECTION_ID
    """
    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
        from azure.ai.agents.models import BingGroundingTool
    except Exception as e:
        raise RuntimeError("Missing optional dependency. Install with: pip install 'newsletter-agent[azure_foundry]'") from e

    project_endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT") or os.environ.get("PROJECT_ENDPOINT")
    model = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT_NAME") or os.environ.get("MODEL_DEPLOYMENT_NAME")
    conn_id = os.environ.get("FOUNDRY_BING_CONNECTION_ID") or os.environ.get("BING_CONNECTION_ID")
    if not (project_endpoint and model and conn_id):
        raise RuntimeError("Foundry env vars not set: FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL_DEPLOYMENT_NAME, FOUNDRY_BING_CONNECTION_ID")

    project_client = AIProjectClient(endpoint=project_endpoint, credential=DefaultAzureCredential())
    bing = BingGroundingTool(connection_id=conn_id)

    # Create a lightweight agent+thread per call (simple + stateless).
    # For production, you can create one persistent agent and reuse it.
    with project_client:
        agent = project_client.agents.create_agent(
            model=model,
            name="grounding-search",
            instructions="Return a short list of the most relevant and recent links. Include the URL in each bullet.",
            tools=bing.definitions,
        )
        thread = project_client.agents.threads.create()
        project_client.agents.messages.create(thread_id=thread.id, role="user", content=f"Search latest: {query}")
        run = project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
        if run.status == "failed":
            raise RuntimeError(f"Foundry run failed: {run.last_error}")

        messages = list(project_client.agents.messages.list(thread_id=thread.id))
        # Grab the most recent assistant message (best-effort)
        text = ""
        for m in messages:
            if getattr(m, "role", None) == "assistant":
                # m.content can be structured; treat as string-ish
                text = str(m.content)
                break

        # Heuristic URL extraction (citations are in the model response too, but shape varies)
        urls = re.findall(r"https?://\S+", text)
        urls = [u.strip(").,]\"'") for u in urls]
        seen = set()
        out: List[Candidate] = []
        for u in urls:
            if u in seen:
                continue
            seen.add(u)
            out.append(Candidate(
                id=_stable_id(u),
                title=f"Link: {u}",
                url=u,
                source="Web (Foundry Grounding)",
                published_at=None,
                snippet=None,
                topic_tags=[query],
                raw={"foundry": {"freshness": freshness}},
            ))
            if len(out) >= count:
                break

        project_client.agents.delete_agent(agent.id)
        return out
