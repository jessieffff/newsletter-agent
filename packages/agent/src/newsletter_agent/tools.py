"""LLM function calling tools for newsletter generation."""

from __future__ import annotations
import logging
from typing import List, Dict, Set
from urllib.parse import urlparse
from collections import Counter

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_openai import AzureChatOpenAI

from .types import (
    RankAndSelectInput,
    RankAndSelectOutput, 
    DraftNewsletterInput,
    DraftNewsletterOutput,
    CandidateForRanking,
    SelectedItemForDraft,
    DraftedItem,
    Candidate,
    Error,
    AgentState
)
from .settings import get_openai_settings
from .ranking import simple_rank


logger = logging.getLogger("newsletter_agent")


class RankAndSelectTool(BaseTool):
    """LLM tool for ranking and selecting newsletter candidates."""
    
    name: str = "rank_and_select"
    description: str = (
        "Select the best N candidates from a list using recency, topic relevance, and diversity. "
        "You must return only IDs that exist in the input candidates list. "
        "Respect max_per_domain constraints for source diversity."
    )
    
    class RankAndSelectSchema(BaseModel):
        """Input schema for rank_and_select tool."""
        topics: List[str] = Field(description="List of topics for the newsletter")
        target_count: int = Field(description="Number of items to select")
        max_per_domain: int = Field(default=2, description="Maximum items per domain")
        candidates: List[Dict] = Field(description="List of candidate items with id, title, url, source, etc.")
    
    args_schema = RankAndSelectSchema
    
    def _run(self, topics: List[str], target_count: int, max_per_domain: int, candidates: List[Dict]) -> Dict:
        """Execute the ranking and selection."""
        try:
            # Convert candidates to proper format
            candidate_objects = []
            for c in candidates:
                candidate_objects.append(CandidateForRanking(**c))
            
            # Create input model
            input_data = RankAndSelectInput(
                topics=topics,
                target_count=target_count,
                max_per_domain=max_per_domain,
                candidates=candidate_objects
            )
            
            # This will be replaced by actual LLM call
            # For now, implement fallback logic
            return self._fallback_selection(input_data)
            
        except Exception as e:
            logger.error(f"RankAndSelectTool execution failed: {e}")
            # Return empty selection that will trigger fallback
            return {"selected_ids": [], "reasons": {}, "rejected": []}
    
    def _fallback_selection(self, input_data: RankAndSelectInput) -> Dict:
        """Fallback selection using simple ranking."""
        # Convert to Candidate objects for simple_rank
        candidates = []
        for c in input_data.candidates:
            candidates.append(Candidate(
                id=c.id,
                title=c.title,
                url=c.url,
                source=c.source,
                published_at=c.published_at,
                snippet=c.snippet
            ))
        
        # Use simple ranking
        ranked = simple_rank(candidates)
        selected = ranked[:input_data.target_count]
        
        return {
            "selected_ids": [c.id for c in selected],
            "reasons": {c.id: "Selected by fallback ranking" for c in selected},
            "rejected": []
        }


class DraftNewsletterTool(BaseTool):
    """LLM tool for drafting newsletter content."""
    
    name: str = "draft_newsletter_items"
    description: str = (
        "Generate newsletter subject and per-item copy with structured output. "
        "You must preserve URLs exactly as provided and use only information from the input items. "
        "Keep summaries concise and factual."
    )
    
    class DraftNewsletterSchema(BaseModel):
        """Input schema for draft_newsletter_items tool."""
        tone: str = Field(description="Tone for the newsletter content")
        max_summary_sentences: int = Field(default=3, description="Maximum sentences per summary")
        items: List[Dict] = Field(description="List of selected items to draft")
    
    args_schema = DraftNewsletterSchema
    
    def _run(self, tone: str, max_summary_sentences: int, items: List[Dict]) -> Dict:
        """Execute the newsletter drafting."""
        try:
            # Convert items to proper format
            item_objects = []
            for item in items:
                item_objects.append(SelectedItemForDraft(**item))
            
            # Create input model
            input_data = DraftNewsletterInput(
                tone=tone,
                max_summary_sentences=max_summary_sentences,
                items=item_objects
            )
            
            # This will be replaced by actual LLM call
            # For now, implement fallback logic
            return self._fallback_drafting(input_data)
            
        except Exception as e:
            logger.error(f"DraftNewsletterTool execution failed: {e}")
            # Return empty draft that will trigger fallback
            return {"subject": "", "items": []}
    
    def _fallback_drafting(self, input_data: DraftNewsletterInput) -> Dict:
        """Fallback drafting with basic templates."""
        drafted_items = []
        
        for item in input_data.items:
            # Create basic draft
            drafted_items.append({
                "id": item.id,
                "title": item.title,
                "source": item.source,
                "url": item.url,
                "why_it_matters": "This story provides important insights for our readers.",
                "summary": item.snippet[:200] + "..." if item.snippet and len(item.snippet) > 200 else (item.snippet or "Summary not available.")
            })
        
        return {
            "subject": "Newsletter Update",
            "items": drafted_items
        }


