# generate_sample_data.py
# Run this script ONCE to create the sample ecommerce CSV.
# Usage: python generate_sample_data.py

import pandas as pd
import numpy as np
import os
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

PRODUCTS = [
    ("Laptop", "Electronics"),
    ("Smartphone", "Electronics"),
    ("Headphones", "Electronics"),
    ("Tablet", "Electronics"),
    ("T-Shirt", "Clothing"),
    ("Jeans", "Clothing"),
    ("Jacket", "Clothing"),
    ("Sneakers", "Footwear"),
    ("Boots", "Footwear"),
    ("Running Shoes", "Footwear"),
    ("Coffee Maker", "Home & Kitchen"),
    ("Blender", "Home & Kitchen"),
    ("Microwave", "Home & Kitchen"),
    ("Novel - Fiction", "Books"),
    ("Business Strategy", "Books"),
    ("Programming Guide", "Books"),
]

REGIONS = ["North", "South", "East", "West", "Central"]

def generate_data(n_rows=500):
    records = []
    start_date = datetime(2024, 1, 1)

    for i in range(n_rows):
        # Random date in 2024
        date = start_date + timedelta(days=random.randint(0, 364))

        # Product and category
        product, category = random.choice(PRODUCTS)

        # Region
        region = random.choice(REGIONS)

        # Base price per product type
        price_map = {
            "Electronics": random.uniform(150, 1200),
            "Clothing": random.uniform(20, 120),
            "Footwear": random.uniform(40, 200),
            "Home & Kitchen": random.uniform(30, 300),
            "Books": random.uniform(10, 50),
        }
        unit_price = round(price_map.get(category, 50), 2)

        # Quantity
        quantity = random.randint(1, 10)

        # Revenue with some seasonality (Q4 boost, June dip)
        seasonal_factor = 1.0
        month = date.month
        if month in [11, 12]:  # Q4 holiday boost
            seasonal_factor = 1.3
        elif month in [6, 7]:  # Summer dip
            seasonal_factor = 0.85

        # Regional factor
        region_factor = {"North": 1.1, "South": 0.9, "East": 1.05, "West": 1.0, "Central": 0.95}
        rev = round(unit_price * quantity * seasonal_factor * region_factor[region], 2)

        # Returns (some orders are returned)
        returns = round(rev * random.uniform(0, 0.15), 2) if random.random() < 0.15 else 0.0

        records.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Product": product,
            "Category": category,
            "Region": region,
            "Unit_Price": unit_price,
            "Quantity": quantity,
            "Revenue": rev,
            "Returns": returns,
        })

    df = pd.DataFrame(records)
    # Add a few missing values and duplicates for demo
    for col in ["Revenue", "Quantity"]:
        idx = random.sample(range(len(df)), 5)
        df.loc[idx, col] = np.nan

    # Add 3 duplicate rows
    df = pd.concat([df, df.iloc[:3]], ignore_index=True)

    return df

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ecommerce_sales.csv")

    df = generate_data(500)
    df.to_csv(output_path, index=False)
    print(f"[OK] Sample data created: {output_path}")
    print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"   Columns: {list(df.columns)}")
