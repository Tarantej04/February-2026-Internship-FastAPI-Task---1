from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)
 
app = FastAPI()
 
# ── Temporary data — acting as our database for now ──────────
products = [
    {'id': 1, 'name': 'Wireless Mouse',      'price': 499,  'category': 'Electronics', 'in_stock': True },
    {'id': 2, 'name': 'Notebook',            'price':  99,  'category': 'Stationery',  'in_stock': True },
    {'id': 3, 'name': 'USB Hub',             'price': 799,  'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set',             'price':  49,  'category': 'Stationery',  'in_stock': True },
    {'id': 5, 'name': 'Laptop Stand',        'price': 1299, 'category': 'Electronics', 'in_stock': True},
    {'id': 6, 'name': 'Mechanical Keyboard', 'price': 2499, 'category': 'Electronics', 'in_stock': True},
    {'id': 7, 'name': 'Webcam',              'price': 1599, 'category': 'Electronics', 'in_stock': True},
]
feedback = []
orders = [] 

# ── Endpoint — Home ────────────────────────────────────────
@app.get('/')
def home():
    return {'message': 'Welcome to our E-commerce API'}
 
# ── Endpoint — Return all products ──────────────────────────
@app.get('/products')
def get_all_products():
    return {'products': products, 'total': len(products)}

@app.get('/products/filter')
def filter_products(
    category: str = Query(None, description='Electronics or Stationery'),
    min_price: int = Query(None, description='Minimum price'),
    max_price: int = Query(None, description='Maximum price'),
    in_stock: bool = Query(None, description='True = in stock only')
):

    result = products

    if category:
        filtered = []
        for p in result:
            if p['category'] == category:
                filtered.append(p)
        result = filtered

    if min_price is not None:
        filtered = []
        for p in result:
            if p['price'] >= min_price:
                filtered.append(p)
        result = filtered

    if max_price is not None:
        filtered = []
        for p in result:
            if p['price'] <= max_price:
                filtered.append(p)
        result = filtered

    if in_stock is not None:
        filtered = []
        for p in result:
            if p['in_stock'] == in_stock:
                filtered.append(p)
        result = filtered

    return {
        "filtered_products": result,
        "count": len(result)
    }

# ── Endpoint — Show only in-stock products ───────────────────
@app.get('/products/instock')
def get_instock_products():

    instock_products = []

    for product in products:
        if product['in_stock'] == True:
            instock_products.append(product)

    return {
        "in_stock_products": instock_products,
        "count": len(instock_products)
    }

# ── Endpoint — Get products by category ───────────────────
@app.get('/products/category/{category_name}')
def get_products_by_category(category_name: str):

    filtered_products = []

    for product in products:
        if product['category'].lower() == category_name.lower():
            filtered_products.append(product)

    if len(filtered_products) == 0:
        return {"error": "No products found in this category"}

    return {
        "category": category_name,
        "products": filtered_products,
        "count": len(filtered_products)
    }

# ── Endpoint — Search products by name ─────────────────────
@app.get('/products/search/{keyword}')
def search_products(keyword: str):

    matched_products = []

    for product in products:
        if keyword.lower() in product['name'].lower():
            matched_products.append(product)

    if len(matched_products) == 0:
        return {"message": "No products matched your search"}

    return {
        "matched_products": matched_products,
        "count": len(matched_products)
    }

# ── Endpoint — Best deal & premium pick ───────────────────
@app.get('/products/deals')
def get_product_deals():

    best_deal = products[0]
    premium_pick = products[0]

    for product in products:

        if product['price'] < best_deal['price']:
            best_deal = product

        if product['price'] > premium_pick['price']:
            premium_pick = product

    return {
        "best_deal": best_deal,
        "premium_pick": premium_pick
    }

# ── Endpoint — Get only name and price of a product ─────────
@app.get('/products/{product_id}/price')
def get_product_price(product_id: int):

    for product in products:
        if product['id'] == product_id:
            return {
                "name": product['name'],
                "price": product['price']
            }

    return {"error": "Product not found"}

# ── Endpoint — Submit customer feedback ───────────────────
@app.post('/feedback')
def submit_feedback(data: CustomerFeedback):

    feedback.append(data.dict())

    return {
        "message": "Feedback submitted successfully",
        "feedback": data,
        "total_feedback": len(feedback)
    }

# ── Endpoint — Product summary dashboard ───────────────────
@app.get('/products/summary')
def product_summary():

    total_products = len(products)

    in_stock_count = 0
    out_of_stock_count = 0
    categories = []

    cheapest = products[0]
    most_expensive = products[0]

    for product in products:

        # stock counts
        if product['in_stock'] == True:
            in_stock_count += 1
        else:
            out_of_stock_count += 1

        # collect unique categories
        if product['category'] not in categories:
            categories.append(product['category'])

        # cheapest product
        if product['price'] < cheapest['price']:
            cheapest = product

        # most expensive product
        if product['price'] > most_expensive['price']:
            most_expensive = product

    return {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "most_expensive": {
            "name": most_expensive['name'],
            "price": most_expensive['price']
        },
        "cheapest": {
            "name": cheapest['name'],
            "price": cheapest['price']
        },
        "categories": categories
    }

# ── Endpoint — Place a new order ───────────────────────────
@app.post('/orders')
def create_order(order: BulkOrder):

    order_id = len(orders) + 1

    new_order = {
        "order_id": order_id,
        "company": order.company_name,
        "contact_email": order.contact_email,
        "items": [item.dict() for item in order.items],
        "status": "pending"
    }

    orders.append(new_order)

    return {
        "message": "Order placed successfully",
        "order": new_order
    }

# ── Endpoint — Place bulk order ───────────────────────────
@app.post('/orders/bulk')
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product_found = None

        # find product
        for product in products:
            if product['id'] == item.product_id:
                product_found = product
                break

        # product not found
        if product_found is None:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })
            continue

        # out of stock
        if not product_found['in_stock']:
            failed.append({
                "product_id": item.product_id,
                "reason": f"{product_found['name']} is out of stock"
            })
            continue

        subtotal = product_found['price'] * item.quantity
        grand_total += subtotal

        confirmed.append({
            "product": product_found['name'],
            "qty": item.quantity,
            "subtotal": subtotal
        })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }

# ── Endpoint — Confirm an order ───────────────────────────
@app.patch('/orders/{order_id}/confirm')
def confirm_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {
                "message": "Order confirmed",
                "order": order
            }

    return {"error": "Order not found"}

# ── Endpoint — Get order by ID ─────────────────────────────
@app.get('/orders/{order_id}')
def get_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            return order

    return {"error": "Order not found"}

# ── Endpoint — Return one product by its ID ──────────────────
@app.get('/products/{product_id}')
def get_product(product_id: int):
    for product in products:
        if product['id'] == product_id:
            return {'product': product}
    return {'error': 'Product not found'}

# ── Endpoint — Store summary ───────────────────────────────
@app.get('/store/summary')
def store_summary():

    total_products = len(products)

    in_stock_count = 0
    out_of_stock_count = 0
    categories = []

    for product in products:

        # count stock
        if product['in_stock'] == True:
            in_stock_count += 1
        else:
            out_of_stock_count += 1

        # collect unique categories
        if product['category'] not in categories:
            categories.append(product['category'])

    return {
        "store_name": "My E-commerce Store",
        "total_products": total_products,
        "in_stock": in_stock_count,
        "out_of_stock": out_of_stock_count,
        "categories": categories
    }
