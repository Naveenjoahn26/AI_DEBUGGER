import json

def parse_data(json_string):
    try:
        data = json.loads(json_string)
        return data['user']['id']
    except Exception as e:
        print(f"Error parsing data")

if __name__ == "__main__":
    print(parse_data('{"user": {"name": "Alice"}}'))
    print(parse_data('invalid json'))
