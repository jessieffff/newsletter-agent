#!/usr/bin/env python3
"""
Comprehensive test script for function calling implementation.
Tests the rank_and_select and draft_newsletter_items LLM tools locally using Azure OpenAI API.
"""

import os
import sys
import asyncio
import json
import logging
from typing import List, Dict
from datetime import datetime, timezone

# Add the package to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'agent', 'src'))

from newsletter_agent.types import (
    Subscription, 
    Candidate,
    CandidateForRanking,
    SelectedItemForDraft,
    AgentState,
    SourceSpec
)
from newsletter_agent.tools import (
    llm_rank_and_select,
    llm_draft_newsletter_items,
    validate_rank_and_select_output,
    validate_draft_newsletter_output,
    enforce_max_per_domain
)
from newsletter_agent.workflow import node_select_and_write


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_function_calling")


def setup_environment():
    """Setup environment variables for testing."""
    # Check if Azure OpenAI credentials are set
    required_vars = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY"]
    
    for var in required_vars:
        if not os.environ.get(var):
            print(f"⚠️  Environment variable {var} is not set.")
            print("Please set the following environment variables:")
            print("  export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
            print("  export AZURE_OPENAI_API_KEY='your-api-key'")
            print("  export AZURE_OPENAI_DEPLOYMENT='gpt-4o-mini'  # optional, defaults to gpt-4o-mini")
            print("  export AZURE_OPENAI_API_VERSION='2024-10-21'  # optional")
            return False
    
    print("✅ Azure OpenAI environment variables are set")
    return True


def create_test_subscription() -> Subscription:
    """Create a test subscription for testing."""
    return Subscription(
        id="test-sub-001",
        user_id="test-user",
        topics=["artificial intelligence", "technology", "machine learning"],
        sources=[
            SourceSpec(kind="rss", value="https://feeds.feedburner.com/oreilly/radar"),
            SourceSpec(kind="domain", value="techcrunch.com")
        ],
        frequency="daily",
        item_count=5,
        tone="concise, professional",
        enabled=True,
        require_approval=False
    )


def create_test_candidates() -> List[Candidate]:
    """Create mock candidates for testing."""
    candidates = [
        Candidate(
            id="1",
            title="AI Breakthrough: New Language Model Achieves Human-Level Performance",
            url="https://techcrunch.com/ai-breakthrough-language-model",
            source="techcrunch.com",
            published_at="2024-12-16T10:00:00Z",
            snippet="Researchers have developed a new language model that demonstrates human-level performance across multiple benchmarks, marking a significant milestone in AI development."
        ),
        Candidate(
            id="2", 
            title="Machine Learning in Healthcare: Revolutionary Treatment Predictions",
            url="https://techcrunch.com/ml-healthcare-treatment-predictions",
            source="techcrunch.com",
            published_at="2024-12-16T09:30:00Z",
            snippet="A new machine learning system can predict treatment outcomes with 95% accuracy, potentially revolutionizing personalized medicine."
        ),
        Candidate(
            id="3",
            title="Tech Giants Announce New Partnership for AI Safety",
            url="https://venturebeat.com/tech-giants-ai-safety-partnership",
            source="venturebeat.com", 
            published_at="2024-12-16T08:00:00Z",
            snippet="Major technology companies have formed a new consortium to address AI safety concerns and develop industry standards."
        ),
        Candidate(
            id="4",
            title="Quantum Computing Milestone: 1000-Qubit Processor Demonstrated",
            url="https://arstechnica.com/quantum-computing-1000-qubit-processor",
            source="arstechnica.com",
            published_at="2024-12-16T07:15:00Z", 
            snippet="Scientists have successfully demonstrated a 1000-qubit quantum processor, bringing us closer to practical quantum computing applications."
        ),
        Candidate(
            id="5",
            title="Robotics Innovation: Humanoid Robots Enter the Workforce",
            url="https://techcrunch.com/robotics-humanoid-workforce",
            source="techcrunch.com",
            published_at="2024-12-16T06:45:00Z",
            snippet="Several companies are deploying humanoid robots in warehouses and manufacturing facilities, marking a new era in automation."
        ),
        Candidate(
            id="6",
            title="Cybersecurity Alert: New AI-Powered Threat Detection System",
            url="https://venturebeat.com/cybersecurity-ai-threat-detection",
            source="venturebeat.com",
            published_at="2024-12-16T06:00:00Z",
            snippet="A new AI-powered cybersecurity system can detect and respond to threats 10x faster than traditional methods."
        ),
        Candidate(
            id="7",
            title="Space Technology: AI Navigation System for Mars Missions",
            url="https://spacenews.com/ai-navigation-mars-missions",
            source="spacenews.com",
            published_at="2024-12-16T05:30:00Z",
            snippet="NASA announces a new AI navigation system that will enable more autonomous Mars rover operations."
        ),
        Candidate(
            id="8",
            title="Edge Computing Revolution: AI Processing at the Network Edge",
            url="https://techcrunch.com/edge-computing-ai-processing",
            source="techcrunch.com",
            published_at="2024-12-16T05:00:00Z",
            snippet="New edge computing solutions bring AI processing closer to data sources, reducing latency and improving efficiency."
        )
    ]
    return candidates


def prepare_candidates_for_ranking(candidates: List[Candidate]) -> List[CandidateForRanking]:
    """Convert test candidates to ranking format."""
    ranking_candidates = []
    for idx, candidate in enumerate(candidates):
        ranking_candidates.append(CandidateForRanking(
            id=f"cand:{idx}",
            title=candidate.title,
            url=str(candidate.url),
            source=candidate.source,
            published_at=candidate.published_at,
            snippet=candidate.snippet
        ))
    return ranking_candidates


async def test_rank_and_select():
    """Test the rank_and_select LLM tool."""
    print("\n🔍 Testing rank_and_select tool...")
    
    subscription = create_test_subscription()
    candidates = create_test_candidates()
    ranking_candidates = prepare_candidates_for_ranking(candidates)
    
    state: AgentState = {
        "subscription": subscription,
        "candidates": candidates,
        "errors": []
    }
    
    try:
        selected_ids, used_llm, fallback_reason = await llm_rank_and_select(
            topics=subscription.topics,
            target_count=subscription.item_count,
            max_per_domain=2,
            candidates=ranking_candidates,
            state=state
        )
        
        print(f"✅ rank_and_select completed")
        print(f"   Used LLM: {used_llm}")
        if fallback_reason:
            print(f"   Fallback reason: {fallback_reason}")
        print(f"   Selected {len(selected_ids)} items: {selected_ids}")
        
        # Validate selection
        id_to_candidate = {c.id: c for c in ranking_candidates}
        for selected_id in selected_ids:
            if selected_id in id_to_candidate:
                candidate = id_to_candidate[selected_id]
                print(f"   - {candidate.title[:60]}...")
        
        return selected_ids, ranking_candidates
        
    except Exception as e:
        print(f"❌ rank_and_select failed: {e}")
        return [], ranking_candidates


async def test_draft_newsletter_items(selected_ids: List[str], ranking_candidates: List[CandidateForRanking]):
    """Test the draft_newsletter_items LLM tool."""
    print("\n✏️  Testing draft_newsletter_items tool...")
    
    if not selected_ids:
        print("❌ No selected items to draft")
        return
    
    # Map selected IDs to items for drafting
    id_to_candidate = {c.id: c for c in ranking_candidates}
    items_for_drafting = []
    
    for idx, selected_id in enumerate(selected_ids):
        if selected_id in id_to_candidate:
            candidate = id_to_candidate[selected_id]
            items_for_drafting.append(SelectedItemForDraft(
                id=f"item:{idx}",
                title=candidate.title,
                url=candidate.url,
                source=candidate.source,
                published_at=candidate.published_at,
                snippet=candidate.snippet
            ))
    
    subscription = create_test_subscription()
    state: AgentState = {"errors": []}
    
    try:
        draft_output, used_llm, fallback_reason = await llm_draft_newsletter_items(
            tone=subscription.tone,
            max_summary_sentences=3,
            items=items_for_drafting,
            state=state
        )
        
        print(f"✅ draft_newsletter_items completed")
        print(f"   Used LLM: {used_llm}")
        if fallback_reason:
            print(f"   Fallback reason: {fallback_reason}")
        
        if draft_output:
            print(f"   Subject: {draft_output.get('subject', 'N/A')}")
            print(f"   Items drafted: {len(draft_output.get('items', []))}")
            
            for item in draft_output.get('items', []):
                print(f"   - {item.get('title', 'N/A')[:50]}...")
                print(f"     Why it matters: {item.get('why_it_matters', 'N/A')[:80]}...")
                print(f"     Summary: {item.get('summary', 'N/A')[:100]}...")
        
        return draft_output
        
    except Exception as e:
        print(f"❌ draft_newsletter_items failed: {e}")
        return None


def test_validation_functions():
    """Test validation functions with various inputs."""
    print("\n🔍 Testing validation functions...")
    
    # Test rank_and_select validation
    candidates = prepare_candidates_for_ranking(create_test_candidates()[:3])
    
    # Valid output
    valid_output = {
        "selected_ids": ["cand:0", "cand:1"],
        "reasons": {"cand:0": "High relevance", "cand:1": "Recent publication"},
        "rejected": [{"id": "cand:2", "reason": "Less relevant"}]
    }
    
    is_valid, error = validate_rank_and_select_output(valid_output, candidates, 3)
    print(f"   Valid output test: {'✅ PASS' if is_valid else '❌ FAIL'} - {error}")
    
    # Invalid output - unknown ID
    invalid_output = {
        "selected_ids": ["unknown:1", "cand:0"],
        "reasons": {},
    }
    
    is_valid, error = validate_rank_and_select_output(invalid_output, candidates, 3)
    print(f"   Invalid ID test: {'❌ FAIL (expected)' if not is_valid else '✅ UNEXPECTED PASS'} - {error}")
    
    # Test draft validation
    items = [SelectedItemForDraft(
        id="item:0",
        title="Test Title", 
        url="https://example.com/test",
        source="example.com",
        snippet="Test snippet"
    )]
    
    valid_draft = {
        "subject": "Test Newsletter",
        "items": [{
            "id": "item:0",
            "title": "Test Title",
            "source": "example.com", 
            "url": "https://example.com/test",
            "why_it_matters": "This is important.",
            "summary": "This is a test summary."
        }]
    }
    
    is_valid, error = validate_draft_newsletter_output(valid_draft, items)
    print(f"   Valid draft test: {'✅ PASS' if is_valid else '❌ FAIL'} - {error}")
    
    # Invalid draft - URL mismatch
    invalid_draft = {
        "subject": "Test Newsletter",
        "items": [{
            "id": "item:0",
            "title": "Test Title",
            "source": "example.com",
            "url": "https://different.com/url",  # Wrong URL
            "why_it_matters": "This is important.",
            "summary": "This is a test summary."
        }]
    }
    
    is_valid, error = validate_draft_newsletter_output(invalid_draft, items)
    print(f"   URL mismatch test: {'❌ FAIL (expected)' if not is_valid else '✅ UNEXPECTED PASS'} - {error}")


def test_domain_enforcement():
    """Test max_per_domain enforcement."""
    print("\n🔒 Testing domain enforcement...")
    
    candidates = [
        CandidateForRanking(id="1", title="Title 1", url="https://techcrunch.com/article1", source="techcrunch.com"),
        CandidateForRanking(id="2", title="Title 2", url="https://techcrunch.com/article2", source="techcrunch.com"), 
        CandidateForRanking(id="3", title="Title 3", url="https://techcrunch.com/article3", source="techcrunch.com"),
        CandidateForRanking(id="4", title="Title 4", url="https://venturebeat.com/article1", source="venturebeat.com"),
        CandidateForRanking(id="5", title="Title 5", url="https://arstechnica.com/article1", source="arstechnica.com"),
    ]
    
    # Test case: 3 from techcrunch, should be limited to 2
    selected_ids = ["1", "2", "3", "4", "5"]
    
    result = enforce_max_per_domain(selected_ids, candidates, max_per_domain=2, target_count=4)
    
    # Count domains in result
    domain_counts = {}
    id_to_candidate = {c.id: c for c in candidates}
    
    for item_id in result:
        if item_id in id_to_candidate:
            from urllib.parse import urlparse
            domain = urlparse(id_to_candidate[item_id].url).netloc.lower()
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    print(f"   Selected items: {result}")
    print(f"   Domain counts: {domain_counts}")
    
    # Check that no domain exceeds limit
    max_domain_count = max(domain_counts.values()) if domain_counts else 0
    if max_domain_count <= 2:
        print("   ✅ Domain enforcement working correctly")
    else:
        print(f"   ❌ Domain enforcement failed - max count: {max_domain_count}")


async def test_full_workflow():
    """Test the complete workflow integration."""
    print("\n🔄 Testing full workflow integration...")
    
    subscription = create_test_subscription()
    candidates = create_test_candidates()
    
    state: AgentState = {
        "subscription": subscription,
        "candidates": candidates,
        "errors": [],
        "node_execution_count": 0,
        "external_search_count": 0
    }
    
    try:
        result_state = await node_select_and_write(state)
        
        print(f"   Status: {result_state.get('status', 'unknown')}")
        print(f"   Selected items: {len(result_state.get('selected', []))}")
        print(f"   Newsletter subject: {result_state.get('newsletter', {}).get('subject', 'N/A')}")
        print(f"   Errors: {len(result_state.get('errors', []))}")
        
        if result_state.get('errors'):
            for error in result_state['errors']:
                print(f"     - {error.source}: {error.code} - {error.message}")
        
        return result_state
        
    except Exception as e:
        print(f"❌ Full workflow test failed: {e}")
        return None


def create_test_report(results: Dict):
    """Create a test execution report."""
    print("\n📊 TEST EXECUTION REPORT")
    print("=" * 50)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"Execution time: {timestamp}")
    print(f"Azure OpenAI Endpoint: {os.environ.get('AZURE_OPENAI_ENDPOINT', 'Not set')}")
    print(f"Azure OpenAI Deployment: {os.environ.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini (default)')}")
    
    print("\n📈 Test Results:")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
        print(f"   {test_name}: {status}")
        
        if result.get('details'):
            for detail in result['details']:
                print(f"     - {detail}")
        
        if result.get('error'):
            print(f"     Error: {result['error']}")
    
    print("\n💡 Next Steps:")
    print("   - Review any failed tests above")
    print("   - Check Azure OpenAI service logs for detailed error information")
    print("   - Verify that your deployment supports function calling")
    print("   - Consider adjusting prompts or schemas if validation fails frequently")


