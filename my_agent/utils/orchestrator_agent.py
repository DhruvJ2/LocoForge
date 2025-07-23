"""
Hybrid Graph-Based Workflow Orchestrator
Combines Intent Classification, Query Decomposition, Result Aggregation, and Context Management
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from my_agent.utils.state import OrchestratorState, QueryDomain, QueryIntent
from my_agent.utils.nosql_agent import NoSQLQueryExecutor


# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import agents with error handling
try:
    from my_agent.utils.sql_agent import SQLQueryExecutor
    SQL_AVAILABLE = True
except ImportError as e:
    import traceback
    print(f"Warning: SQL agent not available: {e}")
    print(traceback.format_exc())
    SQL_AVAILABLE = False
except Exception as e:
    import traceback
    print(f"Warning: SQL agent not available (non-import error): {e}")
    print(traceback.format_exc())
    SQL_AVAILABLE = False

try:
    from my_agent.utils.nosql_agent import NoSQLQueryExecutor
    NOSQL_AVAILABLE = True
except ImportError as e:
    print(f"Warning: NoSQL agent not available: {e}")
    NOSQL_AVAILABLE = False


class HybridOrchestrator:
    """Hybrid Orchestrator that manages SQL and NoSQL agents with intelligent routing"""

    def __init__(self):
        """Initialize the orchestrator with both agents"""
        # Initialize agents only if available
        self.sql_agent = None
        self.nosql_agent = None

        # Load environment variables explicitly with multiple attempts
        load_dotenv()

        # Additional environment loading for LangGraph Studio
        env_file_paths = ['.env', '../.env', '../../.env']
        for env_path in env_file_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path)
                logger.info(f"Loaded environment from: {env_path}")

        # Verify environment variables
        mongo_db = os.getenv("MONGO_DB")
        openai_key = os.getenv("OPENAPI_KEY") or os.getenv("OPENAI_API_KEY")
        postgres_db_url = os.getenv("POSTGRES_DB_URL")

        logger.info(
            f"Environment check - MONGO_DB: {'SET' if mongo_db else 'NOT SET'}")
        logger.info(
            f"Environment check - OPENAPI_KEY: {'SET' if openai_key else 'NOT SET'}")
        logger.info(
            f"Environment check - POSTGRES_DB_URL: {'SET' if postgres_db_url else 'NOT SET'}")

        if SQL_AVAILABLE:
            try:
                # Use the new SQL agent manager for robust initialization
                from my_agent.utils.sql_agent_manager import initialize_sql_agent, get_sql_manager

                logger.info("🔄 Initializing SQL agent using manager...")
                if initialize_sql_agent():
                    manager = get_sql_manager()
                    self.sql_agent = manager.agent
                    logger.info(
                        "✅ SQL agent initialized successfully via manager")
                else:
                    logger.error(
                        "❌ SQL agent initialization failed via manager")
                    self.sql_agent = None

            except Exception as e:
                logger.error(f"❌ Failed to initialize SQL agent: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                self.sql_agent = None

        if NOSQL_AVAILABLE:
            try:
                # Check if MongoDB connection string is available
                if not mongo_db:
                    logger.warning(
                        "Warning: MONGO_DB environment variable not set")
                    logger.warning("Available environment variables: " + str(
                        [k for k in os.environ.keys() if 'MONGO' in k or 'DB' in k]))
                else:
                    logger.info(
                        f"Initializing NoSQL agent with connection: {mongo_db}")
                    self.nosql_agent = NoSQLQueryExecutor()
                    logger.info("✅ NoSQL agent initialized successfully")
            except Exception as e:
                logger.warning(
                    f"Warning: Failed to initialize NoSQL agent: {e}")
                logger.warning(f"Error details: {type(e).__name__}: {str(e)}")
                import traceback
                logger.warning(f"Full traceback: {traceback.format_exc()}")
        else:
            logger.warning(
                "Warning: NoSQL agent not available (import failed)")

        self.model = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAPI_KEY") or os.getenv("OPENAI_API_KEY")
        )

        # Domain keywords for classification
        self.domain_keywords = {
            QueryDomain.EMPLOYEE: [
                "employee", "staff", "department", "salary", "manager", "hire",
                "attendance", "project", "position", "budget", "performance"
            ],
            QueryDomain.SUPPLIES: [
                "sale", "sales", "supplies", "supply", "customer", "customers", "purchase", "purchases",
                "item", "items", "product", "products", "store", "stores", "location", "locations",
                "coupon", "coupons", "satisfaction", "rating", "ratings", "order", "orders",
                "warehouse", "inventory", "stock", "shopping", "buy", "buying"
            ]
        }

        # Context window for conversation history
        self.context_window = 5

    def classify_intent(self, query: str) -> Tuple[QueryDomain, QueryIntent]:
        """
        Use LLM to classify query domain and intent with fallback to keyword-based classification

        Args:
            query: User query string

        Returns:
            Tuple of (QueryDomain, QueryIntent)
        """
        # First try keyword-based classification for common patterns
        keyword_result = self._keyword_based_classification(query)
        if keyword_result[0] != QueryDomain.UNKNOWN:
            return keyword_result

        # If keyword classification fails, try LLM-based classification
        try:
            system_prompt = """
