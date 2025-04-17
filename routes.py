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
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('stats'))
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
                    return redirect(url_for('stats'))
            
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
    # Different views for sponsors and influencers
    searches = Search.query.filter_by(user_id=current_user.id).order_by(Search.date_searched.desc()).limit(10).all()
    
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
    
    if form.validate_on_submit():
        youtube_url = form.youtube_url.data
        try:
            # Get video stats
            video_data = get_video_stats(youtube_url)
            if video_data:
                video_stats = video_data
                
                # Get channel stats
                channel_data = get_channel_stats(video_data['channel_id'])
                if channel_data:
                    channel_stats = channel_data
                    
                    # Save the search
                    search = Search(
                        query=youtube_url,
                        video_id=video_data['video_id'],
                        search_type='stats',
                        user_id=current_user.id
                    )
                    db.session.add(search)
                    
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
                    else:
                        # Update existing channel
                        existing_channel.subscriber_count = channel_data['subscriber_count']
                        existing_channel.video_count = channel_data['video_count']
                        existing_channel.view_count = channel_data['view_count']
                    
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
                error = "Could not retrieve video information."
        except Exception as e:
            logger.error(f"Error processing YouTube URL: {str(e)}")
            error = f"Error processing YouTube URL: {str(e)}"
    
    return render_template('stats.html', title='YouTube Stats', 
                          form=form, 
                          video_stats=video_stats, 
                          channel_stats=channel_stats,
                          error=error,
                          user_type=current_user.user_type)

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
                search = Search(
                    query=youtube_url,
                    video_id=info['video_id'],
                    search_type='demo',
                    user_id=current_user.id
                )
                db.session.add(search)
                db.session.commit()
                
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
                          error=error,
                          user_type=current_user.user_type)
