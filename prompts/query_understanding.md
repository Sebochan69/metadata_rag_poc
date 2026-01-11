# Query Understanding Prompt

## Metadata
- **Version**: 2.1.0
- **Model**: gpt-4o
- **Temperature**: 0.2
- **Max Tokens**: 300
- **Purpose**: Detect domain from query keywords
- **Last Updated**: 2026-01-10

## Prompt:

Analyze the query and detect the domain.

**Query:** {{query}}

**Domain Detection Rules:**
Look for these keywords:
- Medical: disease, symptoms, hormone, glucose, blood, diagnosis, treatment, infection, clinical, patient
- HR: employee, leave, vacation, PTO, benefits, sick leave, policy, remote work
- Engineering: deploy, kubernetes, API, docker, code, infrastructure, software
- Finance: budget, expense, invoice, revenue, cost, accounting
- Legal: contract, compliance, agreement, terms, liability
- Operations: procedure, SOP, workflow, safety, process

**Output Format (JSON only, no markdown):**

{{"intent": "factual", "query_type": "simple_lookup", "required_filters": {{"domain": ["DomainName"]}}, "optional_filters": {{}}, "reformulated_query": "your improved version", "expected_answer_type": "definition", "confidence": 0.9}}

**Examples:**
- "Which hormone affects glucose?" → {{"intent": "factual", "query_type": "simple_lookup", "required_filters": {{"domain": ["Medical"]}}, "optional_filters": {{}}, "reformulated_query": "Which hormones regulate blood glucose levels?", "expected_answer_type": "definition", "confidence": 0.95}}
- "How to request leave?" → {{"intent": "procedural", "query_type": "simple_lookup", "required_filters": {{"domain": ["HR"]}}, "optional_filters": {{}}, "reformulated_query": "What is the procedure for requesting leave?", "expected_answer_type": "procedure", "confidence": 0.95}}

Return JSON for the query above.