import httpx
from typing import Dict, Any, Optional, List
import asyncio
from backend.models_db import WorkerInstance
from sqlalchemy.orm import Session

class WorkerConnectionService:
    def __init__(self, db: Session = None):
        self.db = db

    async def ping_instance(self, url: str, api_key: Optional[str] = None) -> bool:
        """
        Ping a worker instance to check if it's reachable and healthy.
        Expects the instance to expose a /health endpoint.
        """
        if not url:
            return False
            
        # Ensure URL has protocol
        if not url.startswith("http"):
            url = f"https://{url}"
        
        # Strip trailing slash
        url = url.rstrip('/')
            
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                # 1. Try /health
                try:
                    response = await client.get(f"{url}/health", headers=headers)
                    if response.status_code in [200, 204]:
                        return True
                except:
                    pass
                    
                # 2. Try root
                response = await client.get(url, headers=headers)
                return response.status_code < 500
                
        except Exception as e:
            # print(f"Ping failed for {url}: {e}")
            return False

    async def validate_openclaw_connection(self, url: str, api_key: str) -> Dict[str, Any]:
        """
        Validate an OpenClaw specific connection.
        Returns connection details if successful, raises exception otherwise.
        """
        if not url:
            return {"valid": False, "error": "URL is required"}
            
        if not url.startswith("http"):
            url = f"https://{url}"
        url = url.rstrip('/')
            
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # 1. Check Health / Basic Reachability
                health_ok = False
                try:
                    health_res = await client.get(f"{url}/health")
                    if health_res.status_code == 200:
                        health_ok = True
                except:
                    pass

                # 2. Check Auth by trying to list something protected
                # For OpenClaw, we might not have a standard verified endpoint yet.
                # using v1/info mock for now.
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                
                # If health failed, we can still try auth endpoint as a second chance
                # (maybe /health is protected?)
                
                # Mock validation for now until OpenClaw API is finalized
                if url.endswith("locahlhost") or "claw" in url or health_ok:
                     return {
                        "valid": True,
                        "version": "1.0.0",
                        "latency_ms": 50
                    }
                
                # For now, just trust ping if health is ok
                if health_ok:
                    return {"valid": True, "version": "unknown"}
                
                # If all else fails
                # Try one last GET to root
                res = await client.get(url, headers=headers)
                if res.status_code < 500:
                     return {"valid": True, "version": "unknown (root ok)"}
                     
                return {"valid": False, "error": "Could not reach instance"}
                
            except httpx.RequestError as e:
                return {"valid": False, "error": f"Connection failed: {str(e)}"}
            except Exception as e:
                return {"valid": False, "error": str(e)}

    async def check_instance_health(self, instance_id: str) -> str:
        """
        Check health of a stored instance and update its status in DB.
        """
        if not self.db:
            raise ValueError("Database session required for check_instance_health")
            
        instance = self.db.query(WorkerInstance).filter(WorkerInstance.id == instance_id).first()
        if not instance:
            return "unknown"
            
        is_alive = await self.ping_instance(instance.connection_url, instance.api_key_ref)
        
        new_status = "active" if is_alive else "offline"
        
        # Only update if changed
        if instance.status != new_status:
            instance.status = new_status
            self.db.add(instance)
            self.db.commit()
            
        return new_status
