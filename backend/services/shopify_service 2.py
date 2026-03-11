import requests
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

class ShopifyService:
    """Service for interacting with Shopify Admin API."""
    
    API_VERSION = "2024-01"
    
    def __init__(self, shop_url: str, access_token: str):
        """
        Args:
            shop_url: e.g., "my-shop.myshopify.com"
            access_token: Admin API Access Token (shpat_...)
        """
        # Ensure shop_url doesn't have protocol
        self.shop_url = shop_url.replace("https://", "").replace("http://", "").rstrip("/")
        self.access_token = access_token
        self.base_url = f"https://{self.shop_url}/admin/api/{self.API_VERSION}"
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

    def search_products(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for products by title.
        """
        url = f"{self.base_url}/products.json"
        params = {
            "title": query,
            "status": "active",
            "limit": limit
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            products = []
            for item in data.get("products", []):
                # Format for the agent
                variants = item.get("variants", [])
                price_range = "N/A"
                if variants:
                    prices = [float(v["price"]) for v in variants]
                    min_price = min(prices)
                    max_price = max(prices)
                    price_range = f"${min_price:.2f}" if min_price == max_price else f"${min_price:.2f} - ${max_price:.2f}"
                
                products.append({
                    "id": item["id"],
                    "title": item["title"],
                    "description": item.get("body_html", "")[:200], # Truncate description
                    "price": price_range,
                    "handle": item["handle"],
                    "url": f"https://{self.shop_url}/products/{item['handle']}",
                    "variants": [
                        {
                            "id": v["id"],
                            "title": v["title"],
                            "price": v["price"]
                        } for v in variants
                    ]
                })
            
            return products
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching Shopify products: {e}")
            return []

    def get_orders_by_email(self, email: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Find recent orders for a customer by email.
        """
        # First, find the customer ID
        customer_search_url = f"{self.base_url}/customers/search.json"
        try:
            # Search for customer
            response = requests.get(customer_search_url, headers=self.headers, params={"query": f"email:{email}"})
            response.raise_for_status()
            customers = response.json().get("customers", [])
            
            if not customers:
                return []
            
            customer_id = customers[0]["id"]
            
            # Get orders for this customer
            orders_url = f"{self.base_url}/customers/{customer_id}/orders.json"
            orders_response = requests.get(orders_url, headers=self.headers, params={"status": "any", "limit": limit})
            orders_response.raise_for_status()
            
            orders = []
            for order in orders_response.json().get("orders", []):
                orders.append({
                    "order_number": order["order_number"],
                    "status_url": order["order_status_url"],
                    "financial_status": order["financial_status"],
                    "fulfillment_status": order["fulfillment_status"] or "unfulfilled",
                    "created_at": order["created_at"],
                    "total_price": order["total_price"],
                    "currency": order["currency"]
                })
            
            return orders
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Shopify orders: {e}")
            return []

    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific order by ID (Shopify ID, not order number).
        Note: Searching by 'Order Number' (e.g. 1001) requires a different query.
        """
        # Usually users ask about "Order #1001", so we should search by name
        url = f"{self.base_url}/orders.json"
        params = {
            "name": order_id if order_id.startswith("#") else f"#{order_id}",
            "status": "any"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            orders = response.json().get("orders", [])
            
            if not orders:
                return None
                
            order = orders[0]
            return {
                "order_number": order["order_number"],
                "status_url": order["order_status_url"],
                "financial_status": order["financial_status"],
                "fulfillment_status": order["fulfillment_status"] or "unfulfilled",
                "created_at": order["created_at"],
                "line_items": [
                    f"{item['quantity']}x {item['title']}" for item in order.get("line_items", [])
                ]
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Shopify order: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        """
        # Ensure we have the numeric ID
        numeric_id = order_id.replace("#", "")
        
        # If the ID passed is the order number (e.g. 1001), we first need to find the real ID
        # But for safety, the tool should probably pass the real ID found via get_order_by_id
        # However, let's assume we might get either.
        
        # Try to cancel directly assuming it's the ID
        url = f"{self.base_url}/orders/{numeric_id}/cancel.json"
        
        try:
            response = requests.post(url, headers=self.headers, json={})
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error cancelling Shopify order {numeric_id}: {e}")
            return False

    def create_draft_order(self, variant_id: int, quantity: int, email: str) -> Optional[str]:
        """
        Create a draft order and return the invoice URL.
        """
        url = f"{self.base_url}/draft_orders.json"
        payload = {
            "draft_order": {
                "line_items": [
                    {
                        "variant_id": variant_id,
                        "quantity": quantity
                    }
                ],
                "email": email,
                "use_customer_default_address": True
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["draft_order"]["invoice_url"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating draft order: {e}")
            return None
