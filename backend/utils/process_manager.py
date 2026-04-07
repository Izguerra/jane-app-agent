import os
import sys
import signal
import logging
import asyncio
from typing import Callable, Awaitable

logger = logging.getLogger("process-manager")

class ProcessManager:
    """
    Handles PID file locking and signal trapping for agents to prevent runaway processes.
    """
    def __init__(self, name: str, pid_file: str):
        self.name = name
        self.pid_file = pid_file
        self.shutdown_event = asyncio.Event()

    def check_lock(self):
        """Checks if a process is already running with this PID file."""
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, "r") as f:
                    pid = int(f.read().strip())
                if pid == os.getpid():
                    # The PID in the file is our own PID (e.g., written by a shell wrapper)
                    # We shouldn't kill ourselves.
                    return
                
                # Check if process actually exists
                try:
                    os.kill(pid, 0)
                except (OSError, ProcessLookupError):
                    # Process is already dead
                    logger.debug(f"PID {pid} not found, stale PID file.")
                    os.remove(self.pid_file)
                    return

                logger.warning(f"Process '{self.name}' is already running (PID {pid}). Attempting to kill it to prevent port conflicts...")
                try:
                    os.kill(pid, signal.SIGTERM)
                    import time
                    time.sleep(1) # Give it a moment to terminate
                    # Check again, if still there, SIGKILL
                    try:
                        os.kill(pid, 0)
                        logger.warning(f"Process '{self.name}' (PID {pid}) did not terminate. Sending SIGKILL...")
                        os.kill(pid, signal.SIGKILL)
                        time.sleep(0.5)
                    except (OSError, ProcessLookupError):
                        pass # Process terminated after SIGTERM
                except (OSError, ProcessLookupError):
                    pass # Process is already dead
                
                logger.info(f"Successfully purged stale process '{self.name}' (PID {pid}). Proceeding with startup.")
            except (OSError, ValueError):
                # Process is dead or PID file is corrupted, safe to overwrite
                logger.warning(f"Stale PID file found for '{self.name}', cleaning up...")
                os.remove(self.pid_file)

    def write_lock(self):
        """Writes the current PID to the lock file."""
        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))
        logger.info(f"Started '{self.name}' with PID {os.getpid()}")

    def cleanup(self):
        """Removes the PID file."""
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)
        logger.info(f"Cleaned up PID file for '{self.name}'")

    def setup_signals(self, loop: asyncio.AbstractEventLoop = None):
        """Traps SIGINT and SIGTERM to trigger graceful shutdown."""
        if not loop:
            loop = asyncio.get_event_loop()
            
        def handle_signal():
            logger.info(f"Received shutdown signal for '{self.name}'")
            self.shutdown_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, handle_signal)
            except NotImplementedError:
                # Fallback for Windows or environments where add_signal_handler is missing
                signal.signal(sig, lambda s, f: handle_signal())

    async def wait_for_shutdown(self, cleanup_func: Callable[[], Awaitable[None]] = None):
        """Waits for the shutdown event and executes the cleanup function."""
        await self.shutdown_event.wait()
        if cleanup_func:
            logger.info(f"Executing cleanup for '{self.name}'...")
            try:
                await cleanup_func()
            except Exception as e:
                logger.error(f"Cleanup failed for '{self.name}': {e}")
        self.cleanup()
        logger.info(f"'{self.name}' shutdown complete.")
        # Ensure the process exits even if some threads are hanging
        # sys.exit(0) is too aggressive if called from within a loop sometimes, 
        # but here it's our final act.
