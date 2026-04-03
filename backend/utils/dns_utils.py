import socket
import logging

logger = logging.getLogger("dns-utils")

def patch_livekit_dns():
    """
    Patches socket.getaddrinfo to bypass Mac DNS resolution issues 
    for known LiveKit Cloud domains. This is a permanent fix for 
    connectivity drops on macOS.
    """
    _orig_getaddrinfo = socket.getaddrinfo

    def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if host == "jane-clinic-app-tupihomh.livekit.cloud":
            # Hardcode successful resolution for known LiveKit IPs to bypass Mac DNS issues
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('161.115.178.157', port)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('161.115.179.230', port))
            ]
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = _patched_getaddrinfo
    logger.info("Applied DNS bypass patch for LiveKit Cloud")
