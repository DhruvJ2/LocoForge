#!/usr/bin/env python3
"""
Simple test for NoSQL agent functionality
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_simple_queries():
    """Test simple queries to verify the agent works"""
    print("🧪 Testing Simple NoSQL Queries")
    print("=" * 40)

    test_queries = [
        "Show all sales",
        "Find sales with coupons used",
        "Show sales by store location"
    ]

    try:
        from my_agent.utils.nosql_agent import create_nosql_agent

        # Create agent
        agent = create_nosql_agent()

        for query in test_queries:
            print(f"\n🔍 Testing: {query}")
            print("-" * 30)

            result = agent.generate_and_execute_query(query)

            if result.get("execution_result", {}).get("success", False):
                print(
                    f"✅ Success - {result.get('execution_result', {}).get('row_count', 0)} results")
                print(
                    f"⏱️ Time: {result.get('execution_result', {}).get('execution_time_seconds', 0):.2f}s")
            else:
                print(
                    f"❌ Failed: {result.get('execution_result', {}).get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


def test_specific_prompt_verification():
    """Test the specific prompt that was mentioned"""
    print("\n🧪 Testing Specific Prompt Verification")
    print("=" * 50)

    prompt = "list the customer emails where the store is in Denver and the customer age is above 40"

    try:
        from my_agent.utils.nosql_agent import create_nosql_agent

        agent = create_nosql_agent()

        print(f"🔍 Prompt: {prompt}")
        result = agent.generate_and_execute_query(prompt)

        # Check the generated query structure
        generated_query = result.get("generated_mongodb_query", "")
        print(f"\n📋 Generated Query Structure:")
        print(generated_query)

        # Parse and verify the structure
        try:
            query_dict = json.loads(generated_query)
            query_conditions = query_dict.get("query", {})

            print(f"\n✅ Query Structure Analysis:")
            print(f"  - Collection: {query_dict.get('collection', 'N/A')}")
            print(
                f"  - Store Location: {query_conditions.get('storeLocation', 'N/A')}")
            print(
                f"  - Age Condition: {query_conditions.get('customer.age', 'N/A')}")
            print(f"  - Projection: {query_dict.get('projection', {})}")

            # Verify it matches the expected structure
            expected_conditions = {
                "storeLocation": "Denver",
                "customer.age": {"$gt": 40}
            }

            if (query_conditions.get("storeLocation") == expected_conditions["storeLocation"] and
                    query_conditions.get("customer.age") == expected_conditions["customer.age"]):
                print(f"\n🎯 ✅ Query structure matches expected format!")
            else:
                print(f"\n❌ Query structure doesn't match expected format")

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse generated query: {e}")

        # Check execution result
        execution_result = result.get("execution_result", {})
        if execution_result.get("success", False):
            print(f"\n✅ Query executed successfully!")
            print(f"📊 Results: {execution_result.get('row_count', 0)} rows")
            print(
                f"⏱️ Time: {execution_result.get('execution_time_seconds', 0):.2f}s")
        else:
            print(
                f"\n❌ Query execution failed: {execution_result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_simple_queries()
    test_specific_prompt_verification()
