# random useful functions that make things easier

# nullpack unpacks a tuple from the database if it is not null
# otherwise, just return null
def null_pack(value:tuple):
    if value is None:
        return None
    else:
        return value[0]

# gets a range string (e.g. 2-3,5,6,8-11)
def get_num_range(range_str:str):
    range_str = range_str.replace(" ", "")
    segments = range_str.split(",")
    if segments is None:
        raise ValueError("Invalid ranges string")
    nums = []
    for segment in segments:
        if segment.isdigit():
            # the segment is a single number
            nums.append(int(segment))
        else:
            try:
                # the segment is an inclusive range (e.g. 1-5 would be 1,2,3,4,5)
                indices = segment.split("-")
                start = int(indices[0])
                end = int(indices[1])
                if start > end:
                    temp = end
                    end = start
                    start = temp
                for i in range(start, end+1):
                    nums.append(i)
            except ValueError:
                raise ValueError("Invalid ranges string")
    return remove_dupes(nums)

# removes duplicates from a list
def remove_dupes(num_list:list):
    new_list = []
    for num in num_list:
        if num not in new_list:
            new_list.append(num)
    return new_list