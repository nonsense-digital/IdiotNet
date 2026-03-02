# random useful functions that make things easier

# nullpack unpacks a tuple from the database if it is not null
# otherwise, just return null
def nullPack(value:tuple):
    if value is None:
        return None
    else:
        return value[0]