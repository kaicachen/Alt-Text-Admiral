from supabase import create_client, Client
from smtplib import SMTP, SMTPException
from email.message import EmailMessage
from dotenv import load_dotenv
from datetime import datetime
from os import environ


class UserInfo:
    def __init__(self, user_id:int|None=None, email:str|None=None):
        # Load environmental variables
        load_dotenv(".env")

        # Get environmental variables
        supabase_url: str = environ.get("SUPABASE_URL")
        supabase_key: str = environ.get("SUPABASE_API_KEY")

        # Initializes Supabase Connection
        self._supabase: Client = create_client(supabase_url, supabase_key)

        # Store user ID
        self.user_id:int|None = user_id

        # Store user email
        self.email:str|None = email

        # Get user ID from database if not passed in
        if self.user_id is None and email is not None:
            # Adds user to the database if they do not exist
            self.user_id = self._get_user_id(email)

        # Get email from database if not passed in:
        if self.email is None and user_id is not None:
            self.email = self._get_email(user_id)


    '''Checks if User exists in the database and adds them if not'''
    def _get_user_id(self, email:str|None)-> int|None:
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
            

    '''Gets the email associated with a user ID'''
    def _get_email(self, user_id:int) -> str|None:
        # Attempt to read from database
        try:
            response = (
                self._supabase.table("Users")
                .select("*")
                .eq("user_id", user_id)
                .execute()
                )
            
        except Exception as e:
            print(f"Error reading user from the database: user_id: {user_id}, ERROR: {e}")
            response = None
            

        # Returns the user ID if found in the database and user is opted in
        if response and len(response.data):
            if response.data[0]["email_opt_in"]:
                return response.data[0]["email"]


    '''Display past generation options for a user'''
    def previous_generations(self)->list[tuple[int,str,str]]:
        # Read from database
        try:
            response = (
                self._supabase.table("Site Generations")
                .select("*")
                .eq("user_id", self.user_id)
                .order("generation_time", desc=True)
                .execute()
                )
            
        except Exception as e:
            print(f"Error reading generations from the database: user_id: {self.user_id} ERROR: {e}")
            return []
        
        # Initialize list to store past generations
        generation_list = []

        # Convert data to list of tuples
        for generation in response.data:
            # Convert string to datetime object
            dt = datetime.strptime(generation["generation_time"], "%Y-%m-%dT%H:%M:%S.%f")

            # Format to M/D/Y format
            formatted_time = dt.strftime("%m/%d/%y")

            generation_list.append((
                generation["generation_id"],
                generation["website"],
                formatted_time
            ))

        return generation_list
    

    '''Loads images and alt-text from previous generation'''
    def load_generation(self, generation_id:int)->tuple[list[tuple[str,str]],list[int]]:
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
            return [], []
        
        # Initialize list to store data from the generation
        generation_data = []
        data_ids = []

        # Convert data to list of tuples
        for data in response.data:
            # Uploaded image
            if data["image_url"] is None:
                # Read from database
                try:
                    uploaded_image_response = (
                        self._supabase.table("Uploaded Images")
                        .select("*")
                        .eq("image_id", data["image_id"])
                        .execute()
                        )
                    
                except Exception as e:
                    print(f"Error reading uploaded image from the database: image_id: {data['image_id']} ERROR: {e}")
                    # Add None as place holder for failed data
                    data_ids.append(None)
                    continue

                # Add image source and alt-text tuple
                generation_data.append((
                    uploaded_image_response.data[0]["image_src"],
                    data["alt_text"]
                ))

            # Standard scraped image
            else:
                generation_data.append((
                    data["image_url"],
                    data["alt_text"]
                ))

            data_ids.append(data["data_id"])

        return generation_data, data_ids
    

    '''Stores data from a generation'''
    def store_generation(self, website:str, generation_data:list[tuple[str,str]])->tuple[int|None, list[int|None]]:
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
        generation_id = response.data[0]["generation_id"]

        # Create list to store data IDs
        data_ids = []

        # Add each data tuple to the Generation Data table
        for data in generation_data:
            if data[0][:23] == "data:image/jpeg;base64,":
                # Add the uploaded image
                try:
                    response = (
                        self._supabase.table("Uploaded Images")
                        .insert({"generation_id": generation_id,
                                "image_src": data[0],
                                })
                        .execute()
                        )
                    
                    # Save the image ID to add to Generation Data
                    image_id = response.data[0]["image_id"]

                except Exception as e:
                    print(f"Error adding tuple to the database: generation_id: {generation_id}, image_src: {data[0]} ERROR: {e}")
                    # Add None as place holder for failed data
                    data_ids.append(None)
                    continue

                # Add the alt-text
                try:
                    response = (
                        self._supabase.table("Generation Data")
                        .insert({"generation_id": generation_id,
                                "image_id": image_id,
                                "alt_text": data[1]
                                })
                        .execute()
                        )
                    
                    # Save the data ID
                    data_ids.append(response.data[0]["data_id"])
                    
                except Exception as e:
                    print(f"Error adding tuple to the database: generation_id: {generation_id}, image_id: {image_id}, alt_text: {data[1]}, ERROR: {e}")
                    # Add None as place holder for failed data
                    data_ids.append(None)

            # Add the image, alt-text data
            else:
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
    
    
    '''Send an email to the user'''
    def email_user(self, subject:str, message_body:str)->None:
        # Early exit if no email stored
        if self.email is None:
            print("Email is not being sent")
            return
        
        # Load environmental variables
        load_dotenv()
        sending_email = environ.get("EMAIL_ADDRESS")
        password = environ.get("EMAIL_PASSWORD")

        if not sending_email or not password:
            print("Missing EMAIL_ADDRESS or EMAIL_PASSWORD in environment variables.")
            return

        try:
            # Create email message
            msg = EmailMessage()
            msg.set_content(message_body)
            msg["Subject"] = subject
            msg["From"] = sending_email
            msg["To"] = self.email

            # Send the email
            with SMTP("smtp.gmail.com", 587) as smtp:
                smtp.starttls()
                smtp.login(sending_email, password)
                smtp.send_message(msg)

            print("Email sent to user")
        
        except SMTPException as e:
            print(f"Error sending email: {e}")

        