def extract_domain(url: str) -> str:
    """Extract domain from URL for diversity checking."""
    try:
        parsed = urlparse(str(url))
        return parsed.netloc.lower()
    except Exception:
        return "unknown"


def enforce_max_per_domain(selected_ids: List[str], candidates: List[CandidateForRanking], 
                          max_per_domain: int, target_count: int) -> List[str]:
    """Enforce max_per_domain constraint and fill remaining slots."""
    # Build domain mapping
    id_to_candidate = {c.id: c for c in candidates}
    domain_counts = Counter()
    final_selection = []
    
    # First pass: add items respecting domain limits
    for item_id in selected_ids:
        if item_id not in id_to_candidate:
            continue
            
        candidate = id_to_candidate[item_id]
        domain = extract_domain(candidate.url)
        
        if domain_counts[domain] < max_per_domain:
            final_selection.append(item_id)
            domain_counts[domain] += 1
    
    # Second pass: fill remaining slots with unselected candidates
    if len(final_selection) < target_count:
        unselected = [c for c in candidates if c.id not in final_selection]
        # Sort by simple ranking
        candidate_objs = []
        for c in unselected:
            candidate_objs.append(Candidate(
                id=c.id,
                title=c.title,
                url=c.url,
                source=c.source,
                published_at=c.published_at,
                snippet=c.snippet
            ))
        
        ranked_unselected = simple_rank(candidate_objs)
        
        for candidate in ranked_unselected:
            if len(final_selection) >= target_count:
                break
                
            domain = extract_domain(candidate.url)
            if domain_counts[domain] < max_per_domain:
                final_selection.append(candidate.id)
                domain_counts[domain] += 1
    
    return final_selection[:target_count]


def validate_rank_and_select_output(output: Dict, input_candidates: List[CandidateForRanking], 
                                   target_count: int) -> tuple[bool, str]:
    """Validate rank_and_select tool output."""
    try:
        # Check required fields
        if "selected_ids" not in output:
            return False, "missing selected_ids field"
        
        selected_ids = output["selected_ids"]
        
        # Check type and uniqueness
        if not isinstance(selected_ids, list):
            return False, "selected_ids must be a list"
        
        if len(set(selected_ids)) != len(selected_ids):
            return False, "selected_ids contains duplicates"
        
        # Check count
        if len(selected_ids) > target_count:
            return False, f"selected too many items: {len(selected_ids)} > {target_count}"
        
        # Check all IDs exist
        valid_ids = {c.id for c in input_candidates}
        invalid_ids = set(selected_ids) - valid_ids
        if invalid_ids:
            return False, f"invalid ids: {invalid_ids}"
        
        return True, ""
        
    except Exception as e:
        return False, f"validation error: {e}"


def validate_draft_newsletter_output(output: Dict, input_items: List[SelectedItemForDraft]) -> tuple[bool, str]:
    """Validate draft_newsletter_items tool output."""
    try:
        # Check required fields
        if "subject" not in output or "items" not in output:
            return False, "missing required fields (subject, items)"
        
        if not isinstance(output["items"], list):
            return False, "items must be a list"
        
        # Build input mapping
        input_by_id = {item.id: item for item in input_items}
        
        # Validate each item
        for item in output["items"]:
            if not isinstance(item, dict):
                return False, "each item must be a dict"
            
            item_id = item.get("id")
            if item_id not in input_by_id:
                return False, f"invalid item id: {item_id}"
            
            # Check URL integrity
            input_item = input_by_id[item_id]
            if item.get("url") != input_item.url:
                return False, f"URL mismatch for id {item_id}"
        
        return True, ""
        
    except Exception as e:
        return False, f"validation error: {e}"


async def llm_rank_and_select(topics: List[str], target_count: int, max_per_domain: int,
                             candidates: List[CandidateForRanking], state: AgentState) -> tuple[List[str], bool, str]:
    """
    Use LLM to rank and select candidates with fallback to simple_rank.
    
    Returns:
        tuple of (selected_ids, used_llm, fallback_reason)
    """
    try:
        # Build LLM client
        settings = get_openai_settings()
        llm = AzureChatOpenAI(
            azure_endpoint=settings.endpoint,
            api_key=settings.api_key,
            api_version=settings.api_version,
            azure_deployment=settings.deployment,
            temperature=settings.temperature,
            timeout=settings.timeout,
        )
        
        # Create structured output using Pydantic model
        structured_llm = llm.with_structured_output(RankAndSelectOutput)
        
        # Create prompt
        system_msg = (
            "You are an expert newsletter curator. Select the best items from the candidates "
            "considering recency, topic relevance to the given topics, and source diversity. "
            f"You must select up to {target_count} items. Try to respect the max_per_domain limit of {max_per_domain}. "
            "Return only IDs that exist in the candidate list. Do not modify URLs or invent content. "
            "Provide selected_ids as a list of strings, and reasons as a dictionary mapping each selected ID to a brief reason."
        )
        
        candidate_summary = []
        for i, c in enumerate(candidates):
            candidate_summary.append(
                f"ID: {c.id}\n"
                f"Title: {c.title}\n"
                f"Source: {c.source}\n"
                f"URL: {c.url}\n"
                f"Published: {c.published_at or 'Unknown'}\n"
                f"Snippet: {(c.snippet or 'No snippet')[:200]}...\n"
            )
        
        user_msg = (
            f"Topics of interest: {', '.join(topics)}\n"
            f"Target count: {target_count}\n"
            f"Max per domain: {max_per_domain}\n\n"
            f"Candidates:\n" + "\n---\n".join(candidate_summary)
        )
        
        # Make LLM call with structured output
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=user_msg)
        ]
        
        result = await structured_llm.ainvoke(messages)
        
        # Validate output
        result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
        is_valid, error_msg = validate_rank_and_select_output(result_dict, candidates, target_count)
        
        if is_valid:
            selected_ids = result_dict["selected_ids"]
            # Enforce domain constraints
            final_ids = enforce_max_per_domain(selected_ids, candidates, max_per_domain, target_count)
            return final_ids, True, ""
        else:
            return await _fallback_rank_and_select(candidates, target_count, state), False, f"invalid_output: {error_msg}"
            
    except Exception as e:
        logger.error(f"LLM rank_and_select failed: {e}")
        return await _fallback_rank_and_select(candidates, target_count, state), False, f"tool_error: {str(e)}"


