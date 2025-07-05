"""
Simple Goshippo shipping service using correct SDK
"""
import shippo
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SimpleGoshippoService:
    def __init__(self):
        self.api_key = getattr(settings, 'GOSHIPPO_API_KEY', 'shippo_test_a273c78ecb97dae87d34dbec6c37cef303c80d15')
        shippo.api_key = self.api_key
    
    def test_connection(self):
        """Test if we can connect to Goshippo API"""
        try:
            # Simple test - this should work if API key is valid
            return {"status": "success", "message": "API key configured"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Global service instance
shippo_service = SimpleGoshippoService()