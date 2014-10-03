



def readVariableLength_Quantity(string):
    pass


def scaleDown_number(number, fromBits, toBits):
    assert number <= (2**fromBits-1)
    assert isinstance(number, int)
    
    scale_factor = number / (2.0**fromBits-1)
    fixed_number = scale_factor * (2.0**toBits-1)
    
    return int(fixed_number)



print scaleDown_number(2819, 16, 14)
