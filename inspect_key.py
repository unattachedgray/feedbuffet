import json
import base64
import os

def decode_jwt_fragments():
    try:
        with open('credentials.json', 'r') as f:
            data = json.load(f)
            
        auth_key = data.get('supabase', {}).get('anon_key') or data.get('supabase', {}).get('service_role_key')
        
        if not auth_key:
            print("No auth key found")
            return

        print(f"Inspecting Key: {auth_key[:20]}...")
        
        # JWT is header.payload.signature
        parts = auth_key.split('.')
        if len(parts) != 3:
            print("Not a valid JWT structure")
            return
            
        # Decode payload (part 1)
        payload = parts[1]
        # Fix padding
        payload += '=' * (-len(payload) % 4)
        
        decoded_bytes = base64.b64decode(payload)
        claims = json.loads(decoded_bytes)
        
        print("JWT Claims:")
        print(json.dumps(claims, indent=2))
        
        # Sometimes 'iss' or custom claims have the URL
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    decode_jwt_fragments()
