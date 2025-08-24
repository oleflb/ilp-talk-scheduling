import pulp

from talk_scheduling.helpers import pulp_or


def solve_pulp_or(a: float, b: float, *, M: float = 1e6, number_of_true_terms: int | None = None) -> str:
    problem = pulp.LpProblem("test-problem", pulp.LpMinimize)
    pulp_solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=15)

    x = pulp.LpVariable("x")
    y = pulp.LpVariable("y")
    or_variables = [pulp.LpVariable(f"or_{i}", 0, 1, cat=pulp.LpBinary) for i in range(2)]
    pulp_or(
        problem,
        [x == a],
        [y == b],
        or_variables=or_variables,
        number_of_true_terms=number_of_true_terms,
        M=M,
    )
    # problem += x == a
    problem += 0

    problem.solve(pulp_solver)

    return pulp.LpStatus[problem.status], [pulp.value(var) for var in or_variables]


def test_pulp_or():
    status, result = solve_pulp_or(1, 2, number_of_true_terms=0)
    assert status == "Optimal"
    assert sum(result) == 0

    status, result = solve_pulp_or(1, 2, number_of_true_terms=1)
    assert status == "Optimal"
    assert sum(result) == 1

    status, result = solve_pulp_or(2, 1, number_of_true_terms=2)
    assert status == "Optimal"
    assert sum(result) == 2

    status, result = solve_pulp_or(2, 1)
    assert status == "Optimal"
    assert sum(result) >= 1
