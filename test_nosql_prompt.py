#!/usr/bin/env python3
"""
Test script to verify NoSQL agent prompt handling
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_specific_prompt():
    """Test the specific prompt about customer emails in Denver with age above 40"""
    print("🧪 Testing Specific NoSQL Prompt")
    print("=" * 50)

    test_prompt = "list the customer emails where the store is in Denver and the customer age is above 40"

    try:
        from my_agent.utils.nosql_agent import create_nosql_agent

        # Create agent
        agent = create_nosql_agent()

        print(f"🔍 Testing prompt: {test_prompt}")
        print("-" * 50)

        # Generate and execute query
        result = agent.generate_and_execute_query(test_prompt)

        print("📊 Results:")
        print(json.dumps(result, indent=2, default=str))

        # Check if the generated query looks correct
        generated_query = result.get("generated_mongodb_query", "")
        print(f"\n🔍 Generated Query: {generated_query}")

        # Parse the generated query to check structure
        try:
            if generated_query.startswith('{'):
                query_dict = json.loads(generated_query)
                print(f"\n✅ Query parsed successfully")
                print(f"📋 Collection: {query_dict.get('collection', 'N/A')}")
                print(f"🔍 Query conditions: {query_dict.get('query', {})}")
                print(f"📤 Projection: {query_dict.get('projection', {})}")
            elif generated_query.startswith('['):
                pipeline = json.loads(generated_query)
                print(f"\n✅ Aggregation pipeline parsed successfully")
                print(f"📋 Pipeline stages: {len(pipeline)}")
                for i, stage in enumerate(pipeline):
                    print(f"  Stage {i+1}: {list(stage.keys())[0]}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse generated query: {e}")

        # Check execution result
        execution_result = result.get("execution_result", {})
        if execution_result.get("success", False):
            print(f"\n✅ Query executed successfully!")
            print(f"📊 Rows returned: {execution_result.get('row_count', 0)}")
            print(
                f"⏱️ Execution time: {execution_result.get('execution_time_seconds', 0):.2f}s")

            # Show sample data
            data = execution_result.get("data", [])
            if data:
                print(f"\n📋 Sample results:")
                for i, item in enumerate(data[:3]):  # Show first 3
                    print(f"  {i+1}. {item}")
        else:
            print(
                f"\n❌ Query execution failed: {execution_result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


def test_expected_query_structure():
    """Test that the expected query structure is generated"""
    print("\n🧪 Testing Expected Query Structure")
    print("=" * 50)

    expected_query = {
        "collection": "sales",
        "query": {
            "storeLocation": "Denver",
            "customer.age": {"$gt": 40}
        },
        "projection": {
            "customer.email": 1,
            "_id": 0
        }
    }

    print(f"🎯 Expected query structure:")
    print(json.dumps(expected_query, indent=2))

    # Test if this query would work
    try:
        from my_agent.utils.nosql_agent import create_nosql_agent

        agent = create_nosql_agent()
        result = agent.execute_query(json.dumps(expected_query))

        if result.get("success", False):
            print(f"\n✅ Expected query structure works!")
            print(f"📊 Rows returned: {result.get('row_count', 0)}")
        else:
            print(
                f"\n❌ Expected query structure failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Expected query test failed: {e}")


if __name__ == "__main__":
    test_specific_prompt()
    test_expected_query_structure()
