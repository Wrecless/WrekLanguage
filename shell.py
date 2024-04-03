import wrek

while True:
    text = input('Wrek > ')
    result, error = wrek.run('<stdin>', text)

    if error: print(error.as_string())
    else: print(result)