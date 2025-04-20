"""
Graph visualization utilities for the Kartr application.
Used for generating charts and data visualizations.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO

def generate_engagement_chart(data):
    """
    Generate an engagement chart for visualizing YouTube video performance.
    
    Args:
        data (dict): Dictionary containing engagement metrics like views, likes, comments.
        
    Returns:
        str: Base64 encoded image string of the chart.
    """
    if not data:
        return None
        
    # Extract data
    metrics = ['Views', 'Likes', 'Comments', 'Shares']
    values = [
        data.get('views', 0),
        data.get('likes', 0),
        data.get('comments', 0),
        data.get('shares', 0) if 'shares' in data else int(data.get('likes', 0) * 0.1)  # Estimate if not available
    ]
    
    # Create chart
    plt.figure(figsize=(10, 6))
    plt.bar(metrics, values, color=['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e'])
    plt.title('Video Engagement Metrics')
    plt.ylabel('Count')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Format y-axis labels to use K for thousands
    plt.gca().get_yaxis().set_major_formatter(
        plt.FuncFormatter(lambda x, loc: f"{int(x/1000)}K" if x >= 1000 else str(int(x)))
    )
    
    # Save to BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    
    # Encode to base64 for embedding in HTML
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_str

def generate_growth_chart(channel_data, days=30):
    """
    Generate a growth chart showing subscriber and view count trends over time.
    
    Args:
        channel_data (list): List of dictionaries with channel data over time.
        days (int): Number of days to show in the chart.
        
    Returns:
        str: Base64 encoded image string of the chart.
    """
    if not channel_data or len(channel_data) < 2:
        return None
        
    # Create dates (for demo purposes)
    import datetime
    end_date = datetime.datetime.now()
    date_list = [(end_date - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
    date_list.reverse()
    
    # Generate synthetic growth data based on current values
    current_subs = channel_data.get('subscriber_count', 10000)
    current_views = channel_data.get('view_count', 100000)
    
    # Generate growth curves
    import numpy as np
    growth_rate = 1.005  # 0.5% daily growth
    sub_values = [int(current_subs / (growth_rate ** (days-i-1))) for i in range(days)]
    view_values = [int(current_views / (growth_rate ** (days-i-1))) for i in range(days)]
    
    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot subscriber data on the first axis
    color = '#4e73df'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Subscribers', color=color)
    ax1.plot(date_list, sub_values, color=color, marker='o', markersize=3)
    ax1.tick_params(axis='y', labelcolor=color)
    # Only show some of the dates for x-axis clarity
    plt.xticks(date_list[::7], rotation=45)
    
    # Create a second y-axis
    ax2 = ax1.twinx()
    color = '#1cc88a'
    ax2.set_ylabel('Total Views', color=color)
    ax2.plot(date_list, view_values, color=color, marker='s', markersize=3)
    ax2.tick_params(axis='y', labelcolor=color)
    
    # Format the y-axis labels to use K/M for thousands/millions
    def format_number(x, pos):
        if x >= 1000000:
            return f"{x/1000000:.1f}M"
        elif x >= 1000:
            return f"{x/1000:.0f}K"
        else:
            return str(int(x))
            
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(format_number))
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(format_number))
    
    plt.title('Channel Growth Over Time')
    fig.tight_layout()
    
    # Save to BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    
    # Encode to base64 for embedding in HTML
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_str

def generate_content_performance_chart(video_data):
    """
    Generate a chart showing performance of different video types.
    
    Args:
        video_data (list): List of dictionaries with video data.
        
    Returns:
        str: Base64 encoded image string of the chart.
    """
    if not video_data or len(video_data) < 2:
        # Generate mock data for demonstration
        video_data = [
            {'type': 'Tutorial', 'engagement_rate': 4.2},
            {'type': 'Vlog', 'engagement_rate': 3.7},
            {'type': 'Review', 'engagement_rate': 5.1},
            {'type': 'Gameplay', 'engagement_rate': 3.9},
            {'type': 'Unboxing', 'engagement_rate': 4.8}
        ]
    
    # Extract data
    categories = [item['type'] for item in video_data]
    rates = [item['engagement_rate'] for item in video_data]
    
    # Create chart
    plt.figure(figsize=(10, 6))
    bars = plt.bar(categories, rates, color='#36b9cc')
    
    # Add values above bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.1f}%', ha='center', va='bottom')
    
    plt.title('Engagement Rate by Content Type')
    plt.ylabel('Engagement Rate (%)')
    plt.ylim(0, max(rates) + 1)  # Set y limit to max value + 1
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save to BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    
    # Encode to base64 for embedding in HTML
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_str

def load_analysis_data():
    """Load data from ANALYSIS.CSV for visualization."""
    analysis_csv = os.path.join(os.getcwd(), 'data/ANALYSIS.CSV')
    if os.path.exists(analysis_csv):
        try:
            df = pd.read_csv(analysis_csv)
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading analysis data: {e}")
    return []