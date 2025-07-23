#!/usr/bin/env python3
"""
Test script to verify query classification is working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Add the my_agent directory to the path
sys.path.append('my_agent')


def test_classification():
    """Test query classification"""
    print("🔍 Query Classification Test")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    try:
        from my_agent.utils.orchestrator_agent import HybridOrchestrator
        from my_agent.utils.state import QueryDomain, QueryIntent

        orchestrator = HybridOrchestrator()

        # Test queries
        test_queries = [
            # Employee queries
            "Show all employees",
            "Find employees in IT department",
            "List departments with their budgets",

            # Supplies queries
            "Find sales with high customer satisfaction",
            "Show sales from 2020"
        ]

        print("🧪 Testing Query Classification")
        print("=" * 40)

        for query in test_queries:
            print(f"\n🔍 Testing: {query}")

            # Classify the query
            domain, intent = orchestrator.classify_intent(query)

            # Check if classification is correct
            if "employee" in query.lower():
                if domain == QueryDomain.EMPLOYEE:
                    print("   ✅ Correctly classified as employee domain")
                else:
                    print(
                        f"   ❌ Incorrectly classified as {domain.value} (should be employee)")
            elif "sale" in query.lower() or "supplies" in query.lower():
                if domain == QueryDomain.MOVIES:
                    print("   ✅ Correctly classified as supplies domain")
                else:
                    print(
                        f"   ❌ Incorrectly classified as {domain.value} (should be supplies)")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")


def test_workflow():
    """Test the complete workflow"""
    print("\n🔍 Complete Workflow Test")
    print("=" * 50)

    try:
        from my_agent.utils.orchestrator_nodes import get_orchestrator, initialize_state
        from my_agent.utils.state import OrchestratorState

        # Create a test state
        test_state = OrchestratorState(
            messages=[
                {"content": "list all employees first name", "type": "human"}],
            current_query="list all employees first name"
        )

        # Initialize state
        test_state = initialize_state(test_state)

        print(f"Initial state:")
        print(f"  Current query: {test_state['current_query']}")
        print(f"  Query domain: {test_state.get('query_domain', 'Not set')}")
        print(f"  Query intent: {test_state.get('query_intent', 'Not set')}")

        # Test orchestrator
        orchestrator = get_orchestrator()
        domain, intent = orchestrator.classify_intent(
            test_state['current_query'])

        print(f"\nOrchestrator classification:")
        print(f"  Domain: {domain.value}")
        print(f"  Intent: {intent.value}")

        from my_agent.utils.state import QueryDomain
        if domain == QueryDomain.EMPLOYEE:
            print("✅ Query correctly classified as employee domain")
        else:
            print(f"❌ Query incorrectly classified as {domain.value}")

    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")


def main():
    """Run all tests"""
    print("🚀 Query Classification Fix Test Suite")
    print("=" * 50)

    test_classification()
    test_workflow()

    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("Check the output above to verify classification is working correctly.")


if __name__ == "__main__":
    main()
