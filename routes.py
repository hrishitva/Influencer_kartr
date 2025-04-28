import logging
import os
import subprocess
import pandas as pd
from datetime import datetime
import logging
from flask import render_template, url_for, flash, redirect, request, jsonify, session
from flask_login import login_user, current_user, logout_user, login_required
from app import app, db

# Set up logging
logger = logging.getLogger(__name__)

# Try to import Firebase components
try:
    from app import firebase_auth
    from firebase_helpers import user_exists_in_firebase, create_firebase_user
    FIREBASE_AVAILABLE = firebase_auth is not None
    if FIREBASE_AVAILABLE:
        logger.debug("Firebase authentication is available")
    else:
        logger.warning("Firebase authentication is not available (firebase_auth is None)")
except ImportError as e:
    logger.warning(f"Firebase authentication is not available: {e}")
    FIREBASE_AVAILABLE = False
    
    # Create dummy functions to avoid errors
    def user_exists_in_firebase(auth, email, password):
        return False, None
        
    def create_firebase_user(auth, email, password):
        return False, None
from forms import RegistrationForm, LoginForm, YouTubeStatsForm, YouTubeDemoForm, ForgotPasswordForm
from models import User, YouTubeChannel, Search
from youtube_api import get_video_stats, get_channel_stats, extract_video_info
from youtube_utils import save_user_to_csv, validate_user_login, save_analysis_to_csv
from googleapiclient.discovery import build

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/')
@app.route('/home')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('stats'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('stats'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # First check if user already exists in our database
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('A user with that email already exists. Please use a different email or log in.', 'danger')
            return render_template('register.html', title='Register', form=form)
        
        firebase_user = None
        # Try to create user in Firebase if available
        if FIREBASE_AVAILABLE:
            success, firebase_user = create_firebase_user(
                firebase_auth,
                form.email.data, 
                form.password.data
            )
            
            if not success:
                logger.warning(f"Failed to create user in Firebase: {form.email.data}")
                # We'll continue with local registration even if Firebase fails
        
        # Create user in our database
        user = User(username=form.username.data, email=form.email.data, user_type=form.user_type.data)
        user.set_password(form.password.data)

        try:
            # Save to database
            db.session.add(user)
            db.session.commit()

            # Also save to CSV file for validation
            save_user_to_csv(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                user_type=form.user_type.data,
                channel_id=''  # Initialize with empty channel_id
            )

            # Store Firebase user ID in session if Firebase is available
            if FIREBASE_AVAILABLE and firebase_user:
                session['firebase_user'] = form.email.data
                session['firebase_user_id'] = firebase_user['localId'] if firebase_user else None
                flash(f'Account created for {form.username.data} with Firebase integration!', 'success')
            else:
                flash(f'Account created for {form.username.data}!', 'success')
                
            return redirect(url_for('login'))
            
        except Exception as e:
            # If database creation fails, log the error and show a message
            logger.error(f"Database registration error: {str(e)}")
            flash('Registration failed. There was an issue with our database. Please try again.', 'danger')
            return render_template('register.html', title='Register', form=form)

    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('stats'))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            # First check if user exists in our database
            user = User.query.filter_by(email=form.email.data).first()
            
            firebase_exists = False
            firebase_user = None
            
            # Try Firebase authentication if available
            if FIREBASE_AVAILABLE:
                firebase_exists, firebase_user = user_exists_in_firebase(
                    firebase_auth,
                    form.email.data, 
                    form.password.data
                )
            
            if FIREBASE_AVAILABLE and firebase_exists:
                # User exists in Firebase
                logger.info(f"User {form.email.data} authenticated with Firebase")
                
                # Store Firebase user info in session
                session['firebase_user'] = form.email.data
                session['firebase_user_id'] = firebase_user['localId'] if firebase_user else None
                
                if not user:
                    # User exists in Firebase but not in our database, create them
                    username = form.email.data.split('@')[0] if '@' in form.email.data else form.email.data
                    user_type = 'influencer'  # Default user type
                    
                    # Create user in database
                    user = User(username=username, email=form.email.data, user_type=user_type)
                    user.set_password(form.password.data)
                    db.session.add(user)
                    db.session.commit()
                    
                    # Also save to CSV file for validation
                    save_user_to_csv(
                        username=username,
                        email=form.email.data,
                        password=form.password.data,
                        user_type=user_type,
                        channel_id=''  # Initialize with empty channel_id
                    )
                    
                    logger.info(f"Created user {form.email.data} in database from Firebase login")
                
                # Log the user in with Flask-Login
                login_user(user)
                flash('Login successful with Firebase!', 'success')
                return redirect(url_for('stats'))
                
            elif user and user.check_password(form.password.data):
                # User exists in our database
                
                # Try to create the user in Firebase if available and user doesn't exist there
                if FIREBASE_AVAILABLE and not firebase_exists:
                    success, firebase_user = create_firebase_user(
                        firebase_auth,
                        form.email.data, 
                        form.password.data
                    )
                    
                    if success:
                        logger.info(f"Created user {form.email.data} in Firebase from database login")
                        session['firebase_user'] = form.email.data
                        session['firebase_user_id'] = firebase_user['localId'] if firebase_user else None
                    else:
                        logger.warning(f"Failed to create user {form.email.data} in Firebase")
                
                # Log the user in with Flask-Login
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('stats'))
            else:
                # Try CSV validation as fallback
                is_valid, user_type = validate_user_login(form.email.data, form.password.data)
                if is_valid:
                    # Create a user in the database if not exists
                    if not user:
                        try:
                            df = pd.read_csv('data/database.csv')
                            user_data = df[df['email'] == form.email.data]
                            if not user_data.empty:
                                username = user_data.iloc[0]['username']
                            else:
                                username = form.email.data.split('@')[0] if '@' in form.email.data else form.email.data

                            # Create user in database
                            user = User(username=username, email=form.email.data, user_type=user_type)
                            user.set_password(form.password.data)
                            db.session.add(user)
                            db.session.commit()
                            
                            # Try to create the user in Firebase if available
                            if FIREBASE_AVAILABLE:
                                success, firebase_user = create_firebase_user(
                                    firebase_auth,
                                    form.email.data, 
                                    form.password.data
                                )
                                
                                if success:
                                    logger.info(f"Created user {form.email.data} in Firebase from CSV login")
                                    session['firebase_user'] = form.email.data
                                    session['firebase_user_id'] = firebase_user['localId'] if firebase_user else None
                            
                            # Get the user again
                            user = User.query.filter_by(email=form.email.data).first()
                            
                            if user:
                                login_user(user)
                                flash('Login successful via CSV validation!', 'success')
                                return redirect(url_for('stats'))
                        except Exception as e:
                            logger.error(f"Error creating user from CSV: {str(e)}")
                            flash('Error during login. Please try again.', 'danger')
                    else:
                        flash('Invalid email or password.', 'danger')
                else:
                    flash('Invalid email or password.', 'danger')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'danger')

    return render_template('login.html', title='Login', form=form)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    if current_user.is_authenticated:
        return redirect(url_for('stats'))
        
    # Check if Firebase is available
    if not FIREBASE_AVAILABLE:
        flash('Firebase authentication is not available. Password reset is not possible at this time.', 'warning')
        return redirect(url_for('login'))
        
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        
        # Import the send_password_reset_email function
        from firebase_helpers import send_password_reset_email
        
        # Send password reset email
        success, error_message = send_password_reset_email(firebase_auth, email)
        
        if success:
            flash('Password reset email sent. Please check your inbox and follow the instructions to reset your password.', 'success')
            return redirect(url_for('login'))
        else:
            flash(error_message, 'danger')
            
    return render_template('forgot_password.html', title='Forgot Password', form=form)

