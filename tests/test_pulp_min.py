import pulp
from random import randint

from talk_scheduling.helpers import pulp_min, pulp_max


def solve_pulp_min(a: float, b: float, *, M: float = 1e6) -> tuple[str, int]:
    problem = pulp.LpProblem("test-problem", pulp.LpMinimize)
    pulp_solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=15)

    x = pulp.LpVariable("x")
    y = pulp.LpVariable("y")
    c = pulp.LpVariable("c", 0, 1, cat=pulp.LpBinary)
    problem += x == a
    problem += y == b
    pulp_min(problem, x, y, c, M=M)
    
    problem.solve(pulp_solver)

    return pulp.LpStatus[problem.status], pulp.value(c)


def test_pulp_min_equal():
    for i in range(100):
        status, c = solve_pulp_min(i, i)
        assert status == "Optimal"
        assert c == 0


def test_pulp_min():
    for _ in range(1000):
        a = randint(-1000, 1000)
        b = randint(-1000, 1000)
        status, c = solve_pulp_min(a, b)

        assert status == "Optimal"
        if c == 0:
            assert a <= b
        else:
            assert a > b

def solve_pulp_max(a: float, b: float, *, M: float = 1e6) -> tuple[str, int]:
    problem = pulp.LpProblem("test-problem", pulp.LpMinimize)
    pulp_solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=15)

    x = pulp.LpVariable("x")
    y = pulp.LpVariable("y")
    c = pulp.LpVariable("c", 0, 1, cat=pulp.LpBinary)
    problem += x == a
    problem += y == b
    pulp_max(problem, x, y, c, M=M)
    
    problem.solve(pulp_solver)

    return pulp.LpStatus[problem.status], pulp.value(c)


def test_pulp_max_equal():
    for i in range(100):
        status, c = solve_pulp_max(i, i)
        assert status == "Optimal"
        assert c == 0


def test_pulp_max():
    for _ in range(1000):
        a = randint(-1000, 1000)
        b = randint(-1000, 1000)
        status, c = solve_pulp_max(a, b)

        assert status == "Optimal"
        if c == 0:
            assert a >= b
        else:
            assert a < b
