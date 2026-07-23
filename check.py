from real_estate_backend.ai.prompts import parse_model_response

# Test 1 — tool call
r1 = parse_model_response('{"type": "tool_call", "tool": "get_new_leads", "args": {}}')
print("tool call parsed OK:", r1)

# Test 2 — text response
r2 = parse_model_response('{"type": "text", "message": "You have 3 leads"}')
print("text parsed OK:", r2)

# Test 3 — malformed JSON (model ignores instructions)
r3 = parse_model_response("You have 3 new leads waiting.")
print("fallback parsed OK:", r3)

# Test 4 — markdown fence (model wraps in code block)
r4 = parse_model_response('```json\n{"type": "text", "message": "Hello"}\n```')
print("markdown fence parsed OK:", r4)