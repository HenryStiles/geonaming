# Associate a unique 3 word name with every location on the surface.  This is
# just an idea I was experimenting with after hearing about what3words.com.  It
# works by using a large table of words and then generating permuations from
# those words to map coordinates to unique names and back, see below for
# details. Words are sourced from the ispell word list source code distritution which
# is GPL.  Other than that use this as you wish.

from itertools import islice
from itertools import permutations
from math import log10
import time

# set the precision of coordinates in meters
PRECISION = 1.0 * 10**2

# length of one degree of latitude or longitude at the equator in meters.
LENGTH_OF_ONE_DEGREE = 111.32 * 10**3

# calculate the number of decimal places needed to represent the precision given
# the length.
def decimal_places(len, prec):
    return int(round(log10(len / prec), 0))

# round to decimal places
DECIMAL_PLACES = decimal_places(LENGTH_OF_ONE_DEGREE, PRECISION)

# calculate the number or coordinates needed to represent latitude (-90 to 90
# degrees) and longitude (-180 to 180 degrees).
def calculate_number_of_coordinates():
    return (90 * 10**DECIMAL_PLACES * 2) * (180 * 10**DECIMAL_PLACES * 2)


# calculate the number of 3 words needed to represent all possible coordinates.
# So for each word in the list we can represent (n-2)(n-1) coordinates where n
# is the length of the list. We really want the solution to (n-3)(n-2)(n-1) =
# the total number of coordinates, but that's a pain so just round up to the
# cube root.  Here's an example: for the list ['cat', 'dog', 'bird', 'goat'],
# for item 1 we have (4-2)*(4-1) = 6 items: ['cat', 'dog', 'bird'], ['cat',
# 'dog', 'goat'], ['cat', 'bird', 'goat'], ['cat', 'bird', 'dog'], ['cat',
# 'goat', 'bird'], ['cat', 'goat', 'dog']
def calculate_number_of_3_words():
    return int(calculate_number_of_coordinates() ** (1/3))

# read 'n' lines from a file, strip off the newline character, and return a list.
def read_n_lines(n, file_name):
    with open(file_name) as f:
        return [line.rstrip('\n') for line in islice(f, n)]
    
# read as many lines as we calculated above.
word_list = read_n_lines(calculate_number_of_3_words(), 'geonaming_words.txt')

# normalize lattitude and longitude to the range 0 to 180 and 0 to 360, respecively.
def normalize_coordinates(lat, lon):
    return int((lat + 90) * 10**DECIMAL_PLACES), int((lon + 180) * 10**DECIMAL_PLACES)

# convert normalized coordinates back to latitude and longitude.
def denormalize_coordinates(lat, lon):
    return (lat / 10**DECIMAL_PLACES) - 90, (lon / 10**DECIMAL_PLACES) - 180

STRIDE = 360 * 10**DECIMAL_PLACES

# represent longitude and latitude as a single number.
def encode_coordinate_to_one_number(lat, lon):
    return (lat * STRIDE) + lon

# convert a single number back to latitude and longitude.
def decode_coordinates_from_one_number(n):
    lat = n // STRIDE
    lon = n % STRIDE
    return lat, lon

# see long comment above for explanation of this function.
def number_of_perms_per_word(n):
    return (n-2)*(n-1)

# the parameter 'how_many' is always 2 for this application, but I'm leaving it.
# Note we do rely on permuations being generated in the same order each time.
def get_nth_permutation(n, iterable, how_many):
    for i, item in enumerate(permutations(iterable, how_many)):
        if (i==n):
            return item
    raise Exception(f"Error: permutation {n} not found in iterable {iterable}")

# convert to 3 words.  Firse normalize the coordinates, then convert to a single
# number, then convert to 3 words.
def encode_coordinates_to_3_words(lat, lon):
    lat, lon = normalize_coordinates(lat, lon)
    num = encode_coordinate_to_one_number(lat, lon)
    index = num // number_of_perms_per_word(len(word_list))
    offset = num % number_of_perms_per_word(len(word_list))
    # eliminate the word at index from the list
    word_list2 = word_list[:index] + word_list[index+1:]
    return (word_list[index],) + (get_nth_permutation(offset, word_list2, 2))

# this can be slow, search for the permutation in the list of permutations and
# return the index.
def find_permutation_index(iterable, perm):
    for i, item in enumerate(permutations(iterable, len(perm))):
        if (item == perm):
            return i
    raise Exception(f"Error: permutation {perm} not found in iterable {iterable}")

# go back from 3 words to coordinates.  First find the index, find the offset of
# the permutation in the list of permutations, convert to a single number,
# convert to latitude and longitude and finally denormalize.
def decode_coordinates_from_3_words(word1, word2, word3):
    index = word_list.index(word1)
    word_list2 = word_list[:index] + word_list[index+1:]
    offset = find_permutation_index(word_list2, (word2, word3))
    num = index * number_of_perms_per_word(len(word_list)) + offset
    lat, lon = decode_coordinates_from_one_number(num)
    return denormalize_coordinates(lat, lon)

# to test - produce random coordinates, encode them, then decode them.
def test():
    import random
    for i in range(100):
        lat = random.uniform(-90, 90)
        lon = random.uniform(-180, 180)
        print(f"test lat: {lat}, lon: {lon}")
        word1, word2, word3 = encode_coordinates_to_3_words(lat, lon)
        print(f"test word1: {word1}, word2: {word2}, word3: {word3}")
        lat2, lon2 = decode_coordinates_from_3_words(word1, word2, word3)
        print(f"test lat2: {lat2}, lon2: {lon2}")
        # check that the decoded coordinates are the same as the original coordinates to within the precision.
        assert abs(lat - lat2) < 1.0 / 10**DECIMAL_PLACES
        assert abs(lon - lon2) < 1.0 / 10**DECIMAL_PLACES
test()
