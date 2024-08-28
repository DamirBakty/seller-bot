def is_float(message):
    try:
        float(message.text)
        return True
    except ValueError:
        return False
