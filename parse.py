# -*- coding: utf-8 -*-

LAMBDA_MARKERS = {"lambda", "λ", "eps", "ε"}


def is_lambda(tok):
    return tok in LAMBDA_MARKERS


def read_grammar(path):
    lines = [l for l in open(path, encoding="utf-8").read().splitlines() if l.strip() != ""]
    nonterminals = set(lines[0].split())
    terminals = set(lines[1].split())
    n = int(lines[2].split()[0])

    prods = {}
    idx = 3
    for _ in range(n):
        parts = lines[idx].replace("->", " ").split()
        idx += 1
        A = parts[0]
        rhs_str = "".join(parts[1:])
        if not rhs_str or is_lambda(rhs_str):
            rhs = ()
        else:
            rhs = tuple(rhs_str)
        prods.setdefault(A, []).append(rhs)
        nonterminals.add(A)

    start = lines[idx].split()[0]
    idx += 1

    # returnam si liniile ramase (folosite de cyk pentru cuvant)
    rest = lines[idx:]

    return nonterminals, terminals, prods, start, rest


def parse_mode(text):
    text = text.strip().lower()
    if "ambele" in text or "both" in text:
        return "both"
    if "goala" in text or "goală" in text or "empty" in text or "vida" in text:
        return "empty"
    return "final"


def parse_pda_input(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read().splitlines()

    lines = raw
    idx = 0

    def next_line():
        nonlocal idx
        line = lines[idx] if idx < len(lines) else ""
        idx += 1
        return line

    states = next_line().split()
    input_alphabet = next_line().split()
    n = int(next_line().split()[0])

    transitions = []
    for _ in range(n):
        parts = next_line().split()
        cur, read, pop, nxt, push = parts[0], parts[1], parts[2], parts[3], parts[4]
        transitions.append((cur, read, pop, nxt, push))

    start_state = next_line().split()[0]
    init_stack = next_line().split()[0]
    final_states = set(next_line().split())
    mode_raw = next_line().strip().lower()
    word_line = next_line().strip()

    mode = parse_mode(mode_raw)
    word = "" if (word_line == "" or is_lambda(word_line)) else word_line

    return {
        "states": set(states),
        "input_alphabet": set(input_alphabet),
        "transitions": transitions,
        "start_state": start_state,
        "init_stack": init_stack,
        "final_states": final_states,
        "mode": mode,
        "word": word,
    }