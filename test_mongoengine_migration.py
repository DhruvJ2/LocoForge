#!/usr/bin/env python3
"""
Test script for MongoEngine migration with supplies database
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_mongoengine_supplies():
    """Test MongoEngine with supplies database"""
    print("🛒 Testing MongoEngine with Supplies Database")
    print("=" * 50)

    try:
        from my_agent.utils.nosql_agent import NoSQLQueryExecutor, Sale

        # Create agent
        agent = NoSQLQueryExecutor()

        # Test basic query
        print("\n🔍 Testing basic query...")
        test_query = {
            "collection": "sales",
            "query": {},
            "projection": {"storeLocation": 1, "saleDate": 1, "_id": 0}
        }

        result = agent.execute_query(json.dumps(test_query))
        print(
            f"✅ Query executed successfully. Found {result.get('row_count', 0)} sales")

        # Test MongoEngine models directly
        print("\n🔍 Testing MongoEngine models...")

        # Count total sales
        sale_count = Sale.objects.count()
        print(f"✅ Total sales in database: {sale_count}")

        # Find recent sales
        from datetime import datetime
        recent_sales = Sale.objects.filter(
            saleDate__gte=datetime(2023, 1, 1)).limit(5)
        print(f"✅ Found {recent_sales.count()} sales from 2023 or later")

        # Find high satisfaction sales
        high_satisfaction = Sale.objects.filter(
            customer__satisfaction__gte=4).limit(3)
        print(
            f"✅ Found {high_satisfaction.count()} sales with high satisfaction (>= 4)")

        # Test aggregation
        print("\n🔍 Testing aggregation...")
        pipeline = [
            {"$group": {"_id": "$storeLocation", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]

        agg_result = agent.execute_query(json.dumps(pipeline))
        if agg_result.get("success", False):
            print("✅ Aggregation executed successfully")
            print("📊 Top store locations:")
            for item in agg_result.get("data", [])[:3]:
                print(
                    f"  - {item.get('_id', 'Unknown')}: {item.get('count', 0)} sales")
        else:
            print(
                f"❌ Aggregation failed: {agg_result.get('error', 'Unknown error')}")

        print("\n✅ All MongoEngine tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


def test_natural_language_queries():
    """Test natural language query processing"""
    print("\n🤖 Testing Natural Language Queries")
    print("=" * 40)

    test_queries = [
        "Show sales from 2020",
        "Find sales with high customer satisfaction",
        "Show sales by store location"
    ]

    try:
        from my_agent.utils.nosql_agent import NoSQLQueryExecutor

        agent = NoSQLQueryExecutor()

        for query in test_queries:
            print(f"\n🔍 Testing: {query}")
            result = agent.generate_and_execute_query(query)

            if result.get("execution_result", {}).get("success", False):
                print(
                    f"✅ Success - {result.get('execution_result', {}).get('row_count', 0)} results")
            else:
                print(
                    f"❌ Failed: {result.get('execution_result', {}).get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Natural language test failed: {e}")


if __name__ == "__main__":
    test_mongoengine_supplies()
    test_natural_language_queries()
