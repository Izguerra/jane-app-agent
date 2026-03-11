import asyncio
import logging
from backend.database import SessionLocal
from backend.services.campaign_service import CampaignService

logger = logging.getLogger(__name__)

async def run_campaign_processor():
    """
    Background task to process campaign enrollments periodically.
    """
    logger.info("Starting Campaign Processor Worker...")
    
    while True:
        try:
            # Create a new DB session for this iteration
            db = SessionLocal()
            try:
                service = CampaignService(db)
                # Run the synchronous processing logic
                # (If this becomes heavy, we might want to run it in a threadpool)
                service.process_enrollments()
            except Exception as e:
                logger.error(f"Error in campaign processor loop: {e}")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Critical error in campaign worker setup: {e}")
            
        # Wait for 60 seconds before next run
        await asyncio.sleep(60)
