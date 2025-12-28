import json
import urllib.parse
import os

def fix_env():
    with open('credentials.json', 'r') as f:
        creds = json.load(f)
        
    supabase = creds.get('supabase', {})
    raw_conn = supabase.get('db_connection_string')
    
    if not raw_conn:
        print("No connection string found")
        return

    # Expected format: postgresql://user:pass@host:port/db
    # Find last @
    last_at = raw_conn.rfind('@')
    if last_at == -1:
        print("Invalid format: no @")
        return
        
    scheme_user_pass = raw_conn[:last_at]
    host_part = raw_conn[last_at+1:]
    
    # Split scheme
    if '://' not in scheme_user_pass:
        print("Invalid format: no ://")
        return
        
    scheme, user_pass = scheme_user_pass.split('://', 1)
    
    # Split user:pass
    if ':' not in user_pass:
        print("Invalid format: no : in user_pass")
        return
        
    user, password = user_pass.split(':', 1)
    
    # Encode password
    encoded_password = urllib.parse.quote_plus(password)
    
    # Reassemble
    new_conn = f"{scheme}://{user}:{encoded_password}@{host_part}"
    
    print(f"Original: {raw_conn}")
    print(f"New:      {new_conn}")
    
    # Write .env
    env_content = f"""NEWSDATA_API_KEY={creds['news_data_io']['api_key']}
GEMINI_API_KEY={creds['gemini']['api_key']}
SUPABASE_URL={supabase.get('url')}
SUPABASE_SERVICE_ROLE_KEY={supabase.get('service_role_key')}
DATABASE_URL={new_conn}
RAW_DUMP_DIR=data/raw
"""
    
    with open('services/kitchen/.env', 'w') as f:
        f.write(env_content)
    print(".env updated")

if __name__ == "__main__":
    fix_env()
