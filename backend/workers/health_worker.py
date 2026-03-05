import asyncio
import json
import logging
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models_db import Integration
from backend.services.worker_connection_service import WorkerConnectionService

logger = logging.getLogger(__name__)

async def check_openclaw_health():
    """
    Iterates over all active OpenClaw integrations and pings their instances.
    Updates the status in the integration settings if changed.
    """
    db = SessionLocal()
    try:
        integrations = db.query(Integration).filter(
            Integration.provider == "openclaw",
            Integration.is_active == True
        ).all()
        
        service = WorkerConnectionService(db)
        
        for integration in integrations:
            if not integration.settings:
                continue
                
            try:
                settings = json.loads(integration.settings)
                instances = settings.get("instances", [])
                changed = False
                
                updated_instances = []
                for instance in instances:
                    # Skip managed instances in provisioning state (handled by another worker?)
                    # For now we check everything that has a URL.
                    
                    url = instance.get("url")
                    api_key = instance.get("apiKey")
                    
                    if not url:
                        updated_instances.append(instance)
                        continue
                        
                    # Ping
                    is_alive = await service.ping_instance(url, api_key)
                    new_status = "active" if is_alive else "offline"
                    
                    if instance.get("status") != new_status:
                        instance["status"] = new_status
                        changed = True
                        
                    updated_instances.append(instance)
                
                if changed:
                    settings["instances"] = updated_instances
                    integration.settings = json.dumps(settings)
                    db.add(integration)
            except Exception as e:
                logger.error(f"Error checking health for integration {integration.id}: {e}")
                
        if db.dirty:
            db.commit()
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    finally:
        db.close()

async def run_health_worker():
    """
    Background task loop.
    """
    logger.info("Starting Health Worker...")
    while True:
        try:
            await check_openclaw_health()
        except Exception as e:
            logger.error(f"Health worker loop error: {e}")
        
        # Run every 60 seconds
        await asyncio.sleep(60)
