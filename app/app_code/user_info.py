from supabase import create_client, Client
from dotenv import load_dotenv
from os import environ


class UserInfo:
    def __init__(self, username, email):
        # Load environmental variables
        load_dotenv(".env")

        # Get environmental variables
        supabase_url: str = environ.get("SUPABASE_URL")
        supabase_key: str = environ.get("SUPABASE_API_KEY")

        # Initializes Supabase Connection
        self._supabase: Client = create_client(supabase_url, supabase_key)

        # Store user information
        self.username = username
        self.email = email

        # Adds user to the database if they do not exist
        self._verify_user()


    '''Checks if User exists in the database and adds them if not'''
    def _verify_user(self):
        # Attempt to read from database
        response = (
            self._supabase.table("Users")
            .select("*")
            .eq("username", self.username)
            .execute()
            )

        # Updates the timestamp of the value if found in database
        if len(response.data):
            return
        
        # Add to database
        else:
            try:
                response = (
                    self._supabase.table("Users")
                    .insert({"username": self.username,
                            "email": self.email
                            })
                    .execute()
                    )
                
            except Exception as e:
                print(f"Error adding tuple to the database: username: {self.username}, email: {self.email}, ERROR: {e}")


    '''Display past generation options for a user'''
    def previous_generations(self):
        # Read from database
        response = (
            self._supabase.table("Site Generations")
            .select("*")
            .eq("username", self.username)
            .execute()
            )
        
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
        response = (
            self._supabase.table("Generation Data")
            .select("*")
            .eq("generation_id", generation_id)
            .execute()
            )
        
        # Initialize list to store data from the generation
        generation_data = []

        # Convert data to list of tuples
        for data in response.data:
            generation_data.append((
                data["image_url"],
                data["alt_text"],
            ))

        return generation_data
    

    '''Stores data from a generation'''
    def store_generation(self, website, generation_data):
        # Add to Site Generations table
        try:
            response = (
                self._supabase.table("Site Generations")
                .insert({"website": website,
                        "username": self.username
                        })
                .execute()
                )
            
        except Exception as e:
            print(f"Error adding tuple to the database: website: {website}, username: {self.username}, ERROR: {e}")

        # Store UUID for the generation
        generation_id = response[0]["generation_id"]

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
                
            except Exception as e:
                print(f"Error adding tuple to the database: generation_id: {generation_id}, image_url: {data[0]}, alt_text: {data[1]}, ERROR: {e}")

