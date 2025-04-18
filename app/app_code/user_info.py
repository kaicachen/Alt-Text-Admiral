from supabase import create_client, Client
from dotenv import load_dotenv
from os import environ


class UserInfo:
    def __init__(self, user_id=None, email=None):
        # Load environmental variables
        load_dotenv(".env")

        # Get environmental variables
        supabase_url: str = environ.get("SUPABASE_URL")
        supabase_key: str = environ.get("SUPABASE_API_KEY")

        # Initializes Supabase Connection
        self._supabase: Client = create_client(supabase_url, supabase_key)

        # Store user ID
        self.user_id = user_id

        # Get user ID from database if not passed in
        if self.user_id is None:
            # Adds user to the database if they do not exist
            self.user_id = self._get_user_id(email)


    '''Checks if User exists in the database and adds them if not'''
    def _get_user_id(self, email):
        # Attempt to read from database
        try:
            response = (
                self._supabase.table("Users")
                .select("*")
                .eq("email", email)
                .execute()
                )
            
        except Exception as e:
            print(f"Error reading user from the database: email: {email}, ERROR: {e}")
            response = None
            

        # Returns the user ID if found in the database
        if response and len(response.data):
            return int(response.data[0]["user_id"])
        
        # Add to database
        else:
            try:
                response = (
                    self._supabase.table("Users")
                    .insert({"email": email})
                    .execute()
                    )
                
                # Returns the user ID
                return int(response.data[0]["user_id"])
                
            except Exception as e:
                print(f"Error adding tuple to the database: email: {email}, ERROR: {e}")
                return None


    '''Display past generation options for a user'''
    def previous_generations(self):
        # Read from database
        try:
            response = (
                self._supabase.table("Site Generations")
                .select("*")
                .eq("user_id", self.user_id)
                .execute()
                )
            
        except Exception as e:
            print(f"Error reading generations from the database: user_id: {self.user_id} ERROR: {e}")
            return []
        
        # Initialize list to store past generations
        generation_list = []

        # Convert data to list of tuples
        for generation in response.data:
            generation_list.append((
                generation["generation_id"],
                generation["website"],
                generation["generation_time"]
            ))

        return generation_list
    

    '''Loads images and alt-text from previous generation'''
    def load_generation(self, generation_id):
        # Read from database
        try:
            response = (
                self._supabase.table("Generation Data")
                .select("*")
                .eq("generation_id", generation_id)
                .order("data_id")
                .execute()
                )
            
        except Exception as e:
            print(f"Error reading generation data from the database: generation_id: {generation_id} ERROR: {e}")
            return []
        
        # Initialize list to store data from the generation
        generation_data = []

        # Convert data to list of tuples
        for data in response.data:
            generation_data.append((
                data["image_url"],
                data["alt_text"],
                data["data_id"]
            ))

        return generation_data
    

    '''Stores data from a generation'''
    def store_generation(self, website, generation_data):
        # Add to Site Generations table
        try:
            response = (
                self._supabase.table("Site Generations")
                .insert({"website": website,
                        "user_id": self.user_id
                        })
                .execute()
                )
            
        except Exception as e:
            print(f"Error adding generation to the database: website: {website}, user_id: {self.user_id}, ERROR: {e}")
            return None, ([None] * len(generation_data))

        # Store ID for the generation
        print(response.data)
        generation_id = response.data[0]["generation_id"]

        # Create list to store data IDs
        data_ids = []

        # Add each data tuple to the Generation Data table
        for data in generation_data:
            try:
                response = (
                    self._supabase.table("Generation Data")
                    .insert({"generation_id": generation_id,
                            "image_url": data[0],
                            "alt_text": data[1]
                            })
                    .execute()
                    )
                
                # Save the data ID
                data_ids.append(response.data[0]["data_id"])
                
            except Exception as e:
                print(f"Error adding tuple to the database: generation_id: {generation_id}, image_url: {data[0]}, alt_text: {data[1]}, ERROR: {e}")
                # Add None as place holder for failed data
                data_ids.append(None)

        return generation_id, data_ids

