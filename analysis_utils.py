import csv
import os
import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_analysis_to_csv(youtube_url, transcript_summary, analysis_results, filename="ANALYSIS.CSV"):
    """
    Save analysis results to a CSV file
    
    Parameters:
    - youtube_url: URL of the analyzed YouTube video
    - transcript_summary: Summary of the transcript (can be empty)
    - analysis_results: Dictionary containing the analysis results
    - filename: Name of the CSV file to save to
    """
    try:
        # Create the data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        file_path = os.path.join('data', filename)
        file_exists = os.path.isfile(file_path)
        
        # Format the analysis results
        if isinstance(analysis_results, dict):
            creator_name = analysis_results.get('creator_name', 'Unknown')
            creator_industry = analysis_results.get('creator_industry', 'Unknown')
            sponsor_name = analysis_results.get('sponsor_name', 'Unknown')
            sponsor_industry = analysis_results.get('sponsor_industry', 'Unknown')
        else:
            # If analysis_results is not a dict, use default values
            creator_name = 'Unknown'
            creator_industry = 'Unknown'
            sponsor_name = 'Unknown'
            sponsor_industry = 'Unknown'
        
        # Prepare the row to write
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row = [
            timestamp,
            youtube_url,
            creator_name,
            creator_industry,
            sponsor_name,
            sponsor_industry,
            transcript_summary[:500] if transcript_summary else ''  # Limit transcript length
        ]
        
        # Write to CSV
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write header if file doesn't exist
            if not file_exists:
                writer.writerow([
                    'Timestamp', 
                    'YouTube URL', 
                    'Creator Name', 
                    'Creator Industry', 
                    'Sponsor Name', 
                    'Sponsor Industry', 
                    'Transcript Summary'
                ])
            
            # Write the data row
            writer.writerow(row)
        
        logger.info(f"Successfully saved analysis to {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving analysis to CSV: {str(e)}")
        return False