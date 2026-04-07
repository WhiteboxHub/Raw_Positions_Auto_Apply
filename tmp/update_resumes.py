import json
import glob
from datetime import datetime

for file in glob.glob('resume/*/*.json'):
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Calculate total experience
    experiences = data.get('cv', {}).get('sections', {}).get('experience', [])
    if experiences:
        earliest_date_str = None
        for exp in experiences:
            sd = exp.get('date', {}).get('start_date')
            if sd:
                if not earliest_date_str or sd < earliest_date_str:
                    earliest_date_str = sd
        
        if earliest_date_str:
            try:
                # Format is usually YYYY-MM
                start_year = int(earliest_date_str.split('-')[0])
                start_month = int(earliest_date_str.split('-')[1])
                current_year = 2026
                current_month = 4
                total_years = current_year - start_year
                if current_month < start_month:
                    total_years -= 1
                
                # Add total_experience right under email/phone for visibility
                data['cv']['total_experience'] = f'{total_years}+ years'
            except Exception as e:
                print(f'Error calculating for {file}: {e}')
                data['cv']['total_experience'] = 'Unknown'
    
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f'Updated {file} - Total Experience: {data.get("cv", {}).get("total_experience")}')
