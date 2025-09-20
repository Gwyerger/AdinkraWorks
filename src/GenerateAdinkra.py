import numpy as np
from itertools import combinations
# Translated originally form Julia Code, we generate adinkras via cubical cohomology

def generate_code(generator):
    d = len(generator)
    N = len(generator[0])
    
    # collect all combinations of length 1..d
    combs = []
    for dd in range(1, d+1):
        combs.extend(combinations(generator, dd))
    
    code = []
    for str_tuple in combs:
        # XOR all vectors in the tuple
        acc = str_tuple[0].copy()
        for vec in str_tuple[1:]:
            acc = np.bitwise_xor(acc, vec)
        code.append(acc)
    
    # prepend the zero vector
    code.insert(0, np.zeros(N, dtype=np.uint8))
    return code


def decode_ncube_unsigned(generator, allow_large_computations=False):
    d = len(generator)
    N = len(generator[0])
    
    if N >= 16 and not allow_large_computations:
        return "Are You Sure?"
    
    code = generate_code(generator)
    
    # NCubeIndexMap = [1, 2, ..., 2^N]
    NCubeIndexMap = list(range(1, 2**N + 1))
    
    # NCubeLattice = all binary vectors of length N
    NCubeLattice = [np.array(list(map(int, np.binary_repr(nn, width=N))), dtype=np.uint8)
                    for nn in range(2**N)]
    
    # Basis = standard basis vectors
    Basis = [np.array(list(map(int, np.binary_repr(1 << nn, width=N))), dtype=np.uint8)
             for nn in range(N)]
    
    Partitioned = []
    for _ in range(2**(N-d)):
        # apply XOR with each codeword
        new_partition = [np.bitwise_xor(NCubeLattice[0], c) for c in code]
        Partitioned.append(new_partition)
        
        for point in new_partition:
            idx = int(np.dot(point, 2**np.arange(N-1, -1, -1))) + 1
            # delete corresponding lattice point
            del NCubeLattice[NCubeIndexMap[idx-1]-1]
            NCubeIndexMap[idx-1] = 0
            for i in range(idx, len(NCubeIndexMap)):
                NCubeIndexMap[i] -= 1
    
    # Adjacency structure
    Adjacency = [[[np.zeros(2**(N-d), dtype=np.uint8) for _ in range(2**(N-d))]
                  for _ in range(N)]
                 ]
    
    Adjacency = [[ [np.zeros(2**(N-d), dtype=np.uint8) 
                    for _ in range(2**(N-d))] for _ in range(N)]
    
    for hi, basis_vec in enumerate(Basis):
        for hj in range(2**(N-d)):
            newstr = np.bitwise_xor(Partitioned[hj][0], basis_vec)
            for hk in range(2**(N-d)):
                if any(np.array_equal(newstr, p) for p in Partitioned[hk]):
                    Adjacency[hi][hj][hk] = 1
                    break
    
    # Build adjacency matrices
    AdjacencyC = [np.vstack([np.transpose(np.array(layer, dtype=np.uint8)) 
                             for layer in Adjacency[i]])
                  for i in range(N)]
    
    # Sum all adjacency matrices elementwise
    AdjacencyM = np.zeros_like(AdjacencyC[0])
    for A in AdjacencyC:
        AdjacencyM += A
    
    return AdjacencyC, AdjacencyM