You are an expert query classifier for a hybrid database system with:
1. SQL Database: Employee management (employees, departments, projects, attendance, salary, titles)
2. NoSQL Database: Sample Supplies (sales, customers, items, stores)

Classify the query into:
- DOMAIN: employee, supplies, hybrid, unknown
- INTENT: select, analyze, compare, aggregate

EXAMPLES:
- "Show all employees in IT department" → {"domain": "employee", "intent": "select"}
- "List all employees first name" → {"domain": "employee", "intent": "select"}
- "Find employees with salary above 50000" → {"domain": "employee", "intent": "select"}
- "Show employee names and departments" → {"domain": "employee", "intent": "select"}
- "Get all employees" → {"domain": "employee", "intent": "select"}
- "Display employee information" → {"domain": "employee", "intent": "select"}
- "Find sales with high customer satisfaction" → {"domain": "supplies", "intent": "select"}
- "Show sales from 2020" → {"domain": "supplies", "intent": "select"}
- "Find employees who bought office supplies" → {"domain": "hybrid", "intent": "select"}
- "Compare sales by store location" → {"domain": "supplies", "intent": "compare"}
- "Show which employees bought office supplies" → {"domain": "hybrid", "intent": "select"}

EMPLOYEE DOMAIN KEYWORDS: employee, employees, staff, department, departments, salary, salaries, attendance, project, projects, manager, managers, hire, hired, title, titles, position, positions

SUPPLIES DOMAIN KEYWORDS: sale, sales, supplies, supply, customer, customers, purchase, purchases, item, items, product, products, store, stores, location, locations, coupon, coupons, satisfaction, rating, ratings, order, orders, warehouse, inventory, stock, shopping, buy, buying

HYBRID QUERIES combine employee data (attendance, departments, projects) with supplies data (sales, customers, items, stores).

