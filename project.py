from pysat.solvers import Solver
from pysat.card import CardEnc
from pysat.formula import IDPool


def gen_solution(durations: list[int], c: int, T: int) -> None | list[tuple]:
    # vpool.id(('move', t, p, s)):
    # vpool.id(('trip_start', t, s)):
    # vpool.id(('trip_duration', t, d)):
    # vpool.id(('at_A', t, p)):
    # vpool.id(('boat_at_A', t)):
    
    vpool = IDPool()
    possible_durations = list(set(durations))

    with Solver(name='g3') as s:
        #vaiarbles
        
        #contraintes
        #calculs
        if s.solve():
            model = s.get_model()
            solution = []
            for p in range(len(durations)):
                for t in range(T):
                    for s in range(c):
                        if vpool.id(('dep', t, p, s)) in model:
                            solution.append((p, t, s))
            return solution
        else:
            return None


def find_duration(durations: list[int], c: int) -> int:
    pass
