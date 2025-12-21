from pysat.solvers import Solver
from pysat.card import CardEnc
from pysat.formula import IDPool


def gen_solution(durations: list[int], c: int, T: int) -> None | list[tuple]:
    vpool = IDPool()
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
