import random
from collections.abc import Sequence

_rng = random.SystemRandom()


def derangement(n: int, rng: random.Random | None = None) -> list[int]:
    """Permutação aleatória de 0..n-1 sem pontos fixos (ninguém tira a si mesmo).

    Embaralha até não haver pontos fixos. A probabilidade de sucesso por tentativa
    tende a 1/e (~37%), então são ~2,7 tentativas em média, e o resultado é
    uniforme entre todos os derangements.
    """
    if n < 2:
        raise ValueError("É preciso ao menos 2 elementos para um derangement.")
    rng = rng or _rng
    perm = list(range(n))
    while True:
        rng.shuffle(perm)
        if all(i != target for i, target in enumerate(perm)):
            return perm


def draw_pairs[T](people: Sequence[T], rng: random.Random | None = None) -> list[tuple[T, T]]:
    """Retorna (quem presenteia, quem recebe) para cada pessoa."""
    if len(people) < 3:
        raise ValueError("O sorteio exige pelo menos 3 participantes.")
    targets = derangement(len(people), rng)
    return [(people[i], people[t]) for i, t in enumerate(targets)]
