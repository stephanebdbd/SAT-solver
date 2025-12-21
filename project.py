from pysat.solvers import Solver
from pysat.card import CardEnc
from pysat.formula import IDPool


def gen_solution(durations: list[int], c: int, T: int) -> None | list[tuple]:
    vpool = IDPool()
    possible_durations = list(set(durations))

    with Solver(name='g3') as s:
        #variables
        for t in range(T):
            for p in range(len(durations)):
                for s in range(c):
                    s.add(vpool.id(('dep', t, p, s))) # 1 si il y a un d´epart de la barque a l’instant t qui contient la poule p et de type s
                    s.add(vpool.id(('dur', t, d))) # 1 si depart a l'intant t et durrée = max des poules
                    s.add(vpool.id(('A', p, t))) # 1 si la poule p est en A
                    s.add(vpool.id(('B', p, t))) # 1 si la poule p est en B
                    s.add(vpool.id(('ALL', t))) # 1 si les toutes les poules sont en B
                    s.add(vpool.id(('BA', t))) # 1 si le bateau est a A
                    s.add(vpool.id(('BR', t))) # 1 si le bateau est a B
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
