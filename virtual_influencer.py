"""
Virtual Influencer module for the Kartr application.
Provides functionality for renting and managing virtual influencers.
"""
import os
import json
import uuid
from datetime import datetime, timedelta

# Path to store virtual influencer data
VIRTUAL_INFLUENCERS_DIR = os.path.join(os.getcwd(), 'data/virtual_influencers')
RENTALS_FILE = os.path.join(VIRTUAL_INFLUENCERS_DIR, 'rentals.json')

# Create directory if it doesn't exist
os.makedirs(VIRTUAL_INFLUENCERS_DIR, exist_ok=True)

# Sample influencer profiles (in production, these would come from a database)
VIRTUAL_INFLUENCER_PROFILES = [
    {
        "id": "vi_001",
        "name": "Luna Virtual",
        "specialty": "Fashion & Lifestyle",
        "followers": 1250000,
        "engagement_rate": 4.8,
        "daily_rate": 1200,
        "description": "Luna is a digital fashion icon known for her trendsetting style and authentic brand partnerships.",
        "image_url": "https://example.com/luna.jpg"
    },
    {
        "id": "vi_002",
        "name": "Nexus Gaming",
        "specialty": "Gaming & Tech",
        "followers": 2100000,
        "engagement_rate": 5.7,
        "daily_rate": 1800,
        "description": "Nexus is a virtual gaming personality who specializes in game reviews, tech unboxings, and eSports commentary.",
        "image_url": "https://example.com/nexus.jpg"
    },
    {
        "id": "vi_003",
        "name": "Vela Beauty",
        "specialty": "Beauty & Cosmetics",
        "followers": 980000,
        "engagement_rate": 6.2,
        "daily_rate": 950,
        "description": "Vela is a digital beauty influencer who tests the latest cosmetic products and shares makeup tutorials.",
        "image_url": "https://example.com/vela.jpg"
    },
    {
        "id": "vi_004",
        "name": "Aero Travel",
        "specialty": "Travel & Adventure",
        "followers": 1450000,
        "engagement_rate": 5.3,
        "daily_rate": 1300,
        "description": "Aero is a virtual travel blogger who showcases exotic destinations and adventure experiences.",
        "image_url": "https://example.com/aero.jpg"
    },
    {
        "id": "vi_005",
        "name": "Chef Pixel",
        "specialty": "Food & Cooking",
        "followers": 750000,
        "engagement_rate": 7.1,
        "daily_rate": 850,
        "description": "Chef Pixel is a digital culinary expert who shares innovative recipes and cooking techniques.",
        "image_url": "https://example.com/pixel.jpg"
    }
]

def get_available_virtual_influencers():
    """
    Get a list of all available virtual influencers.
    
    Returns:
        list: List of virtual influencer profile dictionaries.
    """
    return VIRTUAL_INFLUENCER_PROFILES

def get_virtual_influencer_by_id(influencer_id):
    """
    Get a virtual influencer profile by ID.
    
    Args:
        influencer_id (str): The ID of the virtual influencer.
        
    Returns:
        dict: Virtual influencer profile or None if not found.
    """
    for profile in VIRTUAL_INFLUENCER_PROFILES:
        if profile["id"] == influencer_id:
            return profile
    return None

def rent_virtual_influencer(user_id, influencer_id, start_date, duration_days, campaign_details):
    """
    Rent a virtual influencer for a campaign.
    
    Args:
        user_id (int): ID of the user renting the influencer.
        influencer_id (str): ID of the virtual influencer.
        start_date (str): Start date in format 'YYYY-MM-DD'.
        duration_days (int): Number of days to rent.
        campaign_details (dict): Details about the campaign.
        
    Returns:
        dict: Rental information including confirmation ID.
    """
    influencer = get_virtual_influencer_by_id(influencer_id)
    if not influencer:
        return {"error": "Virtual influencer not found"}
    
    # Calculate rental details
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = start + timedelta(days=duration_days)
        total_cost = influencer["daily_rate"] * duration_days
        
        # Create rental record
        rental = {
            "rental_id": str(uuid.uuid4()),
            "user_id": user_id,
            "influencer_id": influencer_id,
            "influencer_name": influencer["name"],
            "start_date": start_date,
            "end_date": end.strftime('%Y-%m-%d'),
            "duration_days": duration_days,
            "total_cost": total_cost,
            "campaign_details": campaign_details,
            "status": "confirmed",
            "date_created": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save to rental file
        save_rental(rental)
        
        return {
            "status": "success",
            "rental_id": rental["rental_id"],
            "influencer_name": influencer["name"],
            "start_date": start_date,
            "end_date": end.strftime('%Y-%m-%d'),
            "total_cost": total_cost
        }
    except Exception as e:
        return {"error": f"Error processing rental: {str(e)}"}

def save_rental(rental):
    """
    Save a rental record to the rentals file.
    
    Args:
        rental (dict): Rental information to save.
    """
    rentals = []
    if os.path.exists(RENTALS_FILE):
        try:
            with open(RENTALS_FILE, 'r') as f:
                rentals = json.load(f)
        except:
            rentals = []
    
    rentals.append(rental)
    
    with open(RENTALS_FILE, 'w') as f:
        json.dump(rentals, f, indent=2)

def get_user_rentals(user_id):
    """
    Get all rentals for a specific user.
    
    Args:
        user_id (int): ID of the user.
        
    Returns:
        list: List of rental records for the user.
    """
    if not os.path.exists(RENTALS_FILE):
        return []
    
    try:
        with open(RENTALS_FILE, 'r') as f:
            rentals = json.load(f)
        
        # Filter rentals for this user
        user_rentals = [r for r in rentals if r["user_id"] == user_id]
        return user_rentals
    except Exception as e:
        print(f"Error getting user rentals: {str(e)}")
        return []

def calculate_campaign_metrics(rental_id):
    """
    Calculate estimated performance metrics for a virtual influencer campaign.
    
    Args:
        rental_id (str): ID of the rental.
        
    Returns:
        dict: Dictionary with estimated campaign metrics.
    """
    # In a real implementation, this would use more sophisticated algorithms
    # based on historical performance data
    
    if not os.path.exists(RENTALS_FILE):
        return {"error": "No rental records found"}
    
    try:
        with open(RENTALS_FILE, 'r') as f:
            rentals = json.load(f)
        
        # Find the specific rental
        rental = next((r for r in rentals if r["rental_id"] == rental_id), None)
        if not rental:
            return {"error": "Rental not found"}
        
        # Get the influencer details
        influencer = get_virtual_influencer_by_id(rental["influencer_id"])
        if not influencer:
            return {"error": "Influencer not found"}
        
        # Calculate estimated metrics
        est_impressions = influencer["followers"] * rental["duration_days"] * 0.7
        est_engagements = est_impressions * (influencer["engagement_rate"] / 100)
        est_clicks = est_engagements * 0.15
        est_conversions = est_clicks * 0.03
        
        return {
            "rental_id": rental_id,
            "influencer_name": influencer["name"],
            "campaign_duration": rental["duration_days"],
            "estimated_impressions": int(est_impressions),
            "estimated_engagements": int(est_engagements),
            "estimated_clicks": int(est_clicks),
            "estimated_conversions": int(est_conversions),
            "roi_factor": round((est_conversions * 50) / rental["total_cost"], 2)  # Assuming $50 per conversion
        }
    except Exception as e:
        return {"error": f"Error calculating campaign metrics: {str(e)}"}