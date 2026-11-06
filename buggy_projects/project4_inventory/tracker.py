total_items = 0

def add_items(count):
    if count > 0:
        total_items += count
        
if __name__ == "__main__":
    add_items(5)
    print(f"Total items: {total_items}")
