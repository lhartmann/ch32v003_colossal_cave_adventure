#! /usr/bin/env python3
import re
import itertools
import numpy as np
import codetree
import collections

# Load text files, making all uppercase.
textfiles = [
    "adventure/src/advent1.txt",
    "adventure/src/advent2.txt",
    "adventure/src/advent3.txt",
    "adventure/src/advent4.txt"
]

texts = []
for file in textfiles:
    with open(file,"r") as f:
        texts.append(f.read().upper())

# Character mappings:
#   ZX81 has no lowercase
#   Symbol 0 is space.
#   Symbols 1-10 are graphics, but repurposed.
#   Symbol 11 was the pound symbol, repurposed to #.
#   There are no symbols for _!{}'\n# so they are remapped.
character_map = " abcd_!{}'\n\"#$:?()><=+-*/;,.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
def text_to_zx81(text):
    ret = []
    for ch in text:
        try:
            ret.append(character_map.index(ch))
        except ValueError:
            print(f"Missing symbol '{ch}'")
            ret.append(0)
    return ret

def zx81_to_text(zxt):
    ret = ""
    for i in zxt:
        ret = ret + character_map[i]
    return ret

def test_character_mapper():
    for t in texts:
        zxt = text_to_zx81(t)
        txt = zx81_to_text(zxt)
        print("Validate:", txt == t)

# Remove text information we don't care about
def simplify_text(text):
    text = " " + text + " "
    text = re.sub("\n", " ", text)
    text = re.sub(" +", " ", text)
    return text

def tokenize_message(text):
    ret = []
    for entry in re.finditer("([A-Z]*)([\"'.,/?!-+/ ])", text):
        if entry[1]:
            ret.append(entry[1])
        if entry[2] != " ":
            ret.append(entry[2])
    return ret

def tokenize_text(text, message_tokenizer=tokenize_message):
    ret = []
    for entry in re.finditer("#([0-9]+)\n([^#]*)\n", text):
        entry_id = int(entry[1])
        entry_text = simplify_text(entry[2])
        entry_text_tokenized = message_tokenizer(entry_text)

#        print(f"#{entry_id} ==> {entry_text_tokenized}")

        # Advent2.txt has a few missing indices
        while len(ret) < entry_id - 1:
            ret.append(message_tokenizer(""))

        ret.append(message_tokenizer(entry_text))

        # sanity check
        if len(ret) != entry_id:
            print(f"Probable issue at #{entry[1]}...")
    return ret

# TEST: Create a file with simplified text.
# Each line is a message, all uppercase.
# No file separators, no message ID numbers.
#   44220 bytes raw data
#   13862 bytes with gzip -9
def test_simplified_text_file():
    message_tokenizer = lambda msg: re.sub("^ +| +$","",msg)
    simplified_texts = [ tokenize_text(text, message_tokenizer) for text in texts ]
    res = ""
    for text in simplified_texts:
        for message in text:
            res += message + "\n"
    with open("simplified_text.txt", "w") as f:
        f.write(res)

# TEST: Check what kinds of separators are there
def test_separators():
    separators = []
    def tokenize_separators(text):
        for entry in re.finditer("[A-Z]([^A-Z]+)[A-Z]", "A"+text+"A"):
            separators.append(entry[1])
    tokenize_text(texts[0], tokenize_separators)
    tokenize_text(texts[1], tokenize_separators)
    tokenize_text(texts[2], tokenize_separators)
    tokenize_text(texts[3], tokenize_separators)
    print(set(separators))

def count_token_instances(tokenized_texts):
    ret = {}
    for tokenized_text in tokenized_texts:
        for entry in tokenized_text:
            for token in entry:
                try:
                    ret[token] += 1
                except KeyError:
                    ret[token] = 1
    return ret

def sort_tokens_by_count(token_count_map):
    token_count_sorted = [ (token,count) for token,count in token_count_map.items()]
    token_count_sorted.sort(key=lambda e: e[1])
    return token_count_sorted

def longest_token(token_count_map):
    return max([ len(key) for key in token_count_map.keys() ])

def tokens_by_size(token_count_map):
    ret = [0] * (1+longest_token(token_count_map))
    for token,count in token_count_map.items():
        ret[len(token)] += 1
    return ret

def token_count_by_size(token_count_map):
    ret = [0] * (1+longest_token(token_count_map))
    for token,count in token_count_map.items():
        ret[len(token)] += count
    return ret

def token_total_length(token_count_map):
    return sum([len(token) for token,count in token_count_map.items()])

def token_total_count(token_count_map):
    return sum([count for token,count in token_count_map.items()])

def token_character_counts(token_count_map):
    alltokens = " ".join([token for token in token_count_map.keys()])
    return { char:alltokens.count(char) for char in character_map }

def token_character_counts_sorted(token_count_map, include_unused=True):
    alltokens = " ".join([token for token in token_count_map.keys()])
    counts = [ (char,alltokens.count(char)) for char in character_map ]
    counts.sort(key=lambda e: -e[1])
    if not include_unused:
        counts = [(char,count) for (char,count) in counts if count > 0]
    return counts

tokenized_text = [ tokenize_text(text) for text in texts ]
#token_count_map    = count_token_instances(tokenized_text)
token_count_map    = collections.Counter([word
                                          for text in tokenized_text
                                          for message in text
                                          for word in message])
