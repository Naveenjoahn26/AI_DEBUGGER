def remove_even_numbers(numbers):
    for num in numbers:
        if num % 2 == 0:
            numbers.remove(num)
    return numbers

if __name__ == "__main__":
    nums = [1, 2, 2, 3, 4, 4, 5]
    print(f"Before: {nums}")
    print(f"After:  {remove_even_numbers(nums)}")
