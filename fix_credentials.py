import json
import os
from urllib.parse import urlparse

def clean_credentials():
    try:
        with open('credentials.json', 'r') as f:
            data = json.load(f)
            
        print("Successfully loaded JSON.")
        
        # Check Supabase consistency
        supabase = data.get('supabase', {})
        url = supabase.get('url')
        db_str = supabase.get('db_connection_string')
        
        print(f"Current URL: {url}")
        print(f"Current DB: {db_str}")
        
        if url and db_str:
            # Extract project ref from URL
            # https://PROJECT_ID.supabase.co
            parsed = urlparse(url)
            host = parsed.netloc
            project_id = host.split('.')[0]
            print(f"Project ID from URL: {project_id}")
            
            # Check if DB string uses this project ID
            if project_id not in db_str:
                print("WARNING: DB connection string does not contain Project ID from URL!")
                
                # Propose fix?
                if 'supabase.co' in db_str:
                    # Replace the host part
                    # finding @...:5432
                    import re
                    new_db_str = re.sub(r'@.*?\.supabase\.co:5432', f'@db.{project_id}.supabase.co:5432', db_str)
                    print(f"Proposed DB String: {new_db_str}")
                    data['supabase']['db_connection_string'] = new_db_str
                    
        # Write back cleaned
        with open('credentials.json', 'w') as f:
            json.dump(data, f, indent=2)
            
        print("Saved cleaned credentials.json")
        
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_credentials()
