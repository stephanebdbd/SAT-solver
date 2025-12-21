from pysat.solvers import Minisat22
from pysat.formula import CNFPlus, IDPool
from pysat.card import CardEnc

def gen_solution(durations: list[int], c: int, T: int) -> None | list[tuple]:
    """
    Contexte du Projet : Problème des Poules (SAT Solver)
    
    On résout un problème de planification où N poules doivent traverser une rivière avec une barque de capacité c.
    Chaque poule a une vitesse propre, et la traversée prend le temps de la poule la plus lente.

    1. Dictionnaire des Variables
    Nous utilisons pysat.IDPool avec des tuples pour identifier les variables.

    Variables d'État (State) : ('x', p, s, t)
        Représente la position de la poule p à l'instant t.
        s ∈ {'A', 'B', 'BA', 'BR'} : Rive A, Rive B, Barque Aller, Barque Retour.
        Sémantique : Si Vrai, la poule p est dans l'état s à l'instant t.
        
    Variables d'Événement (Event) :
        ('depart', t, d, 'Aller'/'Retour') : Un bateau part à l'instant t pour une durée d.
        ('embarque', p, t) : Helper variable, Vrai si la poule p embarque dans un trip Aller à t.
        
    Variables d'Inertie Bateau :
        ('boat_at_A', t) / ('boat_at_B', t) : Localisation du bateau (disponible pour un départ).
    """
    vpool = IDPool()
    cnf = CNFPlus()
    N = len(durations)
    possible_durations = list(set(durations))
    STATES = ['A', 'B', 'BA', 'BR']

    # --- initialisation ---
    # Toutes les poules commencent sur la Rive A
    for p in range(N):
        cnf.append([vpool.id(('x', p, 'A', 0))])
    # Le bateau est initialement à A
    cnf.append([vpool.id(('boat_at_A', 0))])
    cnf.append([-vpool.id(('boat_at_B', 0))]) # Il n'est pas à B

    # --- contraintes globales ---
    for t in range(T + 1): 
        # Unicité de l'état : Une poule ne peut être que dans un seul état à la fois
        for p in range(N):
            lits_states = [vpool.id(('x', p, s, t)) for s in STATES]
            # CardEnc.equals(bound=1) impose Exactement 1 état vrai
            cnf.extend(CardEnc.equals(lits=lits_states, bound=1, vpool=vpool))

        if t < T: 
            # Capacité de la Barque (Contrainte d'État)
            # Le nombre de poules dans l'état 'BA' (Barque Aller) ne doit pas dépasser C
            lits_BA = [vpool.id(('x', p, 'BA', t)) for p in range(N)]
            cnf.extend(CardEnc.atmost(lits=lits_BA, bound=c, vpool=vpool))
            
            # Idem pour 'BR' (Barque Retour)
            lits_BR = [vpool.id(('x', p, 'BR', t)) for p in range(N)]
            cnf.extend(CardEnc.atmost(lits=lits_BR, bound=c, vpool=vpool))

    # À l'instant T, toutes les poules doivent être sur la Rive B
    for p in range(N):
        cnf.append([vpool.id(('x', p, 'B', T))])

    # --- transitions ---
    for t in range(T):
        # Unicité du départ : Au maximum 1 départ de bateau par instant t
        lits_depart = [vpool.id(('depart', t, d, sens)) for d in possible_durations for sens in ["Aller", "Retour"]]
        cnf.extend(CardEnc.atmost(lits=lits_depart, bound=1, vpool=vpool))
        
        # Listes des départs possibles temporellement
        departs_Aller = [vpool.id(('depart', t, d, 'Aller')) for d in possible_durations if t+d <= T]
        departs_Retour = [vpool.id(('depart', t, d, 'Retour')) for d in possible_durations if t+d <= T]

        # --- logique des poules ---
        for p in range(N):
            # Définition explicite des variables pour lisibilité
            var_x_A      = vpool.id(('x', p, 'A', t))
            var_x_B      = vpool.id(('x', p, 'B', t))
            var_x_BA     = vpool.id(('x', p, 'BA', t))
            var_x_BR     = vpool.id(('x', p, 'BR', t))

            var_x_A_next   = vpool.id(('x', p, 'A', t+1))
            var_x_B_next   = vpool.id(('x', p, 'B', t+1))
            var_x_BA_next  = vpool.id(('x', p, 'BA', t+1))
            var_x_BR_next  = vpool.id(('x', p, 'BR', t+1))

            # Helper variables, elles indiquent l'action "Monter dans le bateau"
            p_embarque     = vpool.id(('embarque', p, t))
            p_embarque_R   = vpool.id(('embarque_R', p, t))

            # Si on est en A, au prochain tour on est soit encore en A, soit en BA (embarqué), soit en B
            cnf.append([-var_x_A, var_x_A_next, var_x_BA_next, var_x_B_next])
            # Pareil pour B
            cnf.append([-var_x_B, var_x_B_next, var_x_BR_next, var_x_A_next])
            
            # Si on est dans la barque (BA), au prochain tour soit on y reste, soit on arrive (B)
            cnf.append([-var_x_BA, var_x_BA_next, var_x_B_next])
            cnf.append([-var_x_BR, var_x_BR_next, var_x_A_next])
            
            # Pour passer de A à BA, il FAUT que 'embarque' soit Vrai
            cnf.append([-var_x_A, -var_x_BA_next, p_embarque])
            # Pour passer de A à B directement (cas d=1), il FAUT 'embarque'
            cnf.append([-var_x_A, -var_x_B_next, p_embarque])
            
            # Si 'embarque' est Vrai, la poule devrait être en A
            cnf.append([-p_embarque, var_x_A])
            
            # Même logique pour le Retour (B -> BR -> A)
            cnf.append([-var_x_B, -var_x_BR_next, p_embarque_R])
            cnf.append([-var_x_B, -var_x_A_next, p_embarque_R])
            cnf.append([-p_embarque_R, var_x_B])

            # Si une poule embarque, ALORS un départ de bateau correspondant DOIT exister
            if departs_Aller: cnf.append([-p_embarque] + departs_Aller)
            else: cnf.append([-p_embarque]) # Pas de départ possible = Pas d'embarquement
            
            if departs_Retour: cnf.append([-p_embarque_R] + departs_Retour)
            else: cnf.append([-p_embarque_R])
            

        # --- logique du bateau ---
        b_now = vpool.id(('boat_at_A', t))
        b_next = vpool.id(('boat_at_A', t+1))
        
        # Identifier les arrivées de bateau
        arrivals_Retour = []
        for d in possible_durations:
             st = t + 1 - d
             if st >= 0: arrivals_Retour.append(vpool.id(('depart', st, d, 'Retour')))
        
        # Si le bateau part (Aller), il n'est plus à A au tour suivant
        if departs_Aller:
             for start in departs_Aller: cnf.append([-start, -b_next])
        
        # Si le bateau arrive (Retour), il devient disponible à A au tour suivant
        if arrivals_Retour:
             for arr in arrivals_Retour: cnf.append([-arr, b_next])
        
        # S'il ne part pas et n'arrive pas, il garde sa position
        cnf.append([-b_now, b_next] + departs_Aller)
        cnf.append([b_now, -b_next] + arrivals_Retour)


        # --- moteur de déplacement ---
        # C'est ici que l'événement "Départ" force les transitions d'états futures
        for d in possible_durations:
            if t + d > T:
                # Impossible de lancer un départ si on dépasse T
                cnf.append([-vpool.id(('depart', t, d, 'Aller'))])
                cnf.append([-vpool.id(('depart', t, d, 'Retour'))])
                continue

            # DÉPART ALLER (A -> B en d minutes)
            var_dep_A = vpool.id(('depart', t, d, 'Aller'))
            
            # Pré-conditions bateau
            cnf.append([-var_dep_A, b_now]) # Le bateau doit être à A
            cnf.append([-var_dep_A, -b_next]) # Il quitte A
            cnf.append([-var_dep_A, vpool.id(('boat_at_B', t+d))]) # Il sera à B dans d minutes
            
            passengers = []
            for p in range(N):
                p_emb = vpool.id(('embarque', p, t))
                passengers.append(p_emb)
                
                # Si duration < vitesse poule, elle ne peut pas prendre ce départ
                if durations[p] > d: cnf.append([-var_dep_A, -p_emb])
                
                #Force le chemin de l'état
                if d > 1:
                     # t -> t+1 : La poule entre dans l'état 'BA'
                     cnf.append([-var_dep_A, -p_emb, vpool.id(('x', p, 'BA', t+1))])
                     # t+1 ... t+d-1 : La poule reste dans l'état 'BA'
                     for k in range(1, d):
                          cnf.append([-var_dep_A, -p_emb, vpool.id(('x', p, 'BA', t+k))])
                
                # t+d : La poule arrive en 'B'
                cnf.append([-var_dep_A, -p_emb, vpool.id(('x', p, 'B', t+d))])
            
            # Le bateau ne part pas vide
            cnf.append([-var_dep_A] + passengers)
            
            # Capacité Max C
            cnf.extend(CardEnc.atmost(lits=passengers, bound=c, vpool=vpool))

            # Pas d'autre départ pendant le trajet
            for k in range(1, d):
                if t + k < T:
                    for d2 in possible_durations:
                        cnf.append([-var_dep_A, -vpool.id(('depart', t+k, d2, 'Aller'))])
                        cnf.append([-var_dep_A, -vpool.id(('depart', t+k, d2, 'Retour'))])

            # DÉPART RETOUR (B -> A en d minutes)
            var_dep_R = vpool.id(('depart', t, d, 'Retour'))
            b_B_now = vpool.id(('boat_at_B', t))
            
            cnf.append([-var_dep_R, b_B_now])
            cnf.append([-var_dep_R, -vpool.id(('boat_at_B', t+1))])
            cnf.append([-var_dep_R, vpool.id(('boat_at_A', t+d))])
            
            passengers_R = []
            for p in range(N):
                p_emb_R = vpool.id(('embarque_R', p, t))
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

    # --- Résolution et reconstruction ---
    s = Minisat22()
    s.append_formula(cnf.clauses)
    if s.solve():
        model = s.get_model()
        solution = []
        for t in range(T):
            for d in possible_durations:
                # Si un Départ Aller est trouvé
                if vpool.id(('depart', t, d, 'Aller')) in model:
                    chickens = []
                    #On identifie les passagers grâce aux variables helpers 'embarque'
                    for p in range(N):
                        if vpool.id(('embarque', p, t)) in model:
                            chickens.append(p + 1)
                    if chickens: solution.append((t, chickens))
                
                # Si un Départ Retour est trouvé
                elif vpool.id(('depart', t, d, 'Retour')) in model:
                    chickens = []
                    for p in range(N):
                        if vpool.id(('embarque_R', p, t)) in model:
                            chickens.append(p + 1)
                    if chickens: solution.append((t, chickens))
        return solution
    return None

def find_duration(durations: list[int], c: int) -> int:
    """Cherche la durée minimale T en incrémentant T tant qu'aucune solution n'est trouvée."""
    T = 1
    while True:
        if gen_solution(durations, c, T) is not None:
            return T
        T += 1