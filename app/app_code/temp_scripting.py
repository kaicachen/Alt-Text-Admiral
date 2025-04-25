from dotenv import load_dotenv
from os import environ
from supabase import create_client, Client
from os.path import join
import json

# Load environmental variables
load_dotenv(".env")

# Get environmental variables
supabase_url: str = environ.get("SUPABASE_URL")
supabase_key: str = environ.get("SUPABASE_API_KEY")

# Initializes Supabase Connection
supabase: Client = create_client(supabase_url, supabase_key)

#i have a supabase client. Now i want to access site generations and save the websites atribute a s slist of strings

try:
    response = (
        supabase.table("Site Generations")
        .select("website")
        .execute()
        )
    
except Exception as e:
    print(f"Error reading from the database:ERROR: {e}")
    response = None

data_set:set = set()
for i in response.data:
    #print(i['website'])
    data_set.add(i['website'])

with open(join("app", "app_code", "inputs",  "websites.txt"), 'w') as file:
    json.dump(list(data_set), file)

