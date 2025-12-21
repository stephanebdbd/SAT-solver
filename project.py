from pysat.solvers import Minisat22
from pysat.formula import CNFPlus, IDPool
from pysat.card import CardEnc

def gen_solution(durations: list[int], c: int, T: int) -> None | list[tuple]:
    vpool = IDPool()
    cnf = CNFPlus()
    N = len(durations)
    possible_durations = list(set(durations))
    STATES = ['A', 'B', 'BA', 'BR']

    # --- 1. INITIALISATION (t=0) ---
    for p in range(N):
        cnf.append([vpool.id(('x', p, 'A', 0))])
    cnf.append([vpool.id('boat_A_0')])
    cnf.append([-vpool.id('boat_B_0')])

    # --- 2. CONTRAINTES GLOBALES ---
    for t in range(T + 1): 
        # Unicité de l'état
        for p in range(N):
            lits_states = [vpool.id(('x', p, s, t)) for s in STATES]
            cnf.extend(CardEnc.equals(lits=lits_states, bound=1, vpool=vpool))

        if t < T: 
            # Capacité
            lits_BA = [vpool.id(('x', p, 'BA', t)) for p in range(N)]
            cnf.extend(CardEnc.atmost(lits=lits_BA, bound=c, vpool=vpool))
            lits_BR = [vpool.id(('x', p, 'BR', t)) for p in range(N)]
            cnf.extend(CardEnc.atmost(lits=lits_BR, bound=c, vpool=vpool))

    # --- 3. OBJECTIF FINAL ---
    for p in range(N):
        cnf.append([vpool.id(('x', p, 'B', T))])

    # --- 4. DYNAMIQUE ---
    for t in range(T):
        lits_depart = [vpool.id(('depart', t, d, sens)) for d in possible_durations for sens in ["Aller", "Retour"]]
        cnf.extend(CardEnc.atmost(lits=lits_depart, bound=1, vpool=vpool))
        
        departs_Aller = [vpool.id(('depart', t, d, 'Aller')) for d in possible_durations if t+d <= T]
        departs_Retour = [vpool.id(('depart', t, d, 'Retour')) for d in possible_durations if t+d <= T]

        # --- SAFETY LOCKS & INERTIE POULES ---
        for p in range(N):
            # Pré-déclaration explicite comme demandé
            var_x_A      = vpool.id(('x', p, 'A', t))
            var_x_B      = vpool.id(('x', p, 'B', t))
            var_x_BA     = vpool.id(('x', p, 'BA', t))
            var_x_BR     = vpool.id(('x', p, 'BR', t))

            var_x_A_next   = vpool.id(('x', p, 'A', t+1))
            var_x_B_next   = vpool.id(('x', p, 'B', t+1))
            var_x_BA_next  = vpool.id(('x', p, 'BA', t+1))
            var_x_BR_next  = vpool.id(('x', p, 'BR', t+1))

            p_embarque     = vpool.id(f'embarque_{p}_{t}')
            p_embarque_R   = vpool.id(f'embarque_R_{p}_{t}')

            # Inertie
            cnf.append([-var_x_A, var_x_A_next, var_x_BA_next, var_x_B_next])
            cnf.append([-var_x_B, var_x_B_next, var_x_BR_next, var_x_A_next])
            
            # Transitions & Safety Locks (Aller)
            cnf.append([-var_x_A, -var_x_BA_next, p_embarque])
            # Direct A->B (pour d=1) aussi protégé par embarque
            cnf.append([-var_x_A, -var_x_B_next, p_embarque])
            # Embarque implique présence en A
            cnf.append([-p_embarque, var_x_A])
            
            # Transitions & Safety Locks (Retour)
            cnf.append([-var_x_B, -var_x_BR_next, p_embarque_R])
            cnf.append([-var_x_B, -var_x_A_next, p_embarque_R])
            cnf.append([-p_embarque_R, var_x_B])

            # Embarque implique Départ existant
            if departs_Aller: cnf.append([-p_embarque] + departs_Aller)
            else: cnf.append([-p_embarque])
            
            if departs_Retour: cnf.append([-p_embarque_R] + departs_Retour)
            else: cnf.append([-p_embarque_R])
            
            # Inertie Barque/Transits
            cnf.append([-var_x_BA, var_x_BA_next, var_x_B_next])
            cnf.append([-var_x_BR, var_x_BR_next, var_x_A_next])


        # --- INERTIE BATEAU ---
        b_now = vpool.id(f'boat_A_{t}')
        b_next = vpool.id(f'boat_A_{t+1}')
        arrivals_Retour = []
        for d in possible_durations:
             st = t + 1 - d
             if st >= 0: arrivals_Retour.append(vpool.id(('depart', st, d, 'Retour')))
        
        if departs_Aller:
             for start in departs_Aller: cnf.append([-start, -b_next])
        if arrivals_Retour:
             for arr in arrivals_Retour: cnf.append([-arr, b_next])
        
        cnf.append([-b_now, b_next] + departs_Aller)
        cnf.append([b_now, -b_next] + arrivals_Retour)


        # --- BOUCLE D (Moteur) ---
        for d in possible_durations:
            if t + d > T:
                cnf.append([-vpool.id(('depart', t, d, 'Aller'))])
                cnf.append([-vpool.id(('depart', t, d, 'Retour'))])
                continue

            # ALLER
            var_dep_A = vpool.id(('depart', t, d, 'Aller'))
            
            cnf.append([-var_dep_A, b_now]) 
            cnf.append([-var_dep_A, -b_next]) 
            cnf.append([-var_dep_A, vpool.id(f'boat_B_{t+d}')]) 
            
            passengers = []
            for p in range(N):
                p_emb = vpool.id(f'embarque_{p}_{t}')
                passengers.append(p_emb)
                
                if durations[p] > d: cnf.append([-var_dep_A, -p_emb])
                
                if d > 1:
                     # Utilisation tuple ID propre
                     cnf.append([-var_dep_A, -p_emb, vpool.id(('x', p, 'BA', t+1))])
                     for k in range(1, d):
                          cnf.append([-var_dep_A, -p_emb, vpool.id(('x', p, 'BA', t+k))])
                
                cnf.append([-var_dep_A, -p_emb, vpool.id(('x', p, 'B', t+d))])
            
            cnf.append([-var_dep_A] + passengers)
            cnf.extend(CardEnc.atmost(lits=passengers, bound=c, vpool=vpool))

            for k in range(1, d):
                if t + k < T:
                    for d2 in possible_durations:
                        cnf.append([-var_dep_A, -vpool.id(('depart', t+k, d2, 'Aller'))])
                        cnf.append([-var_dep_A, -vpool.id(('depart', t+k, d2, 'Retour'))])

            # RETOUR
            var_dep_R = vpool.id(('depart', t, d, 'Retour'))
            b_B_now = vpool.id(f'boat_B_{t}')
            cnf.append([-var_dep_R, b_B_now])
            cnf.append([-var_dep_R, -vpool.id(f'boat_B_{t+1}')])
            cnf.append([-var_dep_R, vpool.id(f'boat_A_{t+d}')])
            
            passengers_R = []
            for p in range(N):
                p_emb_R = vpool.id(f'embarque_R_{p}_{t}')
                passengers_R.append(p_emb_R)
                if durations[p] > d: cnf.append([-var_dep_R, -p_emb_R])
                
                if d > 1:
                     cnf.append([-var_dep_R, -p_emb_R, vpool.id(('x', p, 'BR', t+1))])
                     for k in range(1, d):
                          cnf.append([-var_dep_R, -p_emb_R, vpool.id(('x', p, 'BR', t+k))])
                cnf.append([-var_dep_R, -p_emb_R, vpool.id(('x', p, 'A', t+d))])
            
            cnf.append([-var_dep_R] + passengers_R)
            cnf.extend(CardEnc.atmost(lits=passengers_R, bound=c, vpool=vpool))
            
            for k in range(1, d):
                if t + k < T:
                    for d2 in possible_durations:
                        cnf.append([-var_dep_R, -vpool.id(('depart', t+k, d2, 'Aller'))])
                        cnf.append([-var_dep_R, -vpool.id(('depart', t+k, d2, 'Retour'))])

    s = Minisat22()
    s.append_formula(cnf.clauses)
    if s.solve():
        model = s.get_model()
        solution = []
        for t in range(T):
            for d in possible_durations:
                if vpool.id(('depart', t, d, 'Aller')) in model:
                    chickens = []
                    for p in range(N):
                        if vpool.id(f'embarque_{p}_{t}') in model: chickens.append(p + 1)
                    if chickens: solution.append((t, chickens))
                if vpool.id(('depart', t, d, 'Retour')) in model:
                    chickens = []
                    for p in range(N):
                        if vpool.id(f'embarque_R_{p}_{t}') in model: chickens.append(p + 1)
                    if chickens: solution.append((t, chickens))
        return solution
    return None

def find_duration(durations: list[int], c: int) -> int:
    T = 1
    while True:
        if gen_solution(durations, c, T) is not None:
            return T
        T += 1