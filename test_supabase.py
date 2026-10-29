from supabase_client import supabase

try:
    result = supabase.auth.get_session()
    print("Supabase client initialized successfully!")
except Exception as e:
    print("Error:")
    print(e)