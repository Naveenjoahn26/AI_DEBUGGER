class UserGroup:
    def __init__(self, name, users=[]):
        self.name = name
        self.users = users
        
    def add_user(self, user):
        self.users.append(user)

if __name__ == "__main__":
    group1 = UserGroup("Admins")
    group1.add_user("Alice")
    
    group2 = UserGroup("Guests")
    group2.add_user("Bob")
    
    print(f"Admins: {group1.users}")
    print(f"Guests: {group2.users}")
