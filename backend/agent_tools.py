import random
from livekit.agents import llm
import importlib
import inspect
from pathlib import Path
from .tools.agent_mixins.search_mixin import SearchMixin
from .tools.agent_mixins.calendar_mixin import CalendarMixin
from .tools.agent_mixins.crm_mixin import CRMMixin
from .tools.agent_mixins.worker_mixin import WorkerMixin
from .tools.agent_mixins.communication_mixin import CommunicationMixin
from .tools.external_tools import ExternalTools

_WORKER_REGISTRY_CACHE = {}

def get_worker_handler(w_type: str):
    """Global Registry resolving worker slugs to their executable methods."""
    global _WORKER_REGISTRY_CACHE
    slug = w_type.lower().strip()
    if slug in _WORKER_REGISTRY_CACHE: return _WORKER_REGISTRY_CACHE[slug]
    
    workers_dir = Path(__file__).parent / "workers"
    if not workers_dir.exists(): return None

    for file in workers_dir.glob("*_worker.py"):
        module_name = f"backend.workers.{file.stem}"
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name.endswith("Worker") and name != "BaseEnterpriseWorker":
                    file_slug = file.stem.replace("_", "-")
                    method = getattr(obj, "run", getattr(obj, "execute", None))
                    if method:
                        _WORKER_REGISTRY_CACHE[file_slug] = method
                        _WORKER_REGISTRY_CACHE[file_slug.replace("-worker", "")] = method
        except: pass
    return _WORKER_REGISTRY_CACHE.get(slug)

class AgentTools(SearchMixin, CalendarMixin, CRMMixin, WorkerMixin, CommunicationMixin, ExternalTools):
    def __init__(self, workspace_id: str, customer_id: str = None, communication_id: str = None, agent_id: str = None, worker_tools=None):
        self.workspace_id = workspace_id
        self.customer_id = customer_id
        self.communication_id = communication_id
        self.agent_id = agent_id
        self.worker_tools = worker_tools
        ExternalTools.__init__(self, workspace_id=workspace_id)
        self.session = None

    async def _play_filler(self, message: str = "One moment please..."):
        if hasattr(self, 'session') and self.session and hasattr(self.session, 'say'):
            try: self.session.say(message, allow_interruptions=False, add_to_chat_ctx=False)
            except: pass
