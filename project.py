from pysat.solvers import Minisat22
from pysat.formula import CNFPlus, IDPool


def gen_solution(durations: list[int], c: int, T: int) -> None | list[tuple]:
    vpool = IDPool()
    cnf = CNFPlus()
    
    cnf.append([vpool.id(('side', 0))])
    for p in range(len(durations)):
        cnf.append([vpool.id(('at_A', 0, p))])
        cnf.append([-vpool.id(('at_A', T, p))])

    for t in range(T):
        for p in range(len(durations)):
            cnf.append([vpool.id(('dep', t, p, s))]) # 1 si il y a un d´epart de la barque a l’instant t qui contient la poule p et de type s
            cnf.append([vpool.id(('dur', t, d))]) # 1 si depart a l'intant t et durrée = max des poules
            cnf.append([vpool.id(('A', p, t))]) # 1 si la poule p est en A
            cnf.append([vpool.id(('B', p, t))]) # 1 si la poule p est en B
            cnf.append([vpool.id(('ALL', t))]) # 1 si les toutes les poules sont en B
            cnf.append([vpool.id(('BA', t))]) # 1 si le bateau est a A
            cnf.append([vpool.id(('BR', t))]) # 1 si le bateau est a B

        cnf.append([vpool.id(('BA', 1))])
        cnf.append([vpool.id(('BR', 0))])
    s = Minisat22()
    s.append_formula(cnf)


def find_duration(durations: list[int], c: int) -> int:
    T = 1
    while True:
        sol = gen_solution(durations, c, T)
        if sol is not None:
            return T
        T += 1
