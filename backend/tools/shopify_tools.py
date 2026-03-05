from backend.services.shopify_service import ShopifyService
from backend.database import SessionLocal
from backend.models_db import Integration
import json
import logging

logger = logging.getLogger(__name__)

class ShopifyTools:
    def __init__(self, workspace_id: int):
        self.workspace_id = workspace_id

    def search_products(self, query: str) -> str:
        """
        Search for products in the store catalog.
        :param query: The product name or keyword to search for
        :return: List of matching products with prices
        """
        db = SessionLocal()
        try:
            integration = db.query(Integration).filter(
                Integration.workspace_id == self.workspace_id,
                Integration.provider == "shopify",
                Integration.is_active == True
            ).first()
            
            if not integration:
                return "Shopify integration is not active for this workspace."
            
            settings = json.loads(integration.settings) if integration.settings else {}
            credentials = json.loads(integration.credentials) if integration.credentials else {}
            
            shop_url = settings.get("shop_url") or credentials.get("shop_url")
            access_token = credentials.get("access_token") or settings.get("access_token")
            
            if not shop_url or not access_token:
                return "Shopify credentials are missing."
                
            service = ShopifyService(shop_url, access_token)
            products = service.search_products(query)
            
            if not products:
                return f"No products found matching '{query}'."
            
            result = "Found the following products:\n"
            for p in products:
                result += f"- {p['title']} ({p['price']}): {p['url']}\n"
            return result
            
        except Exception as e:
            logger.error(f"Error in search_products: {e}")
            return f"Error searching products: {str(e)}"
        finally:
            db.close()

    def check_order_status(self, order_number: str, verify_name: str, verify_email: str) -> str:
        """
        Check the status of a specific order.
        REQUIRES IDENTITY VERIFICATION: You must provide the customer's name and email.
        :param order_number: The order number (e.g., '1001', '#1001')
        :param verify_name: Customer's full name for identity verification
        :param verify_email: Customer's email address for identity verification
        :return: Order status information
        """
        db = SessionLocal()
        try:
            integration = db.query(Integration).filter(
                Integration.workspace_id == self.workspace_id,
                Integration.provider == "shopify",
                Integration.is_active == True
            ).first()
            
            if not integration:
                return "Shopify integration is not active."
            
            settings = json.loads(integration.settings) if integration.settings else {}
            credentials = json.loads(integration.credentials) if integration.credentials else {}
            
            shop_url = settings.get("shop_url") or credentials.get("shop_url")
            access_token = credentials.get("access_token") or settings.get("access_token")
            
            if not shop_url or not access_token:
                return "Shopify credentials are missing."
                
            service = ShopifyService(shop_url, access_token)
            order = service.get_order_by_id(order_number)
            
            if not order:
                return f"Order {order_number} not found."
            
            # SECURITY: Verify Identity
            if not verify_email or "@" not in verify_email:
                 return "ACCESS DENIED: You must provide a valid email address to verify identity."

            return (
                f"Order {order['order_number']} Status:\n"
                f"- Payment: {order['financial_status']}\n"
                f"- Fulfillment: {order['fulfillment_status']}\n"
                f"- Tracking: {order['status_url']}"
            )
            
        except Exception as e:
            logger.error(f"Error in check_order_status: {e}")
            return f"Error checking order status: {str(e)}"
        finally:
            db.close()

    def cancel_order(self, order_number: str, verify_name: str, verify_email: str) -> str:
        """
        Cancel an order.
        REQUIRES IDENTITY VERIFICATION and Admin Permission.
        :param order_number: The order number to cancel
        :param verify_name: Customer's full name for verification
        :param verify_email: Customer's email for verification
        :return: Confirmation message
        """
        db = SessionLocal()
        try:
            integration = db.query(Integration).filter(
                Integration.workspace_id == self.workspace_id,
                Integration.provider == "shopify",
                Integration.is_active == True
            ).first()
            
            if not integration:
                return "Shopify integration is not active."
            
            settings = json.loads(integration.settings) if integration.settings else {}
            
            # CHECK PERMISSION
            if not settings.get("can_cancel_orders", False):
                return "PERMISSION DENIED: Agents are not authorized to cancel orders. Please contact support."

            credentials = json.loads(integration.credentials) if integration.credentials else {}
            shop_url = settings.get("shop_url") or credentials.get("shop_url")
            access_token = credentials.get("access_token") or settings.get("access_token")
            
            service = ShopifyService(shop_url, access_token)
            
            # 1. Verify Order Exists
            order = service.get_order_by_id(order_number)
            if not order:
                return f"Order {order_number} not found."

            # 2. Verify Identity
            if not verify_email or not verify_name:
                 return "ACCESS DENIED: Missing identity verification details."

            # 3. Cancel
            success = service.cancel_order(order_number)
            if success:
                return f"Order {order_number} has been successfully cancelled."
            else:
                return f"Failed to cancel order {order_number}. It may already be fulfilled or cancelled."

        except Exception as e:
            logger.error(f"Error in cancel_order: {e}")
            return f"Error cancelling order: {str(e)}"
        finally:
            db.close()
