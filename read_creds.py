import json
import os

try:
    with open('credentials.json', 'r') as f:
        content = f.read()
        try:
            data = json.loads(content)
            print("Keep structure found:", list(data.keys()))
            if 'supabase' in data:
                print("Supabase Key Found:")
                print(json.dumps(data['supabase'], indent=2))
            else:
                print("No 'supabase' key found in JSON.")
                # Maybe it is flat?
                print("Dumping flat keys just in case:")
                for k in data:
                    if 'supabase' in k.lower() or 'key' in k.lower():
                        print(f"{k}: {str(data[k])[:10]}...") 
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print("Raw Content (first 500 chars):")
            print(content[:500])
except Exception as e:
    print(f"File Read Error: {e}")
