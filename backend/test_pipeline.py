"""Test the Phase 3 agent pipeline end-to-end"""

import sys
import json

# Test pipeline with sample input
from app.agents.graph import run_spec_pipeline_sync

sample_input = """
Client Project Requirements

Project Name: E-commerce Mobile App

Goals:
- Build a mobile shopping app for iOS and Android
- Support real-time inventory updates
- Integrate payment processing
- Provide personalized product recommendations

Features Requested:
- User authentication (email/social login)
- Product catalog with search and filters
- Shopping cart and checkout
- Order tracking
- Push notifications for deals
- Wishlist functionality

Technical Requirements:
- Must support 10,000 concurrent users
- Payment integration with Stripe
- Backend API needed
- Admin dashboard for managing products

Timeline: 3 months
Budget: $50,000

Contact: john@example.com
"""

print("=== Testing Phase 3 Agent Pipeline ===\n")
print("Running pipeline on sample input...")

try:
    result = run_spec_pipeline_sync(sample_input.strip())

    print("\n=== PIPELINE RESULTS ===\n")
    print(f"Project Name: {result.project_name}")
    print(f"\nClient Goals ({len(result.client_goals)}):")
    for goal in result.client_goals:
        print(f"  - {goal}")

    print(f"\nFeatures ({len(result.features)}):")
    for feature in result.features[:5]:
        print(f"  - {feature}")
    if len(result.features) > 5:
        print(f"  ... and {len(result.features) - 5} more")

    print(f"\nUnknown Requirements ({len(result.unknown_requirements)}):")
    for unknown in result.unknown_requirements[:3]:
        print(f"  - {unknown}")
    if len(result.unknown_requirements) > 3:
        print(f"  ... and {len(result.unknown_requirements) - 3} more")

    print(f"\nRisks ({len(result.risks)}):")
    for risk in result.risks[:3]:
        print(f"  - [{risk['severity'].upper()}] {risk['description']}")
    if len(result.risks) > 3:
        print(f"  ... and {len(result.risks) - 3} more")

    print(f"\nComplexity Score: {result.complexity_score}/10")
    print(f"Reasoning: {result.complexity_reasoning[:100]}...")

    print(f"\nFollow-up Questions ({len(result.follow_up_questions)}):")
    for q in result.follow_up_questions[:3]:
        print(f"  - {q}")
    if len(result.follow_up_questions) > 3:
        print(f"  ... and {len(result.follow_up_questions) - 3} more")

    print("\n=== Pipeline Test PASSED ===")

except Exception as e:
    print(f"\n=== Pipeline Test FAILED ===")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
