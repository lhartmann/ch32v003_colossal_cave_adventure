#! /usr/bin/env python3

# Codetree spec
# take bits
# use combinations
# take bits ...

# take 0 means final code
# use 0 means use as compression tokens.

def parse_leaf(
    spec, off, prefix,
    push_literal_code=lambda code:None,
    push_compression_range=lambda prefix,length,start:None
):
    take = spec[off]
    # print(f"take {take}")
    off += 1
    if not take:
        push_literal_code(prefix)
        return off

    avail = 2**take
    used  = 0
    while used < avail:
        use = spec[off]
        # print(f"use +{use} of {avail}, {used+use} so far")
        off += 1
        if used+use > avail:
            print(f"{prefix:<16} = Error, using more than available codes.")
            return off
        if not use:
            for u in range(used, avail):
                suffix = "0" * take + f"{u:b}"
                suffix = suffix[-take:]
                #print(f"{prefix+suffix:<16} = Compression codes.")
            push_compression_range(prefix, take, used)
            return off
        for u in range(use):
            suffix = "0" * take + f"{used+u:b}"
            suffix = suffix[-take:]
            off2 = parse_leaf(spec, off, prefix+suffix, push_literal_code, push_compression_range)
        off = off2
        used += use
    return off

if __name__ == "__main__":
    print_code = lambda code: print(f"{code:<16} = Literals")
    def print_comp(prefix, length, start):
        p=prefix+"x"*length
        print(f"{p:<16} = Compression, starting at {start}")

    spec = [
        3, # takes 3 bit
            6, # use 6 values
                0, # take no more: literals
            1, # use 1 values
                4, # take 4 bits, uase as compresion
                0, # use none for literal. Compression codes.
            1, # use last value
                4, # take 4 more bits
                    16, # use all values
                        0 # take no more: literals
                    # all values were used
            # all values were used
    ]
    parse_leaf(spec, 0, "", print_code, print_comp)

    spec_mini_1 = [
        0, # takes none: all literals
    ]
    parse_leaf(spec_mini_1, 0, "LIT_ONLY", print_code, print_comp)

    spec_mini_2 = [
        1, # takes 1 bit
        0 # use none for literals. Compression codes
    ]
    parse_leaf(spec_mini_2, 0, "COMP_ONLY", print_code, print_comp)




