
def read_varlen_quantity(string):
    pass


def scale_num(num, from_bits, to_bits):
    assert num <= (2**from_bits-1)
    assert isinstance(num, int)
    
    scale_factor = num / (2.0**from_bits-1)
    fixed_number = scale_factor * (2.0**to_bits-1)
    
    return int(fixed_number)


if __name__ == "__main__":
    print scale_num(2819, 14, 16)
