import logging
import os
import subprocess
import pandas as pd
from datetime import datetime
from flask import render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from app import app, db
from forms import RegistrationForm, LoginForm, YouTubeStatsForm, YouTubeDemoForm
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
        user = User(username=form.username.data, email=form.email.data, user_type=form.user_type.data)
        user.set_password(form.password.data)

        # Save to database
        db.session.add(user)
        db.session.commit()

        # Also save to CSV file for validation
        save_user_to_csv(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            user_type=form.user_type.data
        )

        flash(f'Account created for {form.username.data}! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('stats'))

    form = LoginForm()
    if form.validate_on_submit():
        # First check in the SQL database
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Try CSV validation as fallback
            is_valid, user_type = validate_user_login(form.email.data, form.password.data)
            if is_valid:
                # Create a user in the database if not exists
                if not user:
                    # Get username from CSV
                    try:
                        df = pd.read_csv('data/database.csv')
                        user_data = df[df['email'] == form.email.data]
                        username = user_data.iloc[0]['username'] if not user_data.empty else form.email.data.split('@')[0] if '@' in form.email.data else form.email.data

                        # Create user in database
                        user = User(username=username, email=form.email.data, user_type=user_type)
                        user.set_password(form.password.data)
                        db.session.add(user)
                        db.session.commit()
                    except Exception as e:
                        logger.error(f"Error creating user from CSV: {str(e)}")

                    # Get the user again
                    user = User.query.filter_by(email=form.email.data).first()

                if user:
                    login_user(user)
                    flash('Login successful via CSV validation!', 'success')
                    return redirect(url_for('dashboard'))

            flash('Login unsuccessful. Please check email and password.', 'danger')

    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Use a specific column selection to avoid querying non-existent columns
    searches = db.session.query(
        Search.id, 
        Search.user_id, 
        Search.search_term, 
        Search.date_searched
    ).filter_by(user_id=current_user.id).order_by(Search.date_searched.desc()).limit(10).all()

    if current_user.user_type == 'influencer':
        youtube_channels = YouTubeChannel.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard.html', title='Dashboard', 
                              user_type='influencer', 
                              youtube_channels=youtube_channels,
                              searches=searches)
    else:  # sponsor
        return render_template('dashboard.html', title='Dashboard', 
                              user_type='sponsor',
                              searches=searches)

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
    
    # If user has no channels and is an influencer, this is their first time
    if not user_channels and current_user.user_type == 'influencer':
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
                        flash('Channel added successfully!', 'success')
                    else:
                        # Update existing channel
                        existing_channel.subscriber_count = channel_data['subscriber_count']
                        existing_channel.video_count = channel_data['video_count']
                        existing_channel.view_count = channel_data['view_count']
                        existing_channel.date_updated = datetime.utcnow()
                        flash('Channel statistics updated!', 'success')

                    db.session.commit()

                    # Run stats.py and save results to ANALYSIS.CSV
                    try:
                        # Convert channel data and video stats to string format for saving
                        stats_data = f"Channel Stats: {channel_data}\nVideo Stats: {video_data}"
                        save_analysis_to_csv(youtube_url, "", stats_data)
                        logger.info(f"Saved stats analysis to ANALYSIS.CSV for URL: {youtube_url}")
                    except Exception as stats_error:
                        logger.error(f"Error saving stats to ANALYSIS.CSV: {str(stats_error)}")
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
            api_key = app.config.get('YOUTUBE_API_KEY', 'YOUR_API_KEY_HERE')
            
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
            api_key = app.config.get('YOUTUBE_API_KEY', 'YOUR_API_KEY_HERE')
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
                    from youtube_utils import extract_video_id
                    from demo import get_transcript, analyze_transcript

                    # Get the video ID
                    video_id = extract_video_id(youtube_url)
                    if video_id:
                        # Get transcript
                        transcript = get_transcript(video_id)

                        # Analyze transcript (simplified version since we may not have API key)
                        analysis = f"Video Info: {info}\nExtracted from YouTube API"

                        # Save to ANALYSIS.CSV
                        save_analysis_to_csv(youtube_url, transcript, analysis)
                        logger.info(f"Saved demo analysis to ANALYSIS.CSV for URL: {youtube_url}")
                except Exception as demo_error:
                    logger.error(f"Error running demo analysis: {str(demo_error)}")
            else:
                error = "Could not extract information from the video."
        except Exception as e:
            logger.error(f"Error extracting video info: {str(e)}")
            error = f"Error extracting video info: {str(e)}"

    return render_template('demo.html', title='YouTube Demo',
                          form=form, 
                          video_info=video_info,
                          min=min)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('dashboard'))
    
    # Search in YouTube channels
    channels = YouTubeChannel.query.filter(
        YouTubeChannel.title.ilike(f'%{query}%')
    ).all()
    
    # Save the search
    search = Search(
        user_id=current_user.id,
        search_term=query,
        date_searched=datetime.utcnow()
    )
    db.session.add(search)
    db.session.commit()
    
    return render_template('search_results.html', 
                         title='Search Results',
                         query=query,
                         channels=channels)