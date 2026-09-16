import random

def generate_random_id():
    length = 6
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    seed = random.choice(characters)
    
    return ''.join(seed for _ in range(length))