"""
Auth0 Configuration

This file contains the Auth0 configuration and initialization code.
"""
import os
import logging
from authlib.integrations.requests_client import OAuth2Session
from jose import jwt

logger = logging.getLogger(__name__)

# Auth0 configuration
config = {
    'domain': os.environ.get('AUTH0_DOMAIN', 'dev-1ipnytneeebogaqd.us.auth0.com'),
    'client_id': os.environ.get('AUTH0_CLIENT_ID', 'sSw9meytBSWJ3UAbxoKuTM4xfpOWzHY3'),
    'client_secret': os.environ.get('AUTH0_CLIENT_SECRET', 'lx9PLgxmwpqlXaFi698aGNBjBhkl7pKrSThrs4Hp0dfiSVlyKR20KcuznBXcDJu0'),
    'api_audience': os.environ.get('AUTH0_API_AUDIENCE', 'https://dev-1ipnytneeebogaqd.us.auth0.com/api/v2/'),
    'algorithm': ['RS256']
}

# Initialize Auth0 client
try:
    # We'll use requests directly instead of OAuth2Session for better SSL error handling
    import requests
    # Test connection to Auth0
    test_response = requests.get(f"https://{config['domain']}/", timeout=5, verify=True)
    logger.info(f"Auth0 connection test: {test_response.status_code}")
    
    auth0_client = OAuth2Session(
        client_id=config['client_id'],
        client_secret=config['client_secret']
    )
    logger.info("Auth0 client initialized successfully")
except requests.exceptions.SSLError as ssl_err:
    logger.error(f"SSL Error connecting to Auth0: {str(ssl_err)}")
    logger.warning("Auth0 client initialization with SSL verification failed. Using direct requests with SSL verification disabled for development.")
    auth0_client = None
except Exception as e:
    logger.error(f"Error initializing Auth0 client: {str(e)}")
    auth0_client = None

# Function to get Auth0 Management API token
def get_management_api_token():
    """
    Get a token for the Auth0 Management API
    
    Returns:
        str: The access token if successful, None otherwise
    """
    try:
        import requests
        
        token_url = f"https://{config['domain']}/oauth/token"
        token_payload = {
            'grant_type': 'client_credentials',
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'audience': config['api_audience']
        }
        
        # Use requests directly instead of auth0_client to have more control over SSL
        response = requests.post(
            token_url, 
            json=token_payload,
            timeout=10,  # Add timeout
            verify=True  # Verify SSL certificates
        )
        
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            logger.error(f"Failed to get token. Status: {response.status_code}, Response: {response.text}")
            return None
    except requests.exceptions.SSLError as ssl_err:
        logger.error(f"SSL Error connecting to Auth0: {str(ssl_err)}")
        # For development only - not recommended for production
        logger.warning("Attempting to connect without SSL verification...")
        try:
            response = requests.post(
                token_url, 
                json=token_payload,
                timeout=10,
                verify=False  # Disable SSL verification as fallback
            )
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                logger.error(f"Failed to get token (SSL disabled). Status: {response.status_code}, Response: {response.text}")
                return None
        except Exception as inner_e:
            logger.error(f"Error in fallback request: {str(inner_e)}")
            return None
    except Exception as e:
        logger.error(f"Error getting Auth0 Management API token: {str(e)}")
        return None