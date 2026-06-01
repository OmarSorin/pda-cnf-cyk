# -*- coding: utf-8 -*-
from collections import deque
from parse import is_lambda, LAMBDA_MARKERS, parse_pda_input

# pus niste limite ca sa nu intre in bucla infinita pe automate nedeterministe
MAX_STACK = 2000
MAX_CONFIGS = 5_000_000


def tokenize_push(push_str, stack_symbols):
    # imparte sirul de push in simboluri individuale
    # sortam dupa lungime ca sa gasim mai intai simbolurile mai lungi (ex: Z0 inainte de Z)
    if is_lambda(push_str):
        return []
    ordered = sorted(stack_symbols, key=len, reverse=True)
    result = []
    i = 0
    while i < len(push_str):
        matched = None
        for s in ordered:
            if s and push_str.startswith(s, i):
                matched = s
                break
        if matched is None:
            matched = push_str[i]
        result.append(matched)
        i += len(matched)
    return result


def run_pda(spec):
    transitions = spec["transitions"]
    start = spec["start_state"]
    init_stack = spec["init_stack"]
    finals = spec["final_states"]
    mode = spec["mode"]
    word = spec["word"]

    # colectam toate simbolurile de stiva ca sa stim cum sa tokenizam push-ul
    stack_symbols = {init_stack}
    for (_c, _r, pop, _n, _p) in transitions:
        if not is_lambda(pop):
            stack_symbols.add(pop)
    for (_c, _r, _pop, _n, push) in transitions:
        if not is_lambda(push):
            for ch in push:
                stack_symbols.add(ch)

    n = len(word)

    def accepts(state, pos, stack):
        if pos != n:
            return False
        if mode == "final":
            return state in finals
        if mode == "empty":
            return len(stack) == 0
        if mode == "both":
            return state in finals and len(stack) == 0
        return False

    # folosim BFS ca sa exploram toate configuratiile posibile
    # o configuratie e (stare curenta, pozitie in cuvant, continutul stivei)
    start_config = (start, 0, (init_stack,))
    visited = {start_config}
    queue = deque([start_config])
    explored = 0

    while queue:
        explored += 1
        if explored > MAX_CONFIGS:
            return False
        state, pos, stack = queue.popleft()

        if accepts(state, pos, stack):
            return True

        top = stack[0] if stack else None
        cur_sym = word[pos] if pos < n else None

        for (c, r, pop, nxt, push) in transitions:
            if c != state:
                continue

            if is_lambda(r):
                consume = 0
            else:
                if cur_sym is None or r != cur_sym:
                    continue
                consume = 1

            if is_lambda(pop):
                rest = stack
            else:
                if top is None or top != pop:
                    continue
                rest = stack[1:]

            pushed = tokenize_push(push, stack_symbols)
            new_stack = tuple(pushed) + tuple(rest)

            if len(new_stack) > MAX_STACK:
                continue

            new_config = (nxt, pos + consume, new_stack)
            if new_config not in visited:
                visited.add(new_config)
                queue.append(new_config)

    return False


def main():
    spec = parse_pda_input("pda_input.txt")
    accepted = run_pda(spec)
    result = "Acceptat" if accepted else "Respins"
    print(result)
    with open("pda_output.txt", "w", encoding="utf-8") as f:
        f.write(result + "\n")


if __name__ == "__main__":
    main()