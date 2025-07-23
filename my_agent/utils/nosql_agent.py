#!/usr/bin/env python3
"""
NoSQL Query Executor using OpenAI and MongoEngine
Executes MongoDB queries against the sample_supplies database using MongoEngine ODM
Returns structured JSON output with query and results
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from mongoengine import connect, Document, StringField, IntField, ListField, DateTimeField, ReferenceField, EmbeddedDocumentField, EmbeddedDocument, FloatField, DictField, BooleanField, DecimalField
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
import logging
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("NoSQLAgent")

# MongoEngine Document Models for Sample Supplies


class Customer(EmbeddedDocument):
    """Embedded document for customer information"""
    age = IntField()
    email = StringField()
    gender = StringField()
    satisfaction = IntField()


class Item(EmbeddedDocument):
    """Embedded document for item information"""
    name = StringField()
    price = DecimalField()
    quantity = IntField()
    tags = ListField(StringField())


class Sale(Document):
    """Sale document model for sample_supplies"""
    couponUsed = BooleanField()
    customer = EmbeddedDocumentField(Customer)
    items = ListField(EmbeddedDocumentField(Item))
    purchaseMethod = StringField()
    saleDate = DateTimeField()
    storeLocation = StringField()

    meta = {
        'collection': 'sales',
        'allow_inheritance': True
    }


class NoSQLQueryExecutor:
    """NoSQL Query Executor for Sample Supplies Database using MongoEngine"""

    def __init__(self, connection_string: str = None):
        """
        Initialize the NoSQL Query Executor

        Args:
            connection_string: MongoDB connection string (defaults to MONGO_DB from .env)
        """
        self.connection_string = connection_string or os.getenv("MONGO_DB")
        if not self.connection_string:
            raise ValueError(
                "MongoDB connection string not found. Set MONGO_DB in .env file")

        # Connect to MongoDB using MongoEngine
        try:
            # Extract database name from connection string
            db_name = "sample_supplies"
            if "mongodb+srv://" in self.connection_string:
                # For Atlas connections, we need to specify the database name
                connect(db=db_name, host=self.connection_string)
            else:
                # For local connections
                connect(db=db_name, host=self.connection_string)

            print("Successfully connected to MongoDB using MongoEngine!")

        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise e

        self.model = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAPI_KEY")
        )

        # Database schema context
        self.db_context = self._build_database_context()

    def _build_database_context(self) -> str:
        """Build concise database context for sample_supplies schema using MongoEngine models"""
        context = """
MONGODB DATABASE SCHEMA FOR SAMPLE_SUPPLIES (MongoEngine Models)

DATABASE: sample_supplies

SALES COLLECTION (Sale Document):
   - couponUsed: Boolean
   - customer: EmbeddedDocument
     - age: Integer
     - email: String
     - gender: String
     - satisfaction: Integer (1-5 rating)
   - items: List[EmbeddedDocument]
     - name: String
     - price: Decimal128
     - quantity: Integer
     - tags: List[String]
   - purchaseMethod: String (e.g., "Online", "In store", "Phone")
   - saleDate: DateTime
   - storeLocation: String