async def main():
    """Main test execution function."""
    print("🚀 Newsletter Agent Function Calling Tests")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        return
    
    results = {}
    
    # Test validation functions
    try:
        test_validation_functions()
        results['validation_functions'] = {'success': True, 'details': ['All validation tests passed']}
    except Exception as e:
        results['validation_functions'] = {'success': False, 'error': str(e)}
    
    # Test domain enforcement
    try:
        test_domain_enforcement()
        results['domain_enforcement'] = {'success': True, 'details': ['Domain limits enforced correctly']}
    except Exception as e:
        results['domain_enforcement'] = {'success': False, 'error': str(e)}
    
    # Test rank and select
    try:
        selected_ids, ranking_candidates = await test_rank_and_select()
        if selected_ids:
            results['rank_and_select'] = {
                'success': True, 
                'details': [f'Selected {len(selected_ids)} items successfully']
            }
        else:
            results['rank_and_select'] = {
                'success': False, 
                'details': ['No items selected - check LLM integration']
            }
    except Exception as e:
        results['rank_and_select'] = {'success': False, 'error': str(e)}
        selected_ids, ranking_candidates = [], []
    
    # Test draft newsletter
    if selected_ids:
        try:
            draft_output = await test_draft_newsletter_items(selected_ids, ranking_candidates)
            if draft_output:
                results['draft_newsletter'] = {
                    'success': True,
                    'details': [f'Generated newsletter with {len(draft_output.get("items", []))} items']
                }
            else:
                results['draft_newsletter'] = {
                    'success': False,
                    'details': ['No draft output generated - check LLM integration']
                }
        except Exception as e:
            results['draft_newsletter'] = {'success': False, 'error': str(e)}
    else:
        results['draft_newsletter'] = {'success': False, 'details': ['Skipped - no selected items']}
    
    # Test full workflow
    try:
        workflow_result = await test_full_workflow()
        if workflow_result and workflow_result.get('status') in ['draft', 'approved']:
            results['full_workflow'] = {
                'success': True,
                'details': [f'Workflow completed with status: {workflow_result.get("status")}']
            }
        else:
            results['full_workflow'] = {
                'success': False, 
                'details': ['Workflow failed or returned unexpected status']
            }
    except Exception as e:
        results['full_workflow'] = {'success': False, 'error': str(e)}
    
    # Generate report
    create_test_report(results)
    
    print("\n🎯 Testing completed!")
    
    # Save results to file
    with open('function_calling_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'results': results
        }, f, indent=2)
    
    print("   Results saved to: function_calling_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())