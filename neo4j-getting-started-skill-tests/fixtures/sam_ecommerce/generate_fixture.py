#!/usr/bin/env python3
"""Generate synthetic e-commerce CSV fixtures for the sam_developer persona test."""
import csv, random, pathlib, datetime, uuid

random.seed(42)
OUT = pathlib.Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

CATEGORIES = ["Electronics", "Books", "Clothing", "Home & Garden", "Sports", "Beauty", "Toys", "Food"]
COUNTRIES   = ["US", "UK", "DE", "FR", "CA", "AU", "NL", "SE"]
STATUSES    = ["completed", "completed", "completed", "shipped", "pending", "refunded"]

PRODUCT_NAMES = {
    "Electronics":  ["Wireless Headphones", "USB-C Hub", "Mechanical Keyboard", "Webcam HD",
                     "LED Desk Lamp", "Phone Stand", "Bluetooth Speaker", "Smart Watch"],
    "Books":        ["Python Deep Dive", "Graph Databases", "Clean Code", "The Pragmatic Programmer",
                     "Designing Data-Intensive Apps", "Domain-Driven Design"],
    "Clothing":     ["Running Shoes", "Merino Wool Sweater", "Waterproof Jacket", "Cargo Pants",
                     "Cotton T-Shirt", "Wool Socks"],
    "Home & Garden":["Coffee Maker", "Air Purifier", "Bamboo Cutting Board", "Cast Iron Pan",
                     "Herb Garden Kit", "LED Grow Light"],
    "Sports":       ["Yoga Mat", "Resistance Bands", "Pull-up Bar", "Foam Roller",
                     "Jump Rope", "Water Bottle"],
    "Beauty":       ["Face Moisturizer", "Vitamin C Serum", "Bamboo Toothbrush",
                     "Shampoo Bar", "Lip Balm"],
    "Toys":         ["Building Blocks", "Science Kit", "Puzzle 1000pc", "Board Game"],
    "Food":         ["Organic Coffee Beans", "Green Tea Sampler", "Protein Powder",
                     "Dark Chocolate Box", "Olive Oil"],
}

FIRST = ["Alice","Bob","Carol","David","Emma","Frank","Grace","Henry","Iris","Jack",
          "Karen","Leo","Mia","Noah","Olivia","Paul","Quinn","Rose","Sam","Tina",
          "Uma","Victor","Wendy","Xavier","Yara","Zoe","Aaron","Beth","Carl","Diana",
          "Evan","Fiona","George","Hannah","Ivan","Julia","Kyle","Laura","Mike","Nancy",
          "Oscar","Patricia","Raj","Sara","Tom","Ursula","Vince","Wanda","Xander","Yvonne"]
LAST  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson",
          "Taylor","Anderson","Thomas","Jackson","White","Harris","Martin","Thompson","Moore",
          "Allen","Clark","Lewis","Walker","Hall","Young","King","Wright","Scott","Green",
          "Baker","Adams","Nelson","Carter","Mitchell","Perez","Roberts","Turner","Phillips"]

def rdate(start_days=730, end_days=0):
    d = datetime.date.today() - datetime.timedelta(days=random.randint(end_days, start_days))
    return d.isoformat()

# ── Products ──────────────────────────────────────────────────────────────────
products = []
pid = 1
for cat, names in PRODUCT_NAMES.items():
    for name in names:
        price = round(random.uniform(9.99, 299.99), 2)
        sku   = f"SKU-{pid:04d}"
        products.append({
            "product_id": f"prod{pid}",
            "name": name,
            "sku": sku,
            "price": price,
            "category": cat,
            "stock_quantity": random.randint(0, 500),
        })
        pid += 1

with open(OUT / "products.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["product_id","name","sku","price","category","stock_quantity"])
    w.writeheader(); w.writerows(products)

# ── Customers ─────────────────────────────────────────────────────────────────
customers = []
for i in range(1, 151):
    first = random.choice(FIRST)
    last  = random.choice(LAST)
    customers.append({
        "customer_id": f"cust{i}",
        "name": f"{first} {last}",
        "email": f"{first.lower()}.{last.lower()}{i}@example.com",
        "joined_date": rdate(1095, 30),
        "country": random.choice(COUNTRIES),
        "total_spent": 0,  # filled in after orders
    })

# ── Orders + order_items ──────────────────────────────────────────────────────
orders = []
order_items = []
customer_spend = {c["customer_id"]: 0.0 for c in customers}

oid = 1
for _ in range(300):
    cust = random.choice(customers)
    ordered_at = rdate(365, 0)
    n_items = random.randint(1, 5)
    chosen_products = random.sample(products, n_items)
    total = 0.0
    for prod in chosen_products:
        qty   = random.randint(1, 3)
        price = prod["price"]
        total += qty * price
        order_items.append({
            "order_id":   f"ord{oid}",
            "product_id": prod["product_id"],
            "quantity":   qty,
            "unit_price": price,
        })
    total = round(total, 2)
    orders.append({
        "order_id":    f"ord{oid}",
        "customer_id": cust["customer_id"],
        "ordered_at":  ordered_at,
        "total":       total,
        "status":      random.choice(STATUSES),
    })
    customer_spend[cust["customer_id"]] = round(
        customer_spend[cust["customer_id"]] + total, 2
    )
    oid += 1

# Back-fill total_spent
for c in customers:
    c["total_spent"] = customer_spend[c["customer_id"]]

with open(OUT / "customers.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["customer_id","name","email","joined_date","country","total_spent"])
    w.writeheader(); w.writerows(customers)

with open(OUT / "orders.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["order_id","customer_id","ordered_at","total","status"])
    w.writeheader(); w.writerows(orders)

with open(OUT / "order_items.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["order_id","product_id","quantity","unit_price"])
    w.writeheader(); w.writerows(order_items)

print(f"✓ products.csv      {len(products)} rows")
print(f"✓ customers.csv     {len(customers)} rows")
print(f"✓ orders.csv        {len(orders)} rows")
print(f"✓ order_items.csv   {len(order_items)} rows")
print(f"  Distinct customers with orders: {len([c for c in customers if customer_spend[c['customer_id']] > 0])}")