token_count_sorted = sort_tokens_by_count(token_count_map)
print(f"Longest token is {longest_token(token_count_map)} characters")
print("Diffent tokens by size:", tokens_by_size(token_count_map))
print("Usage count by size:", token_count_by_size(token_count_map))
print("Unique tokens:",len(token_count_map.keys()))
print("Sum of unique token lenghts:",token_total_length(token_count_map))
print("Total tokens in text:",token_total_count(token_count_map))

token_frequency_map = collections.Counter(token_count_map.values())
token_frequency_distribution = [token_frequency_map[i]
                                for i in range(max(token_frequency_map.keys())+1)]

def VLQ4_encode(n):
    r = ""
    while n > 14:
        r += "F"
        n -= 15
    r += "0123456789ABCDE"[n]
    return r

def test_compress_dictionary():
    print("Dictionary compression text:")
    tcc  = token_character_counts(token_count_map)
    tccs = token_character_counts_sorted(token_count_map, False)

    # Length of each code symbol in bytes
    codelen = 4/8
    code = [ VLQ4_encode(i) for i in range(len(tcc)) ]

    if False: # Variable bit length. Better, but painful to decompress
        codelen = 1/8
        code = [
            "000",
            "001",
            "0100",
            "0101",
            "0110",
            "0111",
            "1000",
            "1001",
            "1010",
            "1011",
            "11000",
            "11001",
            "11010",
            "11011",
            "11100",
            "111010",
            "111011",
            "1111000",
            "1111001",
            "1111010",
            "1111011",
            "1111100",
            "11111010",
            "11111011",
            "11111100",
            "11111101",
            "11111110000",
            "11111110001",
            "11111110010",
            "11111110011",
            "11111110100",
            "11111110101",
            "11111110110",
            "11111110111",
            "11111111000",
            "11111111001",
            "11111111010",
            "11111111011",
            "11111111100",
            "11111111101",
            "11111111110",
            "11111111111",
        ]

    print(code)
    code.reverse()
    mapper = { char:code.pop() for char,count in tccs }

    uncompressed_bytes = sum([count for char,count in tccs])
    compressed_bytes = codelen * sum([count*len(mapper[char]) for char,count in tccs])

    print(f"char = code        => count x length = space")
    for char in mapper.keys():
        N = tcc[char]
        L = len(mapper[char])*codelen
        print(f"{char:>4} = {mapper[char]:<11} => {N:>5} x {L:<6} = {N*L}")


    print("Total bytes, uncompressed..:", uncompressed_bytes)
    print("Total bytes, compressed....:", compressed_bytes)

# Token dictionary is a list of words.
# Word is a list of characters with added null-terminator.
# RAW size is 10046B.
# Compresses to 5710B using VLQ4 and sorting by frequency.
# test_compress_dictionary()

def codegen(txt, brk, depth, prefix = ""):
    if depth == 0:
        return []
    r = []
    for digit in txt[0:brk]:
        r.append(prefix+digit)
    for digit in txt[brk:]:
        r = r + codegen(txt, brk, depth-1, prefix+digit)
    return r

def codegen_64(a,b):
    r = []
    for i in range(64-a):
        r.append(f"{i:06b}")
    for i in range(64-a, 64-b):
        for j in range(4):
            r.append(f"{i:06b}{j:02b}")
    for i in range(64-b, 64):
        for j in range(2**10):
            r.append(f"{i:06b}{j:010b}")
    return r

def export_tokenized_text():
    mapper = {}
    for i in range(len(token_count_sorted)):
        word = token_count_sorted[i][0]
        mapper[word] = i+2

    tokens = []
    for text in tokenized_text:
        for message in text:
            for word in message:
                tokens.append(mapper[word])
            tokens.append(0)
        tokens.append(1)
    np.save("tokenized_text.npy", tokens)
export_tokenized_text();

# Text includes
#   ~10k tokens used for full-text.
# May be useful for compressing the token usage list: https://excamera.com/sphinx/article-compression.html
def test_compress_text():
    # Generate the simplified text file. Usefull for grep-ing stuff.
    test_simplified_text_file()

    if True: # VLQ8 code
        code = []
        code_break = 251
        codelen = 4/8
        for i in range(code_break):
            code.append(f"{i:02x}")
        for i in range(code_break,256):
            for j in range(code_break):
                code.append(f"{i:02x}{j:02x}")
        code.reverse()

    if False: # Base64 VLQ1
        codelen=6/8
        code = codegen("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",59,3)
        code.sort(key=lambda c: len(c))
        code.reverse()

    if True: # Base64 VLQ2
        codelen=1/8
        code = codegen_64(30,2)
        code.sort(key=lambda c: len(c))
        code.reverse()

    token_count_sorted.reverse()
    mapper = { word:code.pop() for word,count in token_count_sorted }
    token_count_sorted.reverse()

    uncompressed_bytes = sum([2*count for word,count in token_count_sorted])
    compressed_bytes = codelen * sum([count*len(mapper[word]) for word,count in token_count_sorted])

    print(f"char = code        => count x length = space")
    for index,(word,count) in enumerate(token_count_sorted):
        N = count
        L = len(mapper[word]) * codelen
        print(f"{index:>4}:{len(token_count_sorted)-index-1:<4} {word:>15} = {mapper[word]:<11} => {N:>5} x {L:<6} = {N*L}")
    print(f"char = code        => count x length = space")
    print("Total words.................:", sum(token_count_map.values()))
    print("Unique words................:", len(token_count_map))
    print("Word frequncy distribution..:", token_frequency_distribution);
    print("Total bytes, uncompressed...:", uncompressed_bytes)
    print("Total bytes, compressed.....:", compressed_bytes)

test_compress_text()
