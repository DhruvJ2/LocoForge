#!/usr/bin/env python3
"""
Test script to check query decomposition functionality
"""

from my_agent.utils.orchestrator_nodes import decompose_query_node, classify_query_node
from my_agent.utils.state import OrchestratorState, QueryDomain
import sys
import os
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()


def test_query_decomposition():
    """Test the decompose_query_node with the specific query"""

    # The query to test
    test_query = "find the youngest employee and List customer emails where store is in Denver and customer age is above 40"

    print(f"Testing query decomposition for: {test_query}")
    print("=" * 80)

    # Create initial state
    state = OrchestratorState(
        current_query=test_query,
        query_domain=None,
        query_intent=None,
        query_complexity=None,
        sub_queries={},
        execution_path=[],
        sql_results={},
        nosql_results={},
        combined_results={},
        error_message=None,
        context_history=[],
        data_engineer_response=None,
        clarification_suggestions=None
    )

    # First, classify the query
    print("Step 1: Classifying query...")
    state = classify_query_node(state)
    print(f"Query domain: {state['query_domain']}")
    print(f"Query intent: {state['query_intent']}")
    print(f"Query complexity: {state['query_complexity']}")
    print()

    # Then, decompose the query
    print("Step 2: Decomposing query...")
    state = decompose_query_node(state)
    print(f"Sub-queries: {state['sub_queries']}")
    print()

    # Show the decomposition results
    if state['sub_queries']:
        print("Decomposition Results:")
        print("-" * 40)
        for domain, sub_query in state['sub_queries'].items():
            print(f"{domain.upper()}: {sub_query}")
    else:
        print("No sub-queries generated")

    print()
    print("Expected decomposition:")
    print("-" * 40)
    print("SQL: find the youngest employee")
    print("NOSQL: List customer emails where store is in Denver and customer age is above 40")

    return state


if __name__ == "__main__":
    try:
        result_state = test_query_decomposition()
        print("\n" + "=" * 80)
        print("Test completed successfully!")
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
