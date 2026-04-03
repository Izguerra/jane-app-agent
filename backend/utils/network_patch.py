import socket
import logging

logger = logging.getLogger("network-patch")

def apply_network_patches():
    """
    Applies critical network workarounds for LiveKit agents:
    1. DNS Bypass for macOS: Resolves 'worker connection closed unexpectedly' 
       hanging by hardcoding known LiveKit Cloud IPs for the specific project.
    """
    _orig_getaddrinfo = socket.getaddrinfo

    def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        # Specific project Cloud DNS that often hangs on macOS
        if host == "jane-clinic-app-tupihomh.livekit.cloud" or host == "jane-clinic-app-tupihomh.livekit.cloud:443":
            # Direct IPs for jane-clinic-app-tupihomh.livekit.cloud
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('161.115.179.230', port)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('161.115.178.157', port))
            ]
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = _patched_getaddrinfo
    logger.info("✅ Applied LiveKit Cloud DNS bypass for macOS stability.")
