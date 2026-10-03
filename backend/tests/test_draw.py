import random

import pytest

from app.draw import derangement, draw_pairs


@pytest.mark.parametrize("n", [2, 3, 4, 5, 8, 20, 100])
def test_derangement_is_valid_permutation_without_fixed_points(n):
    for _ in range(200):
        perm = derangement(n)
        assert sorted(perm) == list(range(n))  # cada um é sorteado exatamente uma vez
        assert all(i != t for i, t in enumerate(perm))  # ninguém tira a si mesmo


def test_derangement_rejects_single_element():
    with pytest.raises(ValueError):
        derangement(1)


def test_draw_pairs_requires_three_people():
    with pytest.raises(ValueError):
        draw_pairs(["a", "b"])


def test_draw_pairs_each_gives_and_receives_once():
    people = [f"p{i}" for i in range(7)]
    pairs = draw_pairs(people)
    assert [g for g, _ in pairs] == people
    assert sorted(r for _, r in pairs) == sorted(people)
    assert all(g != r for g, r in pairs)


def test_all_derangements_of_three_occur():
    # Existem exatamente 2 derangements de 3 elementos; ambos devem aparecer.
    rng = random.Random(1)
    seen = {tuple(derangement(3, rng)) for _ in range(100)}
    assert seen == {(1, 2, 0), (2, 0, 1)}


def test_seeded_rng_is_deterministic():
    assert derangement(10, random.Random(42)) == derangement(10, random.Random(42))