Return ONLY a JSON object with "domain" and "intent" fields.
"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Classify this query: {query}")
            ]

            response = self.model.invoke(messages)

            try:
                classification = json.loads(response.content)
                domain = QueryDomain(classification.get("domain", "unknown"))
                intent = QueryIntent(classification.get("intent", "select"))
                return domain, intent
            except:
                return QueryDomain.UNKNOWN, QueryIntent.SELECT
        except Exception as e:
            logger.warning(
                f"LLM classification failed: {e}, using keyword fallback")
            return self._keyword_based_classification(query)

    def _keyword_based_classification(self, query: str) -> Tuple[QueryDomain, QueryIntent]:
        """Keyword-based classification as fallback"""
        query_lower = query.lower()

        # Define domain-specific keywords
        domain_keywords = {
            QueryDomain.EMPLOYEE: [
                "employee", "employees", "department", "departments", "project", "projects",
                "attendance", "salary", "manager", "hire", "hired", "position", "role",
                "team", "staff", "worker", "workers", "hr", "human resources"
            ],
            QueryDomain.SUPPLIES: [
                "sale", "sales", "supplies", "supply", "customer", "customers", "purchase", "purchases",
                "item", "items", "product", "products", "store", "stores", "location", "locations",
                "coupon", "coupons", "satisfaction", "rating", "ratings", "order", "orders",
                "warehouse", "inventory", "stock", "shopping", "buy", "buying"
            ]
        }

        # Count keyword matches for each domain
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            domain_scores[domain] = score

        # Check for hybrid indicators first
        if any(word in query_lower for word in ["both", "combine", "together", "and", "with"]):
            return QueryDomain.HYBRID, QueryIntent.SELECT

        # Check if query contains keywords from both domains
        employee_score = domain_scores.get(QueryDomain.EMPLOYEE, 0)
        supplies_score = domain_scores.get(QueryDomain.SUPPLIES, 0)

        if employee_score > 0 and supplies_score > 0:
            return QueryDomain.HYBRID, QueryIntent.SELECT

        # Determine primary domain if not hybrid
        if employee_score > supplies_score:
            primary_domain = QueryDomain.EMPLOYEE
        elif supplies_score > employee_score:
            primary_domain = QueryDomain.SUPPLIES
        else:
            return QueryDomain.UNKNOWN, QueryIntent.SELECT

        # Determine intent based on keywords
        intent_keywords = {
            QueryIntent.SELECT: ["show", "find", "get", "list", "display", "retrieve"],
            QueryIntent.ANALYZE: ["analyze", "analysis", "report", "summary", "overview"],
            QueryIntent.COMPARE: ["compare", "versus", "vs", "difference", "similar"],
            QueryIntent.AGGREGATE: ["total", "sum",
                                    "average", "count", "group", "aggregate"]
        }

        intent_scores = {}
        for intent, keywords in intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            intent_scores[intent] = score

        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
        else:
            primary_intent = QueryIntent.SELECT

        return primary_domain, primary_intent

    def _build_database_context(self) -> str:
        """Build database context for LLM"""
        context = """
DATABASE CONTEXT:

1. SQL Database: Employee Management (employees, departments, projects, attendance)
2. NoSQL Database: Sample Supplies (sales, customers, items, stores)
3. Query Domains: employee, supplies, hybrid, unknown
4. Query Intents: select, analyze, compare, aggregate

EXAMPLES:
- "Show all employees" → {"domain": "employee", "intent": "select"}
- "Find sales with high customer satisfaction" → {"domain": "supplies", "intent": "select"}
- "Show employees who made large purchases" → {"domain": "hybrid", "intent": "select"}
- "Compare sales by store location" → {"domain": "supplies", "intent": "compare"}
- "Show which employees bought office supplies" → {"domain": "hybrid", "intent": "select"}

KEYWORDS:
EMPLOYEE DOMAIN KEYWORDS: employee, employees, department, departments, project, projects, attendance, salary, manager, hire, hired, position, role, team, staff, worker, workers, hr, human resources

SUPPLIES DOMAIN KEYWORDS: sale, sales, supplies, supply, customer, customers, purchase, purchases, item, items, product, products, store, stores, location, locations, coupon, coupons, satisfaction, rating, ratings, order, orders, warehouse, inventory, stock, shopping, buy, buying

HYBRID QUERIES combine employee data (attendance, departments, projects) with supplies data (sales, customers, items, stores).
"""
        return context

    def decompose_query(self, query: str, domain: QueryDomain) -> Dict[str, str]:
        """
        Decompose complex queries into sub-queries for each domain

        Args:
            query: Original query
            domain: Classified domain

        Returns:
            Dictionary of sub-queries for each domain
        """
        if domain == QueryDomain.HYBRID:
            return self._decompose_hybrid_query(query)
        else:
            return {domain.value: query}

    def _decompose_hybrid_query(self, query: str) -> Dict[str, str]:
        """Decompose hybrid queries into domain-specific sub-queries"""
        system_prompt = """
You are an expert at decomposing hybrid database queries into separate sub-queries for different database systems.

TASK: Decompose the given hybrid query into two separate sub-queries:
1. SQL sub-query: Focus ONLY on employee data (employees, departments, projects, attendance)
2. NoSQL sub-query: Focus ONLY on supplies data (sales, customers, items, stores)

IMPORTANT RULES:
- Extract the SPECIFIC parts of the query that belong to each domain
- SQL sub-query should contain ONLY the employee-related part of the original query
- NoSQL sub-query should contain ONLY the supplies-related part of the original query
- Keep the original wording and intent of each part
- Do NOT generalize or simplify the queries
- Do NOT include the other domain's data in each sub-query

EXAMPLES:

Query: "find the youngest employee and List customer emails where store is in Denver and customer age is above 40"
- SQL: "find the youngest employee"
- NoSQL: "List customer emails where store is in Denver and customer age is above 40"

Query: "Find employees who bought office supplies"
- SQL: "Find employees"
- NoSQL: "Find office supplies"

Query: "Show which employees bought office supplies"
- SQL: "Show employees"
- NoSQL: "Find office supplies"

Query: "Find employees in IT department who watched high-rated movies"
- SQL: "Find employees in IT department"
- NoSQL: "Find high-rated movies"

Query: "Show projects managed by employees who watched action movies"
- SQL: "Show projects managed by employees"
- NoSQL: "Find action movies"

Return ONLY a JSON object with "sql" and "nosql" fields containing the decomposed sub-queries.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Decompose this hybrid query: {query}")
        ]

        response = self.model.invoke(messages)

        try:
            decomposition = json.loads(response.content)
            sql_query = decomposition.get("sql", "")
            nosql_query = decomposition.get("nosql", "")

            # Validate that we got different queries
            if sql_query == nosql_query or not sql_query or not nosql_query:
                # Fallback to manual decomposition
                return self._manual_decompose_hybrid_query(query)

            return {
                "sql": sql_query,
                "nosql": nosql_query
            }
        except:
            # Fallback to manual decomposition
            return self._manual_decompose_hybrid_query(query)

    def _manual_decompose_hybrid_query(self, query: str) -> Dict[str, str]:
        """Manual fallback decomposition for hybrid queries"""
        query_lower = query.lower()

        # Extract employee-related parts
        employee_keywords = ["employees", "employee", "attendance", "department",
                             "departments", "project", "projects", "manager", "managers"]
        sql_parts = []

        # Extract supplies-related parts
        supplies_keywords = ["sales", "sale", "supplies", "supply", "customer", "customers", "purchase", "purchases", "item", "items", "product", "products", "store", "stores",
                             "location", "locations", "coupon", "coupons", "satisfaction", "rating", "ratings", "order", "orders", "warehouse", "inventory", "stock", "shopping", "buy", "buying"]
        nosql_parts = []

        # Simple keyword-based decomposition
        words = query.split()
        for word in words:
            word_clean = word.lower().strip(".,!?")
            if word_clean in employee_keywords:
                sql_parts.append(word)
            elif word_clean in supplies_keywords:
                nosql_parts.append(word)

        # Create basic sub-queries
        if "attendance" in query_lower and "perfect" in query_lower:
            sql_query = "Find employees with perfect attendance records"
        elif "department" in query_lower:
            sql_query = "Get employee and department information"
        else:
            sql_query = "Get employee information"

        if "sale" in query_lower and "office" in query_lower:
            nosql_query = "Find sales"
        elif "rating" in query_lower and "high" in query_lower:
            nosql_query = "Find sales with high customer satisfaction"
        elif "order" in query_lower:
            nosql_query = "Find orders"
        else:
            nosql_query = "Get sales information"

        return {
            "sql": sql_query,
            "nosql": nosql_query
        }

    def execute_sql_query(self, query: str) -> Dict[str, Any]:
        """Execute SQL query using SQL agent manager"""
        try:
            # Use the SQL agent manager for robust execution
            from my_agent.utils.sql_agent_manager import generate_and_execute_sql, execute_sql_query as manager_execute_sql

            # Check if this is already a SQL query (starts with SQL keywords)
            sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE',
                            'CREATE', 'DROP', 'ALTER', 'DESCRIBE', 'EXPLAIN', 'USE']
            query_upper = query.strip().upper()

            # Check if it starts with a SQL keyword AND has SQL-like syntax
            starts_with_sql_keyword = any(query_upper.startswith(
                keyword) for keyword in sql_keywords)

            # Additional checks for SQL-like syntax
            has_sql_syntax = (
                'FROM' in query_upper or
                'WHERE' in query_upper or
                'JOIN' in query_upper or
                'GROUP BY' in query_upper or
                'ORDER BY' in query_upper or
                'LIMIT' in query_upper or
                ';' in query or
                query_upper.startswith('SELECT') or
                query_upper.startswith('INSERT') or
                query_upper.startswith('UPDATE') or
                query_upper.startswith('DELETE')
            )

            is_direct_sql = starts_with_sql_keyword and has_sql_syntax

            logger.info(f"[DEBUG] execute_sql_query - Input query: '{query}'")
            logger.info(
                f"[DEBUG] execute_sql_query - Is direct SQL: {is_direct_sql}")

            if is_direct_sql:
                # Execute the SQL query directly
                logger.info(
                    f"[DEBUG] execute_sql_query - Executing direct SQL: {query}")
                result = manager_execute_sql(query)
                # Format the result to match the expected structure
                return {
                    "prompt": query,
                    "generated_sql": query,
                    "execution_result": result,
                    "timestamp": self._get_timestamp()
                }
            else:
                # Generate SQL from natural language
                logger.info(
                    f"[DEBUG] execute_sql_query - Generating SQL from: {query}")
                result = generate_and_execute_sql(query)
                logger.info(
                    f"[DEBUG] execute_sql_query - Generated result: {result}")
                return result
        except Exception as e:
            logger.error(f"SQL Query execution failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"SQL execution failed: {str(e)}",
                "data": [],
                "execution_result": {
                    "success": False,
                    "error": str(e)
                }
            }

    def execute_nosql_query(self, query: str) -> Dict[str, Any]:
        """Execute NoSQL query using NoSQL agent"""
        if self.nosql_agent is None:
            return {"success": False, "error": "NoSQL agent is not initialized. Check your environment variables and MongoDB setup.", "data": []}
        try:
            return self.nosql_agent.generate_and_execute_query(query)
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def aggregate_results(self, sql_results: Dict[str, Any],
                          nosql_results: Dict[str, Any],
                          original_query: str) -> Dict[str, Any]:
        """
        Format results from both agents as JSON without LLM processing

        Args:
            sql_results: Results from SQL agent
            nosql_results: Results from NoSQL agent
            original_query: Original user query

        Returns:
            Formatted JSON results
        """
        # Check if both results are successful
        sql_success = sql_results.get("execution_result", {}).get(
            "success", False) if sql_results else False
        nosql_success = nosql_results.get("execution_result", {}).get(
            "success", False) if nosql_results else False

        # If both failed, return error
        if not sql_success and not nosql_success:
            return {
                "success": False,
                "error": "Both SQL and NoSQL queries failed",
                "sql_error": sql_results.get("execution_result", {}).get("error", "Unknown error") if sql_results else "No SQL results",
                "nosql_error": nosql_results.get("execution_result", {}).get("error", "Unknown error") if nosql_results else "No NoSQL results"
            }

        # Prepare the combined results
        combined_data = {
            "original_query": original_query,
            "timestamp": self._get_timestamp(),
            "data_sources": []
        }

        # Add SQL results if successful
        if sql_success:
            combined_data["sql_data"] = {
                "success": True,
                "query": sql_results.get("generated_sql", "N/A"),
                "row_count": sql_results.get("execution_result", {}).get("row_count", 0),
                "data": sql_results.get("execution_result", {}).get("data", [])
            }
            combined_data["data_sources"].append("sql")
        else:
            combined_data["sql_data"] = {
                "success": False,
                "error": sql_results.get("execution_result", {}).get("error", "Unknown error") if sql_results else "No SQL results"
            }

        # Add NoSQL results if successful
        if nosql_success:
            execution_result = nosql_results.get("execution_result", {})
            combined_data["nosql_data"] = {
                "success": True,
                "query": nosql_results.get("generated_mongodb_query", "N/A"),
                "row_count": execution_result.get("row_count", 0),
                "data": execution_result.get("data", [])
            }
            combined_data["data_sources"].append("nosql")
        else:
            combined_data["nosql_data"] = {
                "success": False,
                "error": nosql_results.get("execution_result", {}).get("error", "Unknown error") if nosql_results else "No NoSQL results"
            }

        # Set overall success
        combined_data["success"] = sql_success or nosql_success

        return combined_data

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def update_context(self, state: OrchestratorState) -> OrchestratorState:
        """Update conversation context for better routing"""
        context_entry = {
            "query": state["current_query"],
            "domain": state["query_domain"].value,
            "intent": state["query_intent"].value,
            "execution_path": state["execution_path"]
        }

        context_history = state.get("context_history", [])
        context_history.append(context_entry)

        # Keep only recent context
        if len(context_history) > self.context_window:
            context_history = context_history[-self.context_window:]

        state["context_history"] = context_history
        return state

    def get_context_summary(self, context_history: List[Dict[str, Any]]) -> str:
        """Generate context summary for better routing"""
        if not context_history:
            return ""

        recent_contexts = context_history[-3:]  # Last 3 interactions
        summary = "Recent context:\n"

        for ctx in recent_contexts:
            summary += f"- Query: {ctx['query'][:50]}... (Domain: {ctx['domain']})\n"

        return summary

    def check_agent_status(self) -> Dict[str, Any]:
        """Check the status of both agents and return detailed information"""
        # Get SQL agent status from manager
        try:
            from my_agent.utils.sql_agent_manager import get_sql_agent_status
            sql_status = get_sql_agent_status()
        except Exception as e:
            sql_status = {
                "initialized": False,
                "agent_available": False,
                "error_message": f"Failed to get SQL agent status: {str(e)}"
            }

        status = {
            "sql_agent": {
                "available": SQL_AVAILABLE,
                "initialized": sql_status.get("initialized", False),
                "agent_available": sql_status.get("agent_available", False),
                "status": "✅ Ready" if sql_status.get("initialized", False) else "❌ Not initialized",
                "error_message": sql_status.get("error_message"),
                "last_error": sql_status.get("last_error")
            },
            "nosql_agent": {
                "available": NOSQL_AVAILABLE,
                "initialized": self.nosql_agent is not None,
                "status": "✅ Ready" if self.nosql_agent else "❌ Not initialized"
            },
            "environment": {
                "mongo_db": os.getenv("MONGO_DB", "NOT SET"),
                "openai_key": "SET" if os.getenv("OPENAPI_KEY") else "NOT SET",
                "postgres_db_url": os.getenv("POSTGRES_DB_URL", "NOT SET")
            }
        }

        # Add detailed error information if agents failed to initialize
        if not self.nosql_agent and NOSQL_AVAILABLE:
            status["nosql_agent"]["error"] = "Agent import succeeded but initialization failed"
            if not os.getenv("MONGO_DB"):
                status["nosql_agent"]["error"] = "MONGO_DB environment variable not set"

        return status