MongoEngine Query Patterns:
- Sale.objects.filter(couponUsed=True)
- Sale.objects.filter(customer__age__gte=30)
- Sale.objects.filter(customer__gender="F")
- Sale.objects.filter(customer__satisfaction__gte=4)
- Sale.objects.filter(items__name="pencil")
- Sale.objects.filter(items__tags__in=["office"])
- Sale.objects.filter(purchaseMethod="Online")
- Sale.objects.filter(storeLocation="Denver")
- Sale.objects.filter(saleDate__gte=datetime(2023,1,1))
- Sale.objects.filter(items__price__gte=10.0)
- Sale.objects.filter(items__quantity__gte=5)
- Aggregation: Sale.objects.aggregate([...])
- Text search: Sale.objects.search_text('search term')
"""
        return context

    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a MongoDB query using MongoEngine and return results
        """
        logger.info(f"Received query: {query}")
        start_time = time.time()
        try:
            if query.strip().startswith('['):
                logger.info("Detected aggregation pipeline.")
                pipeline = json.loads(query)
                results = []
                collections_to_try = [Sale]
                for collection_class in collections_to_try:
                    try:
                        logger.info(
                            f"Trying aggregation on collection: {collection_class.__name__}")
                        results = list(
                            collection_class.objects.aggregate(pipeline))
                        if results:
                            logger.info(
                                f"Aggregation returned {len(results)} results from {collection_class.__name__}")
                            break
                    except Exception as agg_e:
                        logger.warning(
                            f"Aggregation failed on {collection_class.__name__}: {agg_e}")
                        continue
            else:
                logger.info("Detected find query.")
                query_dict = json.loads(query)
                collection_name = query_dict.get('collection', 'sales')
                find_query = query_dict.get('query', {})
                projection = query_dict.get('projection', {})
                logger.info(
                    f"Collection: {collection_name}, Query: {find_query}, Projection: {projection}")

                # Convert dot notation to double underscore notation for MongoEngine
                def convert_query_for_mongoengine(query_dict):
                    """Convert MongoDB query to MongoEngine format"""
                    converted = {}
                    for key, value in query_dict.items():
                        if '.' in key:
                            # Convert customer.age to customer__age
                            new_key = key.replace('.', '__')
                            converted[new_key] = value
                        else:
                            converted[key] = value
                    return converted

                # Convert projection fields as well
                def convert_projection_for_mongoengine(proj_dict):
                    """Convert projection to MongoEngine format"""
                    converted = {}
                    for key, value in proj_dict.items():
                        if '.' in key:
                            # Convert customer.email to customer__email
                            new_key = key.replace('.', '__')
                            converted[new_key] = value
                        else:
                            converted[key] = value
                    return converted

                # Convert query and projection
                find_query = convert_query_for_mongoengine(find_query)
                projection = convert_projection_for_mongoengine(projection)

                logger.info(f"Converted query: {find_query}")
                logger.info(f"Converted projection: {projection}")

                collection_map = {
                    'sales': Sale
                }
                document_class = collection_map.get(collection_name, Sale)

                # Build query using MongoEngine syntax
                query_kwargs = {}
                for key, value in find_query.items():
                    if isinstance(value, dict) and any(op in str(value) for op in ['$gt', '$gte', '$lt', '$lte', '$ne']):
                        # Handle MongoDB operators
                        for op, op_value in value.items():
                            if op == '$gt':
                                query_kwargs[f"{key}__gt"] = op_value
                            elif op == '$gte':
                                query_kwargs[f"{key}__gte"] = op_value
                            elif op == '$lt':
                                query_kwargs[f"{key}__lt"] = op_value
                            elif op == '$lte':
                                query_kwargs[f"{key}__lte"] = op_value
                            elif op == '$ne':
                                query_kwargs[f"{key}__ne"] = op_value
                    else:
                        query_kwargs[key] = value

                logger.info(f"MongoEngine query kwargs: {query_kwargs}")
                queryset = document_class.objects(**query_kwargs)

                # Remove '_id' from projection for MongoEngine compatibility
                if projection and '_id' in projection:
                    logger.info(
                        "Removing '_id' from projection for MongoEngine compatibility.")
                    projection.pop('_id')

                if projection:
                    fields = {}
                    exclude_fields = {}
                    for field, value in projection.items():
                        if value == 1:
                            fields[field] = 1
                        elif value == 0:
                            exclude_fields[field] = 0
                    if fields:
                        queryset = queryset.only(*fields.keys())
                    if exclude_fields:
                        queryset = queryset.exclude(*exclude_fields.keys())

                results = list(queryset)
                logger.info(f"Find query returned {len(results)} results.")

            def convert_to_dict(obj):
                if hasattr(obj, 'to_mongo'):
                    doc_dict = obj.to_mongo().to_dict()
                    if '_id' in doc_dict:
                        doc_dict['_id'] = str(doc_dict['_id'])
                    return doc_dict
                elif isinstance(obj, dict):
                    return {k: convert_to_dict(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_to_dict(item) for item in obj]
                elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'ObjectId':
                    return str(obj)
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                else:
                    return obj
            converted_results = convert_to_dict(results)
            elapsed = time.time() - start_time
            logger.info(f"Query execution completed in {elapsed:.2f} seconds.")
            return {
                "success": True,
                "query": query,
                "row_count": len(converted_results),
                "data": converted_results,
                "execution_time_seconds": elapsed
            }
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Query failed after {elapsed:.2f} seconds: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "data": [],
                "execution_time_seconds": elapsed
            }

    def generate_and_execute_query(self, prompt: str) -> Dict[str, Any]:
        """
        Generate MongoDB query from natural language prompt and execute it using MongoEngine

        Args:
            prompt: Natural language description of what data to retrieve

        Returns:
            Structured response with generated query and results
        """
        # Create system prompt with database context
        system_prompt = """
You are a MongoDB query generator for the Sample Supplies Database using MongoEngine ODM. 

""" + self.db_context + """

INSTRUCTIONS:
1. Generate ONLY valid MongoDB queries (find operations) or aggregation pipelines
2. Use $match for filtering conditions (customer age, gender, satisfaction, items, purchase method, etc.)
3. Use $project for field selection
4. Use $sort for meaningful ordering
5. Use $limit to limit results (default 20 if not specified)
6. Use $unwind for array operations on items
7. Use $group for aggregations (total sales, average satisfaction, etc.)
8. Return ONLY the MongoDB query in JSON format, no explanations

FOR FIND QUERIES, return format:
{
  "collection": "sales",
  "query": { "field": "value" },
  "projection": { "field": 1, "_id": 0 }
}

FOR AGGREGATION PIPELINES, return format:
[
  { "$match": { "field": "value" } },
  { "$unwind": "$items" },
  { "$group": { "_id": "$field", "total": { "$sum": "$items.price" } } }
]

EXAMPLE PROMPTS AND QUERIES:
- "Show all sales": { "collection": "sales", "query": {}, "projection": { "saleDate": 1, "storeLocation": 1, "customer.email": 1, "_id": 0 } }
- "Sales with coupons": { "collection": "sales", "query": { "couponUsed": true }, "projection": { "saleDate": 1, "customer.email": 1, "_id": 0 } }
- "High satisfaction customers": { "collection": "sales", "query": { "customer.satisfaction": { "$gte": 4 } }, "projection": { "customer.email": 1, "customer.satisfaction": 1, "_id": 0 } }
- "Online purchases": { "collection": "sales", "query": { "purchaseMethod": "Online" }, "projection": { "saleDate": 1, "customer.email": 1, "_id": 0 } }
- "Customer emails in Denver with age above 40": { "collection": "sales", "query": { "storeLocation": "Denver", "customer.age": { "$gt": 40 } }, "projection": { "customer.email": 1, "_id": 0 } }
- "Sales by location": [{ "$group": { "_id": "$storeLocation", "count": { "$sum": 1 } } }, { "$sort": { "count": -1 } }]
- "v": [{ "$unwind": "$items" }, { "$group": { "_id": "$items.name", "total_quantity": { "$sum": "$items.quantity" }, "total_revenue": { "$sum": "$items.price" } } }, { "$sort": { "total_revenue": -1 } }]
- "Average satisfaction by gender": [{ "$group": { "_id": "$customer.gender", "avg_satisfaction": { "$avg": "$customer.satisfaction" }, "count": { "$sum": 1 } } }, { "$sort": { "avg_satisfaction": -1 } }]
- "Sales by age group": [{ "$group": { "_id": { "$cond": [{ "$lt": ["$customer.age", 30] }, "Under 30", { "$cond": [{ "$lt": ["$customer.age", 50] }, "30-49", "50+"] }] }, "count": { "$sum": 1 } } }, { "$sort": { "count": -1 } }]
"""

        # Generate MongoDB query
        messages = [
            HumanMessage(content=f"System: {system_prompt}"),
            HumanMessage(content=f"Generate MongoDB query for: {prompt}")
        ]

        response = self.model.invoke(messages)
        generated_query = response.content.strip()

        # Clean up the query (remove markdown if present)
        if generated_query.startswith("```json"):
            generated_query = generated_query.replace(
                "```json", "").replace("```", "").strip()
        elif generated_query.startswith("```"):
            generated_query = generated_query.replace("```", "").strip()

        # Execute the generated query
        query_result = self.execute_query(generated_query)

        # Return structured response
        return {
            "prompt": prompt,
            "generated_mongodb_query": generated_query,
            "execution_result": query_result,
            "timestamp": self._get_timestamp()
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()

    def get_sample_queries(self) -> List[str]:
        """Get sample query prompts for testing"""
        return [
            "Show all sales with coupons used",
            "Find sales with high customer satisfaction (4 or 5)",
            "Show online purchases",
            "List sales by store location",
            "Find sales with specific items like pencils",
            "Show sales by customer age groups",
            "List total sales by item",
            "Find sales with specific tags",
            "Show average satisfaction by gender",
            "Find sales from specific date ranges",
            "List sales by purchase method",
            "Show sales with high-value items",
            "Find sales by customer email domain",
            "Show sales with multiple items",
            "List sales by customer satisfaction level"
        ]

    def close_connection(self):
        """Close the MongoDB connection"""
        # MongoEngine handles connection cleanup automatically
        pass


def create_nosql_agent() -> NoSQLQueryExecutor:
    """Create a pre-configured NoSQL Query Executor"""
    return NoSQLQueryExecutor()


def interactive_nosql_chat():
    """Run an interactive NoSQL query session"""
    print("🛒 NoSQL Query Executor (Sample Supplies Database) - MongoEngine Edition")
    print("=" * 60)

    try:
        agent = create_nosql_agent()
        print("✅ Connected to MongoDB successfully using MongoEngine")
        print("📊 Sample Supplies database context loaded")

        print("\n💡 Sample queries you can try:")
        sample_queries = agent.get_sample_queries()
        for i, query in enumerate(sample_queries[:5], 1):
            print(f"{i}. {query}")

        print("\nType 'quit' to exit, 'samples' to see more examples")
        print("-" * 50)

        while True:
            try:
                user_input = input("\n🔍 Enter your query: ").strip()

                if user_input.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'samples':
                    print("\n📋 Sample Queries:")
                    for i, query in enumerate(sample_queries, 1):
                        print(f"{i}. {query}")
                    continue
                elif not user_input:
                    continue

                # Generate and execute query
                print("🤖 Generating MongoDB query...")
                result = agent.generate_and_execute_query(user_input)

                # Display results in structured format
                print("\n📊 RESULTS:")
                print(json.dumps(result, indent=2, default=str))

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

    except Exception as e:
        print(f"❌ Failed to initialize NoSQL agent: {e}")
        print("Make sure MONGO_DB and OPENAPI_KEY are set in your .env file")
    finally:
        if 'agent' in locals():
            agent.close_connection()


if __name__ == "__main__":
    # Check if required environment variables are available
    if not os.getenv("OPENAPI_KEY"):
        print("❌ Error: OPENAPI_KEY not found in environment variables")
        print("Please make sure your .env file contains: OPENAPI_KEY=your_api_key_here")
        exit(1)

    if not os.getenv("MONGO_DB"):
        print("❌ Error: MONGO_DB not found in environment variables")
        print("Please make sure your .env file contains: MONGO_DB=mongodb+srv://anton:<db_password>@cluster0.ku0y7rt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
        exit(1)

    interactive_nosql_chat()
