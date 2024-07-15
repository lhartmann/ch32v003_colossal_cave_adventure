#! /usr/bin/env python3
import sys
import numpy as np

class CompressionOportunity:
    def __init__(self, _start, _source, _length):
        self.start  = _start
        self.source = _source
        self.length = _length
    def end(self):
        return self.start + self.length
    def overlaps(self, other):
        return ( self.start >= other.start and  self.start < other.end()) \
            or (other.start >= self.start  and othen.start <  self.end())
    def covers(self, other):
        return self.start <= othen.start and self.end() >= other.end()

def test_oportunity(want, have, O,M,N):
    if want[0:M] != have[0:M]:
        return 0

    for m in range(N-1, M-1, -1):
        if want[0:m] == have[0:m]:
            return m
    return 0

def get_all_oportunities(raw, O,M,N):
    # Tuples: (
    #   i = raw destination position,
    #   j = raw source position,
    #   m = raw length
    # )
    oportunities = []
    for i in range(len(raw)):
        want = raw[i:i+N]
        for j in range(max(0,i-O), i):
            have = raw[j:min(i, j+N)]
            m = test_oportunity(want, have, O,M,N)
            if m >= M:
                oportunities.append(CompressionOportunity(i,j,m))

    # Results are intrinsically sorted by i then j, and will probably overlap.
    # It is better to sort by i then -m.
    oportunities.sort(key=lambda o: (o.start, -o.length))

    return oportunities

def remove_oportunities_that_end_on_the_same_byte(oportunities):
    p = 0 # previous index
    while p < len(oportunities)-1:
        n = p+1 # next index
        po = oportunities[p]
        no = oportunities[n]
        # Long strings will produce multiple matches, but smaller every time.
        # Remove all squential matches that end on the same raw byte.
        if no.end() == po.end():
            oportunities.pop(n)
        else:
            p += 1
    return oportunities

def is_contained(external, internal):
    return internal.start >= external.start and internal.end() <= external.end()

def are_overlapping(oportunity1, oportunity2):
    a = oportunity1
    b = oportunity2
    return (b.start >= a.start and b.start < b.end()) or (a.start >= b.start and a.start < b.end())

def remove_small_nested_oportunities(oportunities):
    p = 0 # previous index
    n = 1 # next index
    while p < len(oportunities)-1:
        while n < len(oportunities):
            if not are_overlapping(oportunities[p], oportunities[n]):
                break

            if is_contained(oportunities[p], oportunities[n]):
                oportunities.pop(n)
            else:
                n += 1
        p += 1
        n = p+1
    return oportunities

def count_conflicting_oportunities(oportunities):
    count = 0
    p = 0 # previous index
    n = 1 # next index
    while p < len(oportunities)-1:
        while n < len(oportunities):
            if not are_overlapping(oportunities[p], oportunities[n]):
                break
            count += 1
            n += 1
        p += 1
        n = p+1
    return count

def clusterize_oportunity_conflicts(oportunities):
    clusters = []
    cluster = []
    for o in oportunities:
        if any(are_overlapping(o,other) for other in cluster):
            cluster.append(o)
        else:
            if len(cluster):
                clusters.append(cluster)
            cluster = [o]
    if len(cluster):
        clusters.append(cluster)

    return clusters

def declusterize_oportunity_conflicts(clusters):
    return [ oportunity for cluster in clusters for oportunity in cluster ]

def reclusterize_oportunity_conflicts(clusters):
    return clusterize_oportunity_conflicts(declusterize_oportunity_conflicts(clusters))

def largest_cluster_size(clusters):
    return max(len(cluster) for cluster in clusters)

def oportunity_size_distribution(oportunities):
    sizes = [0] * (1+max(o.length for o in oportunities))
    for o in oportunities:
        sizes[o.length] += 1
    return sizes

def cluster_size_distribution(clusters):
    sizes = [0] * (largest_cluster_size(clusters)+1)
    for cluster in clusters:
        sizes[len(cluster)] += 1
    return sizes

def naive_conflict_resolver(oportunities):
    p = 0
    n = 1
    while n < len(oportunities):
        po = oportunities[p]
        no = oportunities[n]

        if is_contained(po, no):
            oportunities.pop(n)
            continue

        if is_contained(no, po):
            oportunities.pop(p)
            continue

        if not are_overlapping(oportunities[n], oportunities[p]):
            p += 1
            n = p+1
            continue

        overlap = po.end() - no.start
        if overlap > 0:
            no.start  += overlap
            no.source += overlap
            no.length -= overlap
            oportunities[n] = no
        n = n+1
        if n == len(oportunities):
            p = p+1
            n = p+1

    return oportunities

def uncompressed_symbol_frequency(raw, oportunities):
    counts = {}
    o = 0
    r = 0
    while r < len(raw):
        if o < len(oportunities) and r == oportunities[o].start:
            r += oportunities[o].length
            o += 1
        else:
            try:
                counts[raw[r]] += 1
            except KeyError:
                counts[raw[r]] = 1
            r += 1
    return counts

if __name__ == "__main__":
    raw = list(np.load("tokenized_text.npy"))
    #raw = open("simplified_text.txt","r").read();

    O = 2**8 - 1    # lookback distance
    M = 3           # minimum viable compression size
    N = 2**8 -1 + M # maximum compression size

    print(list(range(N-1, M-1, -1)))
    print(f"O {O}, M {M}, N {N}")
    oportunities = get_all_oportunities(raw, O,M,N)
    conflicts = count_conflicting_oportunities(oportunities)
    bytes_saveable = sum(o[2] for o in oportunities)
    largest_oportunity = max(m for i,j,m in oportunities)
    size_distribution = oportunity_size_distribution(oportunities)

    print("Total oportunities:")
    print(f"  Count......: {len(oportunities)}")
    print(f"  Largest....: {largest_oportunity}")
    print(f"  Sizes......: {size_distribution}")
    print(f"  Conflicts..: {conflicts}")
    print(f"  Bytes......: {bytes_saveable}")

    oportunities = remove_oportunities_that_end_on_the_same_byte(oportunities)
    oportunities = remove_small_nested_oportunities(oportunities)
    conflicts = count_conflicting_oportunities(oportunities)
    bytes_saveable = sum(o[2] for o in oportunities)
    largest_oportunity = max(m for i,j,m in oportunities)
    size_distribution = oportunity_size_distribution(oportunities)

    print("Selected oportunities:")
    print(f"  Count......: {len(oportunities)}")
    print(f"  Largest....: {largest_oportunity}")
    print(f"  Sizes......: {size_distribution}")
    print(f"  Conflicts..: {conflicts}")
    print(f"  Bytes......: {bytes_saveable}")

    clusters = clusterize_oportunity_conflicts(oportunities)
    largest_cluster = max(len(cluster) for cluster in clusters)

    print("Clustered oportunities:")
    print(f"  Count......: {len(clusters)}")
    print(f"  Largest....: {largest_cluster}")
    print(f"  Sizes......: {cluster_size_distribution(clusters)}")

    for cluster in clusters:
        if len(cluster) < 9: continue
        print(f"Cluster: {len(cluster)} conflicts.")
        for oportunity in cluster:
            i,j,m = oportunity
            data = raw[j:j+m]#.replace("\n","\\n")
            print(f"  Oportunity: {i:6}, {j:6}, {m:3}, \"{data}\"")
