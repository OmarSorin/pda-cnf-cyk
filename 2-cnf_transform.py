# -*- coding: utf-8 -*-
from itertools import combinations

from parse import read_grammar, is_lambda, LAMBDA_MARKERS

def fresh_char(used):
    # returneaza prima litera majuscula care nu e deja folosita
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if c not in used:
            used.add(c)
            return c
    raise ValueError("nu mai sunt litere disponibile")


def add_new_start(prods, nonterminals, start):
    # pasul 1: adaugam un nou simbol de start ca sa nu apara S in dreapta vreunei productii
    used = set(nonterminals)
    s0 = fresh_char(used)
    nonterminals = nonterminals | {s0}
    prods = dict(prods)
    prods[s0] = [(start,)]
    return prods, nonterminals, s0


def nullable_set(prods):
    # gasim toate neterminalele care pot genera lambda
    nullable = set()
    changed = True
    while changed:
        changed = False
        for A, rhss in prods.items():
            if A in nullable:
                continue
            for rhs in rhss:
                if all(sym in nullable for sym in rhs):
                    nullable.add(A)
                    changed = True
                    break
    return nullable


def eliminate_lambda(prods, start):
    # pasul 2: eliminam productiile lambda
    # pentru fiecare productie care contine simboluri anulabile generam toate variantele
    # fara acel simbol
    nullable = nullable_set(prods)
    new = {A: set() for A in prods}

    for A, rhss in prods.items():
        for rhs in rhss:
            if len(rhs) == 0:
                continue
            nidx = [i for i, s in enumerate(rhs) if s in nullable]
            for r in range(len(nidx) + 1):
                for combo in combinations(nidx, r):
                    combo = set(combo)
                    keep = tuple(rhs[i] for i in range(len(rhs)) if i not in combo)
                    if keep:
                        new[A].add(keep)

    # pastram S -> lambda doar daca cuvantul vid e in limbaj
    if start in nullable:
        new[start].add(())

    return {A: list(v) for A, v in new.items()}


def eliminate_unit(prods, nonterminals):
    # pasul 3: eliminam productiile unitare de forma A -> B
    # pentru fiecare A gasim toate neterminalele accesibile prin lanturi unitare
    # si copiem productiile lor direct la A
    new = {A: set() for A in prods}
    for A in prods:
        reach = {A}
        stack = [A]
        while stack:
            X = stack.pop()
            for rhs in prods.get(X, []):
                if len(rhs) == 1 and rhs[0] in nonterminals:
                    B = rhs[0]
                    if B not in reach:
                        reach.add(B)
                        stack.append(B)
        for B in reach:
            for rhs in prods.get(B, []):
                if not (len(rhs) == 1 and rhs[0] in nonterminals):
                    new[A].add(rhs)
    return {A: list(v) for A, v in new.items()}


def remove_useless(prods, terminals, start):
    # pasul 4: eliminam simbolurile inutile
    # intai gasim ce poate genera un sir de terminale (generating)
    # apoi eliminam ce nu e accesibil din start (reachable)
    generating = set(terminals)
    changed = True
    while changed:
        changed = False
        for A, rhss in prods.items():
            if A in generating:
                continue
            for rhs in rhss:
                if all(s in generating for s in rhs):
                    generating.add(A)
                    changed = True
                    break
    # filtrare, raman doar neterminale generating si productii care contin simboluri generating
    prods2 = {}
    for A, rhss in prods.items():
        if A not in generating:
            continue
        kept = [rhs for rhs in rhss if all(s in generating for s in rhs)]
        if kept:
            prods2[A] = kept

    if start not in prods2:
        return {}

    reachable = {start}
    stack = [start]
    while stack:
        X = stack.pop()
        for rhs in prods2.get(X, []):
            for s in rhs:
                if s not in terminals and s not in reachable:
                    reachable.add(s)
                    stack.append(s)

    return {A: rhss for A, rhss in prods2.items() if A in reachable}


def replace_terminals(prods, terminals, nonterminals):
    # pasul 5: inlocuim terminalele din productiile de lungime >= 2
    # ex: A -> aB devine A -> XB unde X -> a
    used = set(nonterminals)
    term_to_nt = {}

    def get_nt(t):
        if t not in term_to_nt:
            term_to_nt[t] = fresh_char(used)
        return term_to_nt[t]

    new = {}
    for A, rhss in prods.items():
        new[A] = []
        for rhs in rhss:
            if len(rhs) >= 2:
                new[A].append(tuple(get_nt(s) if s in terminals else s for s in rhs))
            else:
                new[A].append(rhs)

    for t, nt in term_to_nt.items():
        new[nt] = [(t,)]
        nonterminals = nonterminals | {nt}

    return new, nonterminals


def binarize(prods, nonterminals):
    # pasul 6: spargem productiile cu mai mult de 2 simboluri
    # ex: A -> BCD devine A -> BX, X -> CD
    used = set(nonterminals)
    new = {}

    for A, rhss in prods.items():
        for rhs in rhss:
            if len(rhs) <= 2:
                new.setdefault(A, []).append(rhs)
            else:
                syms = list(rhs)
                left = A
                while len(syms) > 2:
                    nt = fresh_char(used)
                    nonterminals = nonterminals | {nt}
                    new.setdefault(left, []).append((syms[0], nt))
                    left = nt
                    syms = syms[1:]
                new.setdefault(left, []).append((syms[0], syms[1]))

    return new, nonterminals


def dedupe(prods):
    # scoatem productiile duplicate
    out = {}
    for A, rhss in prods.items():
        seen = set()
        lst = []
        for rhs in rhss:
            if rhs not in seen:
                seen.add(rhs)
                lst.append(rhs)
        out[A] = lst
    return out


def to_cnf(nonterminals, terminals, prods, start):
    nonterminals = set(nonterminals)
    prods, nonterminals, start = add_new_start(prods, nonterminals, start)
    prods = eliminate_lambda(prods, start)
    prods = eliminate_unit(prods, nonterminals)
    prods = remove_useless(prods, terminals, start)
    nonterminals = set(prods.keys())
    prods, nonterminals = replace_terminals(prods, terminals, nonterminals)
    prods, nonterminals = binarize(prods, nonterminals)
    prods = dedupe(prods)
    return prods, nonterminals, start


def render(prods, start, terminals):
    # scriem gramatica in acelasi format ca inputul
    order = [start] + sorted(A for A in prods if A != start)
    all_prods_list = []
    for A in order:
        for rhs in prods.get(A, []):
            all_prods_list.append((A, rhs))

    lines = [
        " ".join(sorted(prods.keys())),
        " ".join(sorted(terminals)),
        str(len(all_prods_list))
    ]
    for A, rhs in all_prods_list:
        rhs_str = "λ" if not rhs else "".join(rhs)
        lines.append(f"{A} -> {rhs_str}")
    lines.append(start)
    return "\n".join(lines)


def main():
    nonterminals, terminals, prods, start, _rest = read_grammar("cnf_input.txt")
    cnf_prods, cnf_nts, new_start = to_cnf(nonterminals, terminals, prods, start)
    result = render(cnf_prods, new_start, terminals)
    print(result)
    with open("cnf_output.txt", "w", encoding="utf-8") as f:
        f.write(result + "\n")


if __name__ == "__main__":
    main()