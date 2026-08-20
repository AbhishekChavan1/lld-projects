class User():
    def __init__(self, user_id: int, name: str, email: str):
        self.user_id: int = user_id
        self.name: str = name
        self.email: str = email      

    def display_info(self):
        print(f"User ID: {self.user_id}, Name: {self.name}, Email: {self.email}")

    def __str__(self):
        return f"User ID: {self.user_id}, Name: {self.name}, Email: {self.email}"  