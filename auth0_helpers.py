"""
Helper functions for Auth0 authentication
"""
import logging
import requests
from auth0_config import config, get_management_api_token

logger = logging.getLogger(__name__)

def user_exists_in_auth0(email, password):
    """
    Check if a user exists in Auth0 by attempting to sign in
    
    Args:
        email: User email
        password: User password
        
    Returns:
        tuple: (exists, user_data)
            - exists: Boolean indicating if user exists
            - user_data: Auth0 user data if exists, None otherwise
    """
    try:
        token_url = f"https://{config['domain']}/oauth/token"
        payload = {
            'grant_type': 'password',
            'username': email,
            'password': password,
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'audience': config['api_audience'],
            'scope': 'openid profile email'
        }
        
        # Add timeout and SSL verification
        response = requests.post(token_url, json=payload, timeout=10, verify=True)
        
        if response.status_code == 200:
            user_data = response.json()
            return True, user_data
        else:
            try:
                error = response.json()
                logger.info(f"Auth0 login failed: {error.get('error_description', 'Unknown error')}")
            except:
                logger.info(f"Auth0 login failed with status code: {response.status_code}")
            return False, None
    except requests.exceptions.SSLError as ssl_err:
        logger.error(f"SSL Error connecting to Auth0: {str(ssl_err)}")
        # For development only - not recommended for production
        logger.warning("Attempting to connect without SSL verification...")
        try:
            response = requests.post(token_url, json=payload, timeout=10, verify=False)
            if response.status_code == 200:
                user_data = response.json()
                return True, user_data
            else:
                try:
                    error = response.json()
                    logger.info(f"Auth0 login failed (SSL disabled): {error.get('error_description', 'Unknown error')}")
                except:
                    logger.info(f"Auth0 login failed with status code (SSL disabled): {response.status_code}")
                return False, None
        except Exception as inner_e:
            logger.error(f"Error in fallback request: {str(inner_e)}")
            return False, None
    except Exception as e:
        logger.error(f"Error checking if user exists in Auth0: {str(e)}")
        return False, None

def create_auth0_user(email, password, username=None):
    """
    Create a new user in Auth0 using the Authentication API signup endpoint
    
    Args:
        email: User email
        password: User password
        username: Optional username
        
    Returns:
        tuple: (success, user_data)
            - success: Boolean indicating if creation was successful
            - user_data: Auth0 user data if successful, None otherwise
    """
    try:
        # Use the Authentication API signup endpoint
        url = f"https://{config['domain']}/dbconnections/signup"
        
        user_data = {
            'client_id': config['client_id'],
            'email': email,
            'password': password,
            'connection': 'Username-Password-Authentication'
        }
        
        if username:
            user_data['name'] = username
        
        # Add timeout and SSL verification
        response = requests.post(url, json=user_data, timeout=10, verify=True)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            try:
                error = response.json()
                error_msg = error.get('description', 'Unknown error')
                
                # Check if the error is because the user already exists
                if 'already exists' in error_msg:
                    logger.info(f"User {email} already exists in Auth0")
                    return False, None
                else:
                    logger.error(f"Error creating user in Auth0: {error_msg}")
                    return False, None
            except:
                logger.error(f"Error creating user in Auth0. Status code: {response.status_code}")
                return False, None
    except requests.exceptions.SSLError as ssl_err:
        logger.error(f"SSL Error connecting to Auth0: {str(ssl_err)}")
        # For development only - not recommended for production
        logger.warning("Attempting to connect without SSL verification...")
        try:
            response = requests.post(url, json=user_data, timeout=10, verify=False)
            if response.status_code == 200:
                return True, response.json()
            else:
                try:
                    error = response.json()
                    error_msg = error.get('description', 'Unknown error')
                    logger.error(f"Error creating user in Auth0 (SSL disabled): {error_msg}")
                except:
                    logger.error(f"Error creating user in Auth0 (SSL disabled). Status code: {response.status_code}")
                return False, None
        except Exception as inner_e:
            logger.error(f"Error in fallback request: {str(inner_e)}")
            return False, None
    except Exception as e:
        logger.error(f"Error creating user in Auth0: {str(e)}")
        return False, None

def send_password_reset_email(email):
    """
    Send a password reset email to the user
    
    Args:
        email: User email
        
    Returns:
        tuple: (success, error_message)
            - success: Boolean indicating if the email was sent successfully
            - error_message: Error message if not successful, None otherwise
    """
    try:
        url = f"https://{config['domain']}/dbconnections/change_password"
        payload = {
            'client_id': config['client_id'],
            'email': email,
            'connection': 'Username-Password-Authentication'
        }
        
        # Add timeout and SSL verification
        response = requests.post(url, json=payload, timeout=10, verify=True)
        
        if response.status_code == 200:
            logger.info(f"Password reset email sent to {email}")
            return True, None
        else:
            error_msg = response.text
            logger.error(f"Error sending password reset email: {error_msg}")
            return False, f"Error sending password reset email: {error_msg}"
    except requests.exceptions.SSLError as ssl_err:
        logger.error(f"SSL Error connecting to Auth0: {str(ssl_err)}")
        # For development only - not recommended for production
        logger.warning("Attempting to connect without SSL verification...")
        try:
            response = requests.post(url, json=payload, timeout=10, verify=False)
            if response.status_code == 200:
                logger.info(f"Password reset email sent to {email} (SSL disabled)")
                return True, None
            else:
                error_msg = response.text
                logger.error(f"Error sending password reset email (SSL disabled): {error_msg}")
                return False, f"Error sending password reset email: {error_msg}"
        except Exception as inner_e:
            logger.error(f"Error in fallback request: {str(inner_e)}")
            return False, f"Error sending password reset email: {str(inner_e)}"
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        return False, f"Error sending password reset email: {str(e)}"

def get_user_profile(access_token):
    """
    Get user profile information from Auth0
    
    Args:
        access_token: Auth0 access token
        
    Returns:
        dict: User profile data if successful, None otherwise
    """
    try:
        url = f"https://{config['domain']}/userinfo"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting user profile: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return None