import stripe
import os
import logging
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PRODUCT_NAME = "Additional Twilio Phone Number"
PRICE_AMOUNT = 999 # $9.99 in cents

def setup_products():
    if not stripe.api_key:
        logger.error("STRIPE_SECRET_KEY not set")
        return

    try:
        # Check if product exists
        products = stripe.Product.search(query=f"name:'{PRODUCT_NAME}'", limit=1)
        
        if products.data:
            product = products.data[0]
            logger.info(f"Product '{PRODUCT_NAME}' already exists: {product.id}")
            
            # Check for price
            prices = stripe.Price.list(product=product.id, limit=1)
            if prices.data:
                price = prices.data[0]
                logger.info(f"Price exists: {price.id} - ${price.unit_amount/100}/mo")
            else:
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=PRICE_AMOUNT,
                    currency="usd",
                    recurring={"interval": "month"},
                    nickname="Monthly Phone Number Fee"
                )
                logger.info(f"Created price: {price.id}")
        else:
            # Create product
            product = stripe.Product.create(name=PRODUCT_NAME)
            logger.info(f"Created product: {product.id}")
            
            # Create price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=PRICE_AMOUNT,
                currency="usd",
                recurring={"interval": "month"},
                nickname="Monthly Phone Number Fee"
            )
            logger.info(f"Created price: {price.id}")
            
    except Exception as e:
        logger.error(f"Error setting up products: {e}")

if __name__ == "__main__":
    setup_products()
