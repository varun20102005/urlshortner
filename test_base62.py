from app.utils import encode_base62

numbers = [0, 1, 10, 61, 62, 125, 1000, 123456]

for num in numbers:
    print(num, "->", encode_base62(num))