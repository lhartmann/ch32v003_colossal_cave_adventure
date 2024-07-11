#! /usr/bin/env python3
import re

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
            ret.append([])

        ret.append(tokenize_message(entry_text))

        # sanity check
        if len(ret) != entry_id:
            print(f"Probable issue at #{entry[1]}...")
    return ret

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

tokenized_text = [ tokenize_text(text) for text in texts ]
token_count_map    = count_token_instances(tokenized_text)
token_count_sorted = sort_tokens_by_count(token_count_map)
print(f"Longest token is {longest_token(token_count_map)} characters")
print("Diffent tokens by size:", tokens_by_size(token_count_map))
print("Usage count by size:", token_count_by_size(token_count_map))
print("token_total_length(token_count_map):",token_total_length(token_count_map))
print("token_total_count(token_count_map):",token_total_count(token_count_map))

# for i in range(len(token_count_sorted)):
#     token,count = token_count_sorted[i]
#     print(f"{i} / {len(token_count_sorted)-i}: '{token}' {count}")


# At this point there are
#   ~8kB in dictionary data, or ~5kB with 5bit per character.
#   ~10k tokens used for full-text.
# Need work to create VLQ code, and select which symbols use a singel byte.
# There are only 23 1-character tokens, and they are used > 2k times.
# May be useful for compressing the token usage list: https://excamera.com/sphinx/article-compression.html
