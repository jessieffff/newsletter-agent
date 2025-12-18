# Function Calling Implementation

This implementation follows the function calling plan outlined in `docs/functioncall.md` and replaces the simple ranking and content generation with LLM-powered tools.

## Overview

The implementation includes:

1. **Two LLM Tools**:
   - `rank_and_select`: Uses LLM to select the best newsletter candidates 
   - `draft_newsletter_items`: Uses LLM to draft newsletter content

2. **Robust Validation**: All LLM outputs are validated and have fallback mechanisms

3. **Domain Enforcement**: Ensures max items per domain constraint is respected

4. **Comprehensive Testing**: Full test suite for local validation

## Key Files

- `packages/agent/src/newsletter_agent/types.py` - Added Pydantic models for LLM inputs/outputs
- `packages/agent/src/newsletter_agent/tools.py` - LLM tool implementations 
- `packages/agent/src/newsletter_agent/workflow.py` - Updated `node_select_and_write` function
- `test_function_calling.py` - Comprehensive test script

## Architecture

### LLM Tool Flow

1. **Ranking Phase**:
   - Candidates are assigned stable IDs (`cand:0`, `cand:1`, etc.)
   - LLM selects best items using structured output
   - Domain constraints are enforced post-selection
   - Falls back to `simple_rank` if LLM fails

2. **Drafting Phase**:
   - Selected items are assigned draft IDs (`item:0`, `item:1`, etc.) 
   - LLM generates subject line and item content
   - URL integrity is validated (no URL modification allowed)
   - Falls back to `generate_newsletter_content` if LLM fails

### Validation & Safety

- **ID Integrity**: LLM can only reference existing candidate/item IDs
- **URL Preservation**: URLs must match exactly between input and output
- **Schema Validation**: All outputs validated against Pydantic schemas
- **Fallback Mechanisms**: Graceful degradation to existing functions
- **Error Tracking**: All failures logged with structured errors

## Testing

### Prerequisites

1. Set up Azure OpenAI credentials:
   ```bash
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   export AZURE_OPENAI_API_KEY="your-api-key"
   export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"  # optional
   ```

2. Install dependencies:
   ```bash
   cd packages/agent
   pip install -e .
   ```

### Run Tests

```bash
# From the root directory
python test_function_calling.py
```

The test script will:
- Validate environment setup
- Test individual function calling components
- Test domain enforcement logic  
- Test complete workflow integration
- Generate a detailed test report

### Expected Output

```
🚀 Newsletter Agent Function Calling Tests
==================================================
✅ Azure OpenAI environment variables are set

🔍 Testing validation functions...
   Valid output test: ✅ PASS - 
   Invalid ID test: ❌ FAIL (expected) - invalid ids: {'unknown:1'}
   Valid draft test: ✅ PASS - 
   URL mismatch test: ❌ FAIL (expected) - URL mismatch for id item:0

🔒 Testing domain enforcement...
   Selected items: ['1', '2', '4', '5']
   Domain counts: {'techcrunch.com': 2, 'venturebeat.com': 1, 'arstechnica.com': 1}
   ✅ Domain enforcement working correctly

🔍 Testing rank_and_select tool...
✅ rank_and_select completed
   Used LLM: True
   Selected 5 items: ['cand:0', 'cand:1', 'cand:2', 'cand:3', 'cand:4']
   - AI Breakthrough: New Language Model Achieves Human-Level Per...
   - Machine Learning in Healthcare: Revolutionary Treatment Pred...
   - Tech Giants Announce New Partnership for AI Safety...
   - Quantum Computing Milestone: 1000-Qubit Processor Demonstra...
   - Robotics Innovation: Humanoid Robots Enter the Workforce...
```

## Production Deployment

### Environment Variables

Set these in your production environment:

```bash
# Required
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key

# Optional (with defaults)
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-10-21
```

### Monitoring

The implementation adds structured logging fields to track LLM usage:

- `used_llm_ranker`: Boolean indicating if LLM ranking was used
- `used_llm_drafter`: Boolean indicating if LLM drafting was used  
- `llm_ranker_fallback_reason`: Reason for ranking fallback (if any)
- `llm_drafter_fallback_reason`: Reason for drafting fallback (if any)
- `max_per_domain_enforced`: Boolean indicating if domain limits were enforced

Monitor these fields to track LLM success rates and identify issues.

### Performance Considerations

1. **Timeout Settings**: Default timeout is 45 seconds, adjust based on your needs
2. **Token Limits**: Large candidate sets may exceed token limits
3. **Rate Limiting**: Consider Azure OpenAI rate limits for your deployment
4. **Fallback Performance**: Ensure fallback functions perform well under load

## Troubleshooting

### Common Issues

1. **"No tool call in response"**: 
   - Check if your Azure OpenAI deployment supports function calling
   - Verify API version is recent (2024-10-21 or later)

2. **"Invalid output" errors**:
   - LLM may be returning unexpected formats
   - Check and adjust prompts for better guidance

3. **Timeout errors**:
   - Increase timeout in settings
   - Reduce candidate set size
   - Check Azure OpenAI service status

4. **Fallback usage**:
   - Monitor structured logs for fallback reasons
   - Common causes: network issues, rate limits, invalid schemas

### Debug Mode

Enable debug logging to see detailed LLM interactions:

```python
import logging
logging.getLogger("newsletter_agent").setLevel(logging.DEBUG)
```

## Next Steps

1. **Monitor Production**: Track LLM success rates and fallback usage
2. **Prompt Tuning**: Adjust prompts based on production performance  
3. **Schema Evolution**: Update schemas as requirements change
4. **Cost Optimization**: Monitor token usage and optimize prompts
5. **A/B Testing**: Compare LLM vs. fallback performance metrics