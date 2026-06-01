# -*- coding: utf-8 -*-

from parse import read_grammar, is_lambda, LAMBDA_MARKERS

def cyk(prods, start, word):
    n = len(word)

    # cuvantul vid e acceptat doar daca exista productia S -> lambda
    if n == 0:
        accepted = any(rhs == () for rhs in prods.get(start, []))
        return accepted, []

    # T[i][j] = multimea neterminalelor care pot genera subsirul word[i..j]
    T = [[set() for _ in range(n)] for _ in range(n)]

    # cazul de baza: completam diagonala cu productiile A -> a
    for i in range(n):
        a = word[i]
        for A, rhss in prods.items():
            for rhs in rhss:
                if len(rhs) == 1 and rhs[0] == a:
                    T[i][i].add(A)

    # cazul recursiv: subsiruri din ce in ce mai lungi
    # pentru T[i][j] incercam toate punctele de taiere k
    for length in range(2, n + 1):
        for i in range(0, n - length + 1):
            j = i + length - 1
            for k in range(i, j):
                left = T[i][k]
                right = T[k + 1][j]
                if not left or not right:
                    continue
                for A, rhss in prods.items():
                    for rhs in rhss:
                        if len(rhs) == 2 and rhs[0] in left and rhs[1] in right:
                            T[i][j].add(A)

    # cuvantul e acceptat daca simbolul de start se afla in T[0][n-1]
    return start in T[0][n - 1], T


def format_table(T, word):
    n = len(word)
    if n == 0:
        return "(cuvant vid - tabela goala)"

    def cell(i, j):
        s = T[i][j]
        return "-" if not s else "{" + ",".join(sorted(s)) + "}"

    width = max(3, max(len(cell(i, j)) for i in range(n) for j in range(i, n)))

    lines = []
    header = "j:".ljust(5) + " ".join(
        ("a" + str(j + 1) + "=" + word[j]).center(width) for j in range(n))
    lines.append(header)
    lines.append("-" * len(header))

    for i in range(n):
        row = []
        for j in range(n):
            row.append(" " * width if j < i else cell(i, j).center(width))
        lines.append(("i=" + str(i + 1)).ljust(5) + " ".join(row))

    return "\n".join(lines)


def main():
    nonterminals, terminals, prods, start, rest = read_grammar("cyk_input.txt")
    word = rest[0].strip() if rest and not is_lambda(rest[0].strip()) else ""
    accepted, T = cyk(prods, start, word)
    result = ("DA" if accepted else "NU") + "\n\nTabela CYK:\n" + format_table(T, word)
    print(result)
    with open("cyk_output.txt", "w", encoding="utf-8") as f:
        f.write(result + "\n")


if __name__ == "__main__":
    main()