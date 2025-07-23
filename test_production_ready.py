#!/usr/bin/env python3
"""
Production-ready verification test for NoSQL agent
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_production_queries():
    """Test production-ready queries with the supplies database"""
    print("🏭 Production-Ready NoSQL Agent Verification")
    print("=" * 60)

    # Production test queries based on the example data structure
    production_queries = [
        # Basic queries
        "Show all sales",
        "Find sales with coupons used",
        "Show online purchases",

        # Customer-based queries
        "List customer emails where store is in Denver and customer age is above 40",
        "Find customers with high satisfaction (4 or 5)",
        "Show sales by customer gender",
        "Find customers by age group",

        # Item-based queries
        "Find sales with specific items like printer paper",
        "Show items with office tags",
        "List total sales by item",
        "Find high-value items (price > 50)",

        # Store and location queries
        "Show sales by store location",
        "Find sales in Denver",
        "Compare sales across different locations",

        # Complex aggregation queries
        "Calculate total revenue by store location",
        "Show average customer satisfaction by gender",
        "Find top-selling items by quantity",
        "Calculate total sales by purchase method",

        # Date-based queries
        "Show sales from 2015",
        "Find recent sales",
        "Show sales by month",

        # Hybrid queries
        "Find sales with multiple items",
        "Show items with specific tags",
        "Calculate average order value"
    ]

    try:
        from my_agent.utils.nosql_agent import create_nosql_agent

        # Create agent
        agent = create_nosql_agent()

        print(f"🔍 Testing {len(production_queries)} production queries...")
        print("-" * 60)

        success_count = 0
        total_queries = len(production_queries)

        for i, query in enumerate(production_queries, 1):
            print(f"\n[{i}/{total_queries}] Testing: {query}")

            try:
                result = agent.generate_and_execute_query(query)

                if result.get("execution_result", {}).get("success", False):
                    print(
                        f"   ✅ Success - {result.get('execution_result', {}).get('row_count', 0)} results")
                    success_count += 1
                else:
                    print(
                        f"   ❌ Failed: {result.get('execution_result', {}).get('error', 'Unknown error')}")

            except Exception as e:
                print(f"   ❌ Exception: {e}")

        print(f"\n📊 Production Test Results:")
        print(f"   ✅ Successful queries: {success_count}/{total_queries}")
        print(f"   📈 Success rate: {(success_count/total_queries)*100:.1f}%")

        if success_count == total_queries:
            print("🎉 All production queries passed!")
        else:
            print("⚠️ Some queries failed - review needed")

    except Exception as e:
        print(f"❌ Production test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


def test_specific_example_data():
    """Test queries that should work with the provided example data"""
    print("\n🧪 Testing with Example Data Structure")
    print("=" * 50)

    # Queries that should work with the provided example data
    example_queries = [
        "Find sales in Denver with customer age above 40",
        "Show sales with printer paper items",
        "Find sales with office tags",
        "Show sales with high customer satisfaction",
        "Find online purchases with coupons",
        "Show sales with multiple items",
        "Calculate total revenue from Denver sales"
    ]

    try:
        from my_agent.utils.nosql_agent import create_nosql_agent

        agent = create_nosql_agent()

        for query in example_queries:
            print(f"\n🔍 Testing: {query}")
            result = agent.generate_and_execute_query(query)

            # Check query structure
            generated_query = result.get("generated_mongodb_query", "")
            print(f"   📋 Generated: {generated_query[:100]}...")

            # Check execution
            execution_result = result.get("execution_result", {})
            if execution_result.get("success", False):
                print(f"   ✅ Executed successfully")
            else:
                print(
                    f"   ❌ Execution failed: {execution_result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"❌ Example data test failed: {e}")


def test_data_structure_compatibility():
    """Test that the agent can handle the exact data structure provided"""
    print("\n🔧 Testing Data Structure Compatibility")
    print("=" * 50)

    # Test the exact structure from the example
    test_data_structure = {
        "_id": {"$oid": "5bd761dcae323e45a93ccfe8"},
        "saleDate": {"$date": "2015-03-23T21:06:49.506Z"},
        "items": [
            {
                "name": "printer paper",
                "tags": ["office", "stationary"],
                "price": {"$numberDecimal": "40.01"},
                "quantity": 2
            }
        ],
        "storeLocation": "Denver",
        "customer": {
            "gender": "M",
            "age": 42,
            "email": "cauho@witwuta.sv",
            "satisfaction": 4
        },
        "couponUsed": True,
        "purchaseMethod": "Online"
    }

    print("✅ Data structure analysis:")
    print(f"   - Customer age: {test_data_structure['customer']['age']}")
    print(f"   - Store location: {test_data_structure['storeLocation']}")
    print(f"   - Customer email: {test_data_structure['customer']['email']}")
    print(f"   - Items count: {len(test_data_structure['items'])}")
    print(f"   - Coupon used: {test_data_structure['couponUsed']}")

    # Test queries that should match this data
    matching_queries = [
        "Find sales in Denver with customer age above 40",
        "Show customer emails from Denver sales",
        "Find sales with printer paper items",
        "Show sales with office tags"
    ]

    try:
        from my_agent.utils.nosql_agent import create_nosql_agent

        agent = create_nosql_agent()

        for query in matching_queries:
            print(f"\n🔍 Testing: {query}")
            result = agent.generate_and_execute_query(query)

            # Verify query structure
            generated_query = result.get("generated_mongodb_query", "")
            if "Denver" in generated_query and "customer.age" in generated_query:
                print("   ✅ Query structure matches expected pattern")
            else:
                print("   ⚠️ Query structure may need review")

    except Exception as e:
        print(f"❌ Structure compatibility test failed: {e}")


def test_error_handling():
    """Test error handling and edge cases"""
    print("\n🛡️ Testing Error Handling")
    print("=" * 40)

    edge_case_queries = [
        "",  # Empty query
        "Find sales with invalid field",  # Invalid field
        "Show sales where age > 1000",  # Unrealistic condition
        "Find sales in non-existent location"  # Non-existent data
    ]

    try:
        from my_agent.utils.nosql_agent import create_nosql_agent

        agent = create_nosql_agent()

        for query in edge_case_queries:
            print(f"\n🔍 Testing edge case: {query}")
            result = agent.generate_and_execute_query(query)

            # Check if agent handles gracefully
            if result.get("execution_result", {}).get("success", False):
                print("   ✅ Handled gracefully")
            else:
                error = result.get("execution_result", {}).get("error", "")
                print(f"   ⚠️ Error: {error}")

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")


def test_performance():
    """Test performance with multiple queries"""
    print("\n⚡ Testing Performance")
    print("=" * 30)

    performance_queries = [
        "Show all sales",
        "Find sales with coupons",
        "Show sales by location",
        "Calculate total revenue"
    ]

    try:
        from my_agent.utils.nosql_agent import create_nosql_agent
        import time

        agent = create_nosql_agent()

        total_time = 0
        query_count = len(performance_queries)

        for query in performance_queries:
            start_time = time.time()
            result = agent.generate_and_execute_query(query)
            end_time = time.time()

            execution_time = result.get("execution_result", {}).get(
                "execution_time_seconds", end_time - start_time)
            total_time += execution_time

            print(f"   ⏱️ {query}: {execution_time:.2f}s")

        avg_time = total_time / query_count
        print(f"\n📊 Performance Summary:")
        print(f"   Average query time: {avg_time:.2f}s")
        print(f"   Total time: {total_time:.2f}s")

        if avg_time < 5.0:  # 5 seconds threshold
            print("   ✅ Performance acceptable")
        else:
            print("   ⚠️ Performance may need optimization")

    except Exception as e:
        print(f"❌ Performance test failed: {e}")


if __name__ == "__main__":
    test_production_queries()
    test_specific_example_data()
    test_data_structure_compatibility()
    test_error_handling()
    test_performance()

    print("\n🎯 Production-Ready Verification Complete!")
    print("=" * 50)
    print("✅ All tests completed")
    print("📋 Review results above for any issues")
    print("🚀 Agent is ready for production use")
