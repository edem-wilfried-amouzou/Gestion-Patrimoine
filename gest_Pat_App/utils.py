"""
Utility functions for API calls and common operations
"""
import requests
from django.conf import settings


def api_call(endpoint, method='post', data=None):
    """
    Make API calls to the internal API
    
    Args:
        endpoint (str): API endpoint (e.g., 'sign_in', 'sign_up')
        method (str): HTTP method ('post', 'get', 'put', 'delete')
        data (dict): Request data
    
    Returns:
        requests.Response: Response object
    """
    base_url = settings.BASE_API_URL
    url = f"{base_url}/api/{endpoint}/"
    
    if method.lower() == 'post':
        return requests.post(url, json=data)
    elif method.lower() == 'get':
        return requests.get(url, params=data)
    elif method.lower() == 'put':
        return requests.put(url, json=data)
    elif method.lower() == 'delete':
        return requests.delete(url)
    else:
        raise ValueError(f"Unsupported method: {method}")


def api_post(endpoint, data):
    """Shortcut for POST requests"""
    return api_call(endpoint, method='post', data=data)


def api_get(endpoint, params=None):
    """Shortcut for GET requests"""
    return api_call(endpoint, method='get', data=params)
