import httpx

# Global singleton HTTP client for the AI Interviewer service
# Reusing this client avoids TLS handshake overhead on every request
http_client = httpx.AsyncClient()
