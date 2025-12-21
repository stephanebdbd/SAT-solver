from pysat.solvers import Solver
from pysat.card import CardEnc
from pysat.formula import IDPool


def gen_solution(durations: list[int], c: int, T: int) -> None | list[tuple]:
    vpool = IDPool()
    with Solver(name='m22') as s:
        s.add_clause([vpool.id(('boat_at_A', 0))])
        for p in range(len(durations)):
            s.add_clause([vpool.id(('at_A', 0, p))])
            s.add_clause([-vpool.id(('at_A', T, p))])

        for t in range(T):
            for p in range(len(durations)):
                s.add(vpool.id(('dep', t, p, s))) # 1 si il y a un d´epart de la barque a l’instant t qui contient la poule p et de type s
                s.add(vpool.id(('dur', t, d))) # 1 si depart a l'intant t et durrée = max des poules
                s.add(vpool.id(('A', p, t))) # 1 si la poule p est en A
                s.add(vpool.id(('B', p, t))) # 1 si la poule p est en B
                s.add(vpool.id(('ALL', t))) # 1 si les toutes les poules sont en B
                s.add(vpool.id(('BA', t))) # 1 si le bateau est a A
            s.add(vpool.id(('BR', t))) # 1 si le bateau est a B

        s.add_clause([vpool.id(('BA', 1))])
        s.add_clause([vpool.id(('BR', 0))])
        #calculs



def find_duration(durations: list[int], c: int) -> int:
    T = 0
    while True:
        sol = gen_solution(durations, c, T)
        if sol is not None:
            return T
        T += 1
