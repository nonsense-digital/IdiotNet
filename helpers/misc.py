# random useful functions that make things easier

# nullpack unpakcs a tuple from the datbase if it is not null
# otherwise, just return null
def nullPack(value:tuple):
    if value is None:
        return None
    else:
        return value[0]