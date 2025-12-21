from pysat.solvers import Minisat22
from pysat.formula import CNFPlus, IDPool
from pysat.card import CardEnc

def gen_solution(durations: list[int], c: int, T: int) -> None | list[tuple]:
    vpool = IDPool()
    cnf = CNFPlus()
    N = len(durations)
    possible_durations = list(set(durations))

    # --- 1. INITIALISATION ---
    # t=0 : Tout le monde est en A, Bateau en A
    cnf.append([vpool.id(('boat_at_A', 0))])
    for p in range(N):
        cnf.append([vpool.id(('at_A', 0, p))])

    # t=T : Tout le monde doit être en B
    for p in range(N):
        cnf.append([-vpool.id(('at_A', T, p))])

    # --- 2. BOUCLE TEMPORELLE ---
    for t in range(T):
        
        # A. Unicité du départ : Au plus 1 départ par instant t
        lits_depart = [vpool.id(('depart', t, d)) for d in possible_durations]
        cnf.extend(CardEnc.atmost(lits=lits_depart, bound=1, vpool=vpool))

        # Pour chaque durée possible d
        for d in possible_durations:
            
            # Si le voyage dépasse le temps imparti T, il est interdit
            if t + d > T:
                cnf.append([-vpool.id(('depart', t, d))])
                continue

            var_dep = vpool.id(('depart', t, d))
            
            # --- B. Contraintes du voyage ---
            
            # 1. Gestion de la Barque "Occupée" (Busy)
            # Si depart(t, d), alors PAS de départ entre t+1 et t+d-1
            for k in range(1, d):
                if t + k < T:
                    for d_next in possible_durations:
                        cnf.append([-var_dep, -vpool.id(('depart', t+k, d_next))])

            # 2. Groupe de passagers (on_boat)
            passengers = [vpool.id(('on_boat', p, t)) for p in range(N)]
            
            # Capacité : Max C passagers
            cnf.extend(CardEnc.atmost(lits=passengers, bound=c, vpool=vpool))
            
            # Minimum : Au moins 1 passager
            cnf.append([-var_dep] + passengers)

            # --- C. Cohérence passagers / bateau ---
            for p in range(N):
                p_on_boat = vpool.id(('on_boat', p, t))
                
                # a. Vitesse Limite
                if durations[p] > d:
                    cnf.append([-var_dep, -p_on_boat])

                # b. Synchro Position (Si p monte, elle doit être du même côté que le bateau)
                b_at_A = vpool.id(('boat_at_A', t))
                p_at_A = vpool.id(('at_A', t, p))
                # p_on_boat => (p_at_A == b_at_A)
                cnf.append([-var_dep, -p_on_boat, -b_at_A, p_at_A])
                cnf.append([-var_dep, -p_on_boat, b_at_A, -p_at_A])

                # c. Changement de Rive (Arrivée)
                # Si p est dans le bateau, elle change de côté à t+d
                p_at_A_next = vpool.id(('at_A', t+d, p))
                cnf.append([-var_dep, -p_on_boat, -p_at_A, -p_at_A_next]) # A -> B
                cnf.append([-var_dep, -p_on_boat, p_at_A, p_at_A_next])   # B -> A
            
            # --- D. Mouvement de la Barque ---
            # Si départ, la barque change de côté à t+d
            b_at_A_next = vpool.id(('boat_at_A', t+d))
            cnf.append([-var_dep, -vpool.id(('boat_at_A', t)), -b_at_A_next])
            cnf.append([-var_dep, vpool.id(('boat_at_A', t)), b_at_A_next])


        # --- 3. INERTIE (PERSISTENCE) ---
        if t + 1 <= T:
             # On cherche s'il y a un départ à (t+1 - d) qui arrive maintenant.
             arrival_causes = []
             for d in possible_durations:
                 start = t + 1 - d
                 if start >= 0:
                     dep_var = vpool.id(('depart', start, d))
                     arrival_causes.append(dep_var)
                     
                     # PERSISTENCE CONDITIONNELLE :
                     # Si un bateau arrive (déclenché par dep_var), mais que p n'est PAS dedans,
                     # alors p ne doit PAS changer de côté.
                     # Clause : depart(start) AND !on_boat(p, start) => (at_A(t) == at_A(t+1))
                     
                     for p in range(N):
                         p_on_boat_start = vpool.id(('on_boat', p, start))
                         
                         # Si (At A et !Change -> Reste A) est trivial.
                         # On veut: Si At A (t) et !OnBoat => At A (t+1)
                         # ~dep v on_boat v ~at_A(t) v at_A(t+1)
                         cnf.append([-dep_var, p_on_boat_start, -vpool.id(('at_A', t, p)), vpool.id(('at_A', t+1, p))])
                         
                         # Si At B (t) et !OnBoat => At B (t+1) (donc !at_A(t+1))
                         # ~dep v on_boat v at_A(t) v ~at_A(t+1)
                         cnf.append([-dep_var, p_on_boat_start, vpool.id(('at_A', t, p)), -vpool.id(('at_A', t+1, p))])

             # PERSISTENCE GLOBALE (Cas où AUCUN bateau n'arrive)
             # Si l'état du bateau change, c'est qu'il est ARRIVÉ.
             cnf.append([vpool.id(('boat_at_A', t)), -vpool.id(('boat_at_A', t+1))] + arrival_causes)
             cnf.append([-vpool.id(('boat_at_A', t)), vpool.id(('boat_at_A', t+1))] + arrival_causes)
             
             # Si l'état d'une poule change, c'est qu'un bateau est ARRIVÉ (condition nécessaire globale)
             for p in range(N):
                 cnf.append([vpool.id(('at_A', t, p)), -vpool.id(('at_A', t+1, p))] + arrival_causes)
                 cnf.append([-vpool.id(('at_A', t, p)), vpool.id(('at_A', t+1, p))] + arrival_causes)

    # Résolution
    s = Minisat22()
    # On ajoute la formule CNFPlus (clauses et constraints)
    s.append_formula(cnf.clauses) 
    if s.solve():
        model = s.get_model()
        solution = []
        for t in range(T):
            for d in possible_durations:
                if vpool.id(('depart', t, d)) in model:
                    chickens = []
                    for p in range(N):
                        if vpool.id(('on_boat', p, t)) in model:
                            chickens.append(p + 1)
                    solution.append((t, chickens))
        return solution
    else:
        return None

def find_duration(durations: list[int], c: int) -> int:
    T = 0
    while True:
        sol = gen_solution(durations, c, T)
        if sol is not None:
            return T
        T += 1