@app.route('/logout')
def logout():
    # Clear Firebase session variables
    if 'firebase_user' in session:
        session.pop('firebase_user')
    if 'firebase_user_id' in session:
        session.pop('firebase_user_id')
    
    # Standard Flask-Login logout
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/firebase-login', methods=['POST', 'GET'])
def firebase_login():
    # Check if Firebase is available
    if not FIREBASE_AVAILABLE:
        flash('Firebase authentication is not available. Please use standard login.', 'warning')
        return redirect(url_for('login'))
        
    if current_user.is_authenticated:
        return redirect(url_for('stats'))
        
    if 'firebase_user' in session:
        # User is already logged in with Firebase
        return redirect(url_for('stats'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            # Authenticate with Firebase
            user = firebase_auth.sign_in_with_email_and_password(email=email, password=password)
            
            # Store user info in session
            session['firebase_user'] = email
            
            # Check if user exists in our database
            db_user = User.query.filter_by(email=email).first()
            
            if not db_user:
                # Create a new user in our database
                username = email.split('@')[0]  # Use part before @ as username
                
                # Create a random password for database (they'll use Firebase to authenticate)
                import secrets
                random_password = secrets.token_hex(16)
                
                # Default to 'influencer' user type
                user_type = 'influencer'
                
                # Create user in database
                db_user = User(username=username, email=email, user_type=user_type)
                db_user.set_password(random_password)
                db.session.add(db_user)
                db.session.commit()
                
                # Also save to CSV file for validation
                from youtube_utils import save_user_to_csv
                save_user_to_csv(
                    username=username,
                    email=email,
                    password=random_password,
                    user_type=user_type,
                    channel_id=''  # Initialize with empty channel_id
                )
                
                flash(f'Account created with Firebase authentication!', 'success')
            
            # Log the user in with Flask-Login
            login_user(db_user)
            
            flash('Login successful with Firebase!', 'success')
            return redirect(url_for('stats'))
            
        except Exception as e:
            logger.error(f"Firebase login error: {str(e)}")
            flash('Failed to login with Firebase. Please check your credentials.', 'danger')
    
    return render_template('firebase_login.html', title='Firebase Login')
    
@app.route('/firebase-register', methods=['POST', 'GET'])
def firebase_register():
    # Check if Firebase is available
    if not FIREBASE_AVAILABLE:
        flash('Firebase authentication is not available. Please use standard registration.', 'warning')
        return redirect(url_for('register'))
        
    if current_user.is_authenticated:
        return redirect(url_for('stats'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')
        user_type = request.form.get('user_type', 'influencer')

        try:
            # Create user in Firebase
            user = firebase_auth.create_user_with_email_and_password(email=email, password=password)
            
            # Create user in our database
            db_user = User(username=username, email=email, user_type=user_type)
            db_user.set_password(password)  # Store the same password in our database
            db.session.add(db_user)
            db.session.commit()
            
            # Also save to CSV file for validation
            from youtube_utils import save_user_to_csv
            save_user_to_csv(
                username=username,
                email=email,
                password=password,
                user_type=user_type,
                channel_id=''  # Initialize with empty channel_id
            )
            
            # Store user info in session
            session['firebase_user'] = email
            
            # Log the user in with Flask-Login
            login_user(db_user)
            
            flash(f'Account created for {username} with Firebase authentication!', 'success')
            return redirect(url_for('stats'))
            
        except Exception as e:
            logger.error(f"Firebase registration error: {str(e)}")
            flash('Failed to register with Firebase. Please try again.', 'danger')
    
    return render_template('firebase_register.html', title='Firebase Register')



# Keep the old route for backward compatibility, redirecting to the new one
@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('visualizations'))

@app.route('/stats', methods=['GET', 'POST'])
@login_required
def stats():
    form = YouTubeStatsForm()
    video_stats = None
    channel_stats = None
    error = None
    is_first_time = False
    auto_update = False

    # Check if user has any YouTube channels
    user_channels = YouTubeChannel.query.filter_by(user_id=current_user.id).all()
    
    # If user has no channels and is an influencer, check if they have a channel ID in the CSV file
    if not user_channels and current_user.user_type == 'influencer':
        # Check if user has a channel ID in the CSV file
        import os
        import csv
        from youtube_utils import DATABASE_CSV
        
        if os.path.exists(DATABASE_CSV):
            try:
                with open(DATABASE_CSV, 'r', newline='') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        if row.get('email') == current_user.email and row.get('channel_id'):
                            # User has a channel ID in the CSV file, let's create a YouTubeChannel record
                            channel_id = row.get('channel_id')
                            
                            # Get channel stats using the channel ID
                            from stats import get_channel_stats, API_KEY
                            channel_url = f"https://www.youtube.com/channel/{channel_id}"
                            channel_data = get_channel_stats(channel_url, API_KEY)
                            
                            if isinstance(channel_data, dict):
                                # Create a new YouTubeChannel record
                                new_channel = YouTubeChannel(
                                    channel_id=channel_data['channel_id'],
                                    title=channel_data['title'],
                                    subscriber_count=channel_data['subscriber_count'],
                                    video_count=channel_data['video_count'],
                                    view_count=channel_data['view_count'],
                                    user_id=current_user.id
                                )
                                db.session.add(new_channel)
                                db.session.commit()
                                
                                # Update user_channels
                                user_channels = [new_channel]
                                
                                flash('Your YouTube channel information has been loaded automatically!', 'success')
                                break
            except Exception as e:
                logger.error(f"Error checking CSV for channel ID: {str(e)}")
        
        # If still no channels, this is their first time
        if not user_channels:
            is_first_time = True
            flash('Welcome! Please enter your YouTube channel URL to get started.', 'info')
    
    # If user has channels, check if we need to auto-update
    elif user_channels and current_user.user_type == 'influencer':
        # Check if any channel needs updating (older than 24 hours)
        for channel in user_channels:
            if (datetime.utcnow() - channel.date_updated).total_seconds() > 86400:  # 24 hours
                auto_update = True
                break
    
    if form.validate_on_submit():
        youtube_url = form.youtube_url.data
        try:
            # Get video stats
            video_data = get_video_stats(youtube_url)
            if video_data:
                video_stats = video_data

                # Get channel stats using the enhanced stats.py
                from stats import get_channel_stats, API_KEY
                channel_data = get_channel_stats(youtube_url, API_KEY)
                
                if isinstance(channel_data, dict):  # Make sure we got valid data
                    channel_stats = channel_data

                    # Save the search
                    try:
                        # Only use fields that exist in the database
                        search = Search(
                            user_id=current_user.id,
                            search_term=youtube_url,
                            date_searched=datetime.utcnow()
                        )
                        db.session.add(search)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Error saving search history: {str(e)}")

                    # Check if channel already exists
                    existing_channel = YouTubeChannel.query.filter_by(
                        channel_id=channel_data['channel_id'],
                        user_id=current_user.id
                    ).first()

                    if not existing_channel:
                        # Save channel data
                        new_channel = YouTubeChannel(
                            channel_id=channel_data['channel_id'],
                            title=channel_data['title'],
                            subscriber_count=channel_data['subscriber_count'],
                            video_count=channel_data['video_count'],
                            view_count=channel_data['view_count'],
                            user_id=current_user.id
                        )
                        db.session.add(new_channel)
                        
                        # Also update the channel_id in the CSV file
                        from youtube_utils import update_channel_id
                        update_channel_id(current_user.email, channel_data['channel_id'])
                        
                        flash('Channel added successfully! You won\'t need to enter this information again.', 'success')
                    else:
                        # Update existing channel
                        existing_channel.subscriber_count = channel_data['subscriber_count']
                        existing_channel.video_count = channel_data['video_count']
                        existing_channel.view_count = channel_data['view_count']
                        existing_channel.date_updated = datetime.utcnow()
                        flash('Channel statistics updated!', 'success')

                    db.session.commit()

                    # We're not saving stats data to ANALYSIS.CSV anymore
                    # ANALYSIS.CSV is only updated from the demo page
                else:
                    error = "Could not retrieve channel information."
            else:
                error = "Could not retrieve video information."
        except Exception as e:
            logger.error(f"Error processing YouTube URL: {str(e)}")
            error = f"Error processing YouTube URL: {str(e)}"
    
    # Auto-update channel statistics if needed
    elif auto_update and user_channels:
        try:
            from stats import get_channel_stats
            api_key = app.config.get('YOUTUBE_API_KEY', '')
            if not api_key:
                logger.warning("YouTube API key not set. Please add it to your environment variables.")
                
            for channel in user_channels:
                channel_url = f"https://www.youtube.com/channel/{channel.channel_id}"
                channel_data = get_channel_stats(channel_url, api_key)
                
                if isinstance(channel_data, dict):
                    # Update channel data
                    channel.subscriber_count = channel_data['subscriber_count']
                    channel.video_count = channel_data['video_count']
                    channel.view_count = channel_data['view_count']
                    channel.date_updated = datetime.utcnow()
                    
                    # Get the most recent video for stats
                    if channel_data.get('recent_videos'):
                        video_id = channel_data['recent_videos'][0]['video_id']
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        video_data = get_video_stats(video_url)
                        if video_data:
                            video_stats = video_data
                            channel_stats = channel_data
                            break
            
            db.session.commit()
            flash('Channel statistics automatically updated!', 'success')
        except Exception as e:
            logger.error(f"Error auto-updating channel statistics: {str(e)}")
            flash('Could not automatically update channel statistics.', 'warning')
    
    # If user has channels but no video_stats, get the most recent video
    elif user_channels and not video_stats:
        try:
            # Get the most recently updated channel
            recent_channel = max(user_channels, key=lambda x: x.date_updated)
            
            # Get recent videos for this channel
            from stats import get_recent_videos
            api_key = app.config.get('YOUTUBE_API_KEY', '')
            if not api_key:
                logger.warning("YouTube API key not set. Please add it to your environment variables.")
                flash('YouTube API key is not set. Some features may not work properly.', 'warning')
                return render_template('stats.html', title='YouTube Stats', form=form)
            
            youtube = build('youtube', 'v3', developerKey=api_key)
            
            recent_videos = get_recent_videos(youtube, recent_channel.channel_id, api_key)
            
            if recent_videos:
                video_id = recent_videos[0]['video_id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                video_data = get_video_stats(video_url)
                
                if video_data:
                    video_stats = video_data
                    
                    # Get channel stats
                    from stats import get_channel_stats
                    channel_url = f"https://www.youtube.com/channel/{recent_channel.channel_id}"
                    channel_data = get_channel_stats(channel_url, api_key)
                    
                    if isinstance(channel_data, dict):
                        channel_stats = channel_data
        except Exception as e:
            logger.error(f"Error getting recent video: {str(e)}")

    return render_template('stats.html', title='YouTube Stats', 
                          form=form, 
                          video_stats=video_stats, 
                          channel_stats=channel_stats,
                          error=error,
                          user_type=current_user.user_type,
                          is_first_time=is_first_time,
                          auto_update=auto_update,
                          min=min)  # Add the min function to the template context

@app.route('/demo', methods=['GET', 'POST'])
@login_required
def demo():
    form = YouTubeDemoForm()
    video_info = None
    error = None

    if form.validate_on_submit():
        youtube_url = form.youtube_url.data
        try:
            # Extract information from the video using youtube_api.py
            info = extract_video_info(youtube_url)
            if info:
                video_info = info

                # Save the search
                try:
                    # Try to create a Search with only the columns that exist in the database
                    search = Search(
                        user_id=current_user.id,
                        search_term=youtube_url,  # Changed from url to youtube_url
                        date_searched=datetime.utcnow()
                    )
                    db.session.add(search)
                    db.session.commit()
                except Exception as e:
                    # If there's an error, roll back the session
                    db.session.rollback()
                    print(f"Error saving search history: {str(e)}")

                # Also run demo.py functionality to extract transcript and save to ANALYSIS.CSV
                try:
                    # Use the analyze_influencer_sponsors function from demo.py
                    result = analyze_influencer_sponsors(youtube_url)
                    if result and not "error" in result:
                        # Add influencer analysis to video_info
                        video_info['influencer_analysis'] = result
                        logger.info(f"Added influencer analysis for URL: {youtube_url}")
                except Exception as demo_error:
                    logger.error(f"Error running influencer analysis: {str(demo_error)}")
            else:
                error = "Could not extract information from the video."
        except Exception as e:
            logger.error(f"Error extracting video info: {str(e)}")
            error = f"Error extracting video info: {str(e)}"

    return render_template('demo.html', title='YouTube Demo',
                          form=form, 
                          video_info=video_info,
                          min=min)

# Virtual Influencer routes
@app.route('/virtual-influencer')
@login_required
def virtual_influencer():
    # Import from virtual_influencer.py
    from virtual_influencer import get_available_virtual_influencers
    
    # Get available virtual influencers
    influencers = get_available_virtual_influencers()
    
    return render_template('virtual_influencer.html', 
                          title='Rent a Virtual Influencer',
                          influencers=influencers)

@app.route('/social-media-agents')
@login_required
def social_media_agents():
    # Import from social_media_agents.py
    from social_media_agents import get_available_agents
    
    # Get available social media agents
    agents = get_available_agents()
    
    return render_template('social_media_agents.html',
                          title='Social Media Agents',
                          agents=agents)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('visualizations'))
    
    # Search in YouTube channels
    channels = YouTubeChannel.query.filter(
        YouTubeChannel.title.ilike(f'%{query}%')
    ).all()
    
    # Save the search to the database
    search = Search(
        user_id=current_user.id,
        search_term=query,
        date_searched=datetime.utcnow()
    )
    db.session.add(search)
    db.session.commit()
    
    # Get searchable users from database.csv (those with public_email enabled)
    users = []
    # Define the database CSV path
    DATABASE_CSV = os.path.join(os.getcwd(), 'data/database.csv')
    
    if os.path.exists(DATABASE_CSV):
        try:
            import pandas as pd
            df = pd.read_csv(DATABASE_CSV)
            # Filter users with public email that match query
            if 'public_email' in df.columns:
                # Only show users who have toggled public_email to True
                user_matches = df[
                    (df['username'].str.contains(query, case=False, na=False) | 
                     df['email'].str.contains(query, case=False, na=False)) &
                    (df['public_email'].astype(str) == 'True')
                ]
                
                if not user_matches.empty:
                    # Convert to dictionary records
                    users = user_matches.to_dict('records')
                    
                    # Debug logging
                    logger.debug(f"Found {len(users)} users with public email matching '{query}'")
                else:
                    logger.debug(f"No users with public email found matching '{query}'")
            else:
                logger.warning("public_email column not found in database.csv")
        except Exception as e:
            logger.error(f"Error searching users in CSV: {str(e)}")
    
    return render_template('search_results.html', 
                         title='Search Results',
                         query=query,
                         channels=channels,
                         users=users)

@app.route('/api/search_suggestions', methods=['GET'])
def api_search_suggestions():
    """API endpoint for search suggestions (autocomplete)"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    suggestions = []
    
    # Get YouTube channel suggestions
    channels = YouTubeChannel.query.filter(
        YouTubeChannel.title.ilike(f'%{query}%')
    ).limit(5).all()
    
    for channel in channels:
        suggestions.append({
            'id': f"channel_{channel.id}",
            'text': channel.title,
            'type': 'channel'
        })
    
    # Get user suggestions from database.csv (respecting privacy settings)
    from youtube_utils import search_users
    user_results = search_users(query, respect_privacy=True)
    
    for user in user_results:
        suggestions.append({
            'id': f"user_{user.get('username')}",
            'text': user.get('username'),
            'email': user.get('email'),
            'type': user.get('user_type')
        })
    
    return jsonify(suggestions)

    
# Import functions from demo.py - fix the imports to match what's actually in demo.py
from demo import analyze_influencer_sponsors, batch_analyze_channel

# Add these functions to your demo.py file or import them from elsewhere if they exist
import csv

@app.route('/analyze_video', methods=['POST'])
@login_required
def analyze_video():
    """Analyze a YouTube video for influencer and sponsor information"""
    data = request.json
    video_url = data.get('video_url')
    
    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400
    
    try:
        # Use the analyze_influencer_sponsors function from demo.py
        result = analyze_influencer_sponsors(video_url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze_channel', methods=['POST'])
@login_required
def analyze_channel():
    """Analyze a YouTube channel for influencer and sponsor information"""
    data = request.json
    channel_id = data.get('channel_id')
    max_videos = int(data.get('max_videos', 5))
    
    if not channel_id:
        return jsonify({"error": "No channel ID provided"}), 400
    
    try:
        # Use the batch_analyze_channel function from demo.py
        result = batch_analyze_channel(channel_id, max_videos=max_videos)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/save_analysis', methods=['POST'])
@login_required
def save_analysis():
    """Save analysis data to CSV file"""
    data = request.json
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # CSV file path
    csv_file = 'data/analysis_results.csv'
    file_exists = os.path.isfile(csv_file)
    
    try:
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if file doesn't exist
            if not file_exists:
                writer.writerow([
                    'Date', 'User ID', 'Video/Channel Title', 'Channel Name',
                    'Creator Name', 'Creator Industry', 'Sponsor Name', 'Sponsor Industry'
                ])
            
            # Write creator row with no sponsor
            if not data.get('sponsors'):
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    current_user.id,
                    data.get('video_title', 'Unknown'),
                    data.get('channel_name', 'Unknown'),
                    data.get('creator_name', 'Unknown'),
                    data.get('creator_industry', 'Unknown'),
                    'No Sponsor',
                    'N/A'
                ])
            else:
                # Write a row for each sponsor
                for sponsor in data.get('sponsors', []):
                    writer.writerow([
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        current_user.id,
                        data.get('video_title', 'Unknown'),
                        data.get('channel_name', 'Unknown'),
                        data.get('creator_name', 'Unknown'),
                        data.get('creator_industry', 'Unknown'),
                        sponsor.get('name', 'Unknown'),
                        sponsor.get('industry', 'Unknown')
                    ])
        
        return jsonify({"success": True, "message": "Analysis saved to CSV"})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

from graph import load_creator_sponsor_graph, load_industry_graph

@app.route('/visualization')
def visualization():
    return render_template('visualization.html')

@app.route('/api/creator_sponsor_graph')
def api_creator_sponsor_graph():
    return jsonify(load_creator_sponsor_graph())

@app.route('/api/industry_graph')
def api_industry_graph():
    return jsonify(load_industry_graph())