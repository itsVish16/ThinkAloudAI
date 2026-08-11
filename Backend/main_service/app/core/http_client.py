import httpx

# Global singleton HTTP client for the main service
# Reusing this client avoids TLS handshake overhead on every request
http_client = httpx.AsyncClient()
