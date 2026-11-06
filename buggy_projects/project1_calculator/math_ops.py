def average(numbers):
    total = sum(numbers)
    return total / len(numbers)

if __name__ == "__main__":
    print(average([1, 2, 3, 4]))
    print(average([]))