async def llm_draft_newsletter_items(tone: str, max_summary_sentences: int, 
                                   items: List[SelectedItemForDraft], state: AgentState) -> tuple[Dict, bool, str]:
    """
    Use LLM to draft newsletter content with fallback.
    
    Returns:
        tuple of (draft_output, used_llm, fallback_reason)
    """
    try:
        # Build LLM client
        settings = get_openai_settings()
        llm = AzureChatOpenAI(
            azure_endpoint=settings.endpoint,
            api_key=settings.api_key,
            api_version=settings.api_version,
            azure_deployment=settings.deployment,
            temperature=settings.temperature,
            timeout=settings.timeout,
        )
        
        # Create structured output using Pydantic model
        structured_llm = llm.with_structured_output(DraftNewsletterOutput)
        
        # Create prompt
        system_msg = (
            "You are an expert newsletter editor. Generate a compelling newsletter subject line "
            f"and draft content for each item in the specified tone: {tone}. "
            f"Keep summaries to {max_summary_sentences} sentences maximum. "
            "Use only information supported by the title and snippet. Do not invent facts. "
            "Preserve URLs exactly as provided. Each 'why_it_matters' should be exactly 1 sentence. "
            "Return the response in the exact format: subject (string) and items (list of objects with id, title, source, url, why_it_matters, summary)."
        )
        
        items_summary = []
        for item in items:
            items_summary.append(
                f"ID: {item.id}\n"
                f"Title: {item.title}\n"
                f"Source: {item.source}\n"
                f"URL: {item.url}\n"
                f"Published: {item.published_at or 'Unknown'}\n"
                f"Snippet: {(item.snippet or 'No snippet available')[:300]}...\n"
            )
        
        user_msg = (
            f"Newsletter tone: {tone}\n"
            f"Max summary sentences: {max_summary_sentences}\n\n"
            f"Items to draft:\n" + "\n---\n".join(items_summary)
        )
        
        # Make LLM call with structured output
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=user_msg)
        ]
        
        result = await structured_llm.ainvoke(messages)
        
        # Validate output
        result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
        is_valid, error_msg = validate_draft_newsletter_output(result_dict, items)
        
        if is_valid:
            return result_dict, True, ""
        else:
            return _fallback_draft_newsletter_items(items, tone), False, f"invalid_output: {error_msg}"
            
    except Exception as e:
        logger.error(f"LLM draft_newsletter_items failed: {e}")
        return _fallback_draft_newsletter_items(items, tone), False, f"tool_error: {str(e)}"


async def _fallback_rank_and_select(candidates: List[CandidateForRanking], target_count: int, 
                                  state: AgentState) -> List[str]:
    """Fallback ranking using simple_rank."""
    # Convert to Candidate objects
    candidate_objs = []
    for c in candidates:
        candidate_objs.append(Candidate(
            id=c.id,
            title=c.title,
            url=c.url,
            source=c.source,
            published_at=c.published_at,
            snippet=c.snippet
        ))
    
    ranked = simple_rank(candidate_objs)
    selected = ranked[:target_count]
    return [c.id for c in selected]


def _fallback_draft_newsletter_items(items: List[SelectedItemForDraft], tone: str) -> Dict:
    """Fallback drafting with basic templates."""
    drafted_items = []
    
    for item in items:
        # Create basic draft
        summary = item.snippet[:300] + "..." if item.snippet and len(item.snippet) > 300 else (item.snippet or "Summary not available.")
        
        drafted_items.append({
            "id": item.id,
            "title": item.title,
            "source": item.source,
            "url": item.url,
            "why_it_matters": "This story provides important updates for our readers.",
            "summary": summary
        })
    
    return {
        "subject": "Newsletter Update - Latest News",
        "items": drafted_items
    }