#!/usr/bin/env python3
"""
Populate sample_supplies database with example data
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from mongoengine import connect, Document, StringField, IntField, ListField, DateTimeField, ReferenceField, EmbeddedDocumentField, EmbeddedDocument, FloatField, DictField, BooleanField, DecimalField
from decimal import Decimal

# Load environment variables
load_dotenv()

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


def populate_database():
    """Populate the database with sample data"""
    print("🛒 Populating Sample Supplies Database")
    print("=" * 50)

    # Connect to MongoDB
    connection_string = os.getenv("MONGO_DB")
    if not connection_string:
        print("❌ MONGO_DB environment variable not found")
        return

    try:
        # Connect to MongoDB using MongoEngine
        db_name = "sample_supplies"
        if "mongodb+srv://" in connection_string:
            connect(db=db_name, host=connection_string)
        else:
            connect(db=db_name, host=connection_string)

        print("✅ Connected to MongoDB successfully!")

        # Clear existing data
        Sale.objects.delete()
        print("🗑️ Cleared existing data")

        # Sample data based on the provided example
        sample_sales = [
            {
                "couponUsed": True,
                "customer": Customer(
                    age=42,
                    email="cauho@witwuta.sv",
                    gender="M",
                    satisfaction=4
                ),
                "items": [
                    Item(
                        name="printer paper",
                        price=Decimal("40.01"),
                        quantity=2,
                        tags=["office", "stationary"]
                    ),
                    Item(
                        name="notepad",
                        price=Decimal("35.29"),
                        quantity=2,
                        tags=["office", "writing", "school"]
                    ),
                    Item(
                        name="pens",
                        price=Decimal("56.12"),
                        quantity=5,
                        tags=["writing", "office", "school", "stationary"]
                    ),
                    Item(
                        name="backpack",
                        price=Decimal("77.71"),
                        quantity=2,
                        tags=["school", "travel", "kids"]
                    ),
                    Item(
                        name="notepad",
                        price=Decimal("18.47"),
                        quantity=2,
                        tags=["office", "writing", "school"]
                    ),
                    Item(
                        name="envelopes",
                        price=Decimal("19.95"),
                        quantity=8,
                        tags=["stationary", "office", "general"]
                    ),
                    Item(
                        name="envelopes",
                        price=Decimal("8.08"),
                        quantity=3,
                        tags=["stationary", "office", "general"]
                    ),
                    Item(
                        name="binder",
                        price=Decimal("14.16"),
                        quantity=3,
                        tags=["school", "general", "organization"]
                    )
                ],
                "purchaseMethod": "Online",
                "saleDate": datetime(2015, 3, 23, 21, 6, 49),
                "storeLocation": "Denver"
            },
            {
                "couponUsed": False,
                "customer": Customer(
                    age=35,
                    email="john.doe@example.com",
                    gender="M",
                    satisfaction=5
                ),
                "items": [
                    Item(
                        name="laptop",
                        price=Decimal("1200.00"),
                        quantity=1,
                        tags=["electronics", "computer", "office"]
                    ),
                    Item(
                        name="mouse",
                        price=Decimal("25.50"),
                        quantity=1,
                        tags=["electronics", "computer", "accessories"]
                    )
                ],
                "purchaseMethod": "In store",
                "saleDate": datetime(2015, 3, 24, 14, 30, 0),
                "storeLocation": "Denver"
            },
            {
                "couponUsed": True,
                "customer": Customer(
                    age=28,
                    email="sarah.wilson@example.com",
                    gender="F",
                    satisfaction=3
                ),
                "items": [
                    Item(
                        name="pencils",
                        price=Decimal("5.99"),
                        quantity=10,
                        tags=["writing", "school", "stationary"]
                    ),
                    Item(
                        name="notebook",
                        price=Decimal("12.50"),
                        quantity=3,
                        tags=["writing", "school", "office"]
                    )
                ],
                "purchaseMethod": "Online",
                "saleDate": datetime(2015, 3, 25, 9, 15, 30),
                "storeLocation": "New York"
            },
            {
                "couponUsed": False,
                "customer": Customer(
                    age=45,
                    email="mike.johnson@example.com",
                    gender="M",
                    satisfaction=5
                ),
                "items": [
                    Item(
                        name="desk chair",
                        price=Decimal("299.99"),
                        quantity=1,
                        tags=["furniture", "office", "ergonomic"]
                    ),
                    Item(
                        name="desk lamp",
                        price=Decimal("45.00"),
                        quantity=1,
                        tags=["lighting", "office", "furniture"]
                    )
                ],
                "purchaseMethod": "Phone",
                "saleDate": datetime(2015, 3, 26, 16, 45, 0),
                "storeLocation": "Denver"
            },
            {
                "couponUsed": True,
                "customer": Customer(
                    age=52,
                    email="lisa.brown@example.com",
                    gender="F",
                    satisfaction=4
                ),
                "items": [
                    Item(
                        name="printer",
                        price=Decimal("199.99"),
                        quantity=1,
                        tags=["electronics", "office", "computer"]
                    ),
                    Item(
                        name="printer paper",
                        price=Decimal("15.99"),
                        quantity=5,
                        tags=["office", "stationary"]
                    ),
                    Item(
                        name="ink cartridges",
                        price=Decimal("29.99"),
                        quantity=2,
                        tags=["electronics", "office", "computer"]
                    )
                ],
                "purchaseMethod": "Online",
                "saleDate": datetime(2015, 3, 27, 11, 20, 15),
                "storeLocation": "Los Angeles"
            }
        ]

        # Insert sample data
        created_sales = []
        for sale_data in sample_sales:
            sale = Sale(**sale_data)
            sale.save()
            created_sales.append(sale)

        print(f"✅ Successfully inserted {len(created_sales)} sales records")

        # Verify data insertion
        total_sales = Sale.objects.count()
        print(f"📊 Total sales in database: {total_sales}")

        # Show sample queries that should now return data
        print("\n🔍 Sample queries that should now return data:")
        print("1. 'Show all sales'")
        print("2. 'Find sales in Denver'")
        print("3. 'List customer emails where store is in Denver and customer age is above 40'")
        print("4. 'Show sales with printer paper items'")
        print("5. 'Find sales with office tags'")
        print("6. 'Show sales with high customer satisfaction'")
        print("7. 'Find online purchases with coupons'")

        # Test a specific query
        print("\n🧪 Testing specific query...")
        denver_sales = Sale.objects.filter(storeLocation="Denver")
        print(f"   Sales in Denver: {denver_sales.count()}")

        denver_over_40 = Sale.objects.filter(
            storeLocation="Denver", customer__age__gt=40)
        print(
            f"   Sales in Denver with customer age > 40: {denver_over_40.count()}")

        if denver_over_40.count() > 0:
            print("   ✅ Query should now return results!")
        else:
            print("   ⚠️ Still no results - check data structure")

    except Exception as e:
        print(f"❌ Error populating database: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    populate_database()
