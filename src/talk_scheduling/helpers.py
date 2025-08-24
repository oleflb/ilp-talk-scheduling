import pulp


def pulp_min(
    problem: pulp.LpProblem,
    a: pulp.LpVariable,
    b: pulp.LpVariable,
    sel: pulp.LpVariable,
    *,
    M: float,
):
    """
    Compute the min of two variable a and b using a binary variable sel.
    This function adds constraints such that sel is forced to be 0 if a <= b or 1 if b < a.

    Parameters:
    - problem: The pulp.LpProblem instance to which the constraints will be added.
    - a: The first variable.
    - b: The second variable.
    - sel: The binary variable that indicates which of a or b is smaller.
    - M: A large constant used for the constraints.
    """
    problem += a - b <= M * sel
    problem += b - a <= M * (1 - sel)


def pulp_max(
    problem: pulp.LpProblem,
    a: pulp.LpVariable,
    b: pulp.LpVariable,
    sel: pulp.LpVariable,
    *,
    M: float,
):
    """
    Compute the max of two variable a and b using a binary variable sel.
    This function adds constraints such that sel is forced to be 0 if a >= b or 1 if b > a.

    Parameters:
    - problem: The pulp.LpProblem instance to which the constraints will be added.
    - a: The first variable.
    - b: The second variable.
    - sel: The binary variable that indicates which of a or b is larger.
    - M: A large constant used for the constraints.
    """
    pulp_min(problem, -a, -b, sel, M=M)


def pulp_select(
    problem: pulp.LpProblem,
    a: pulp.LpVariable,
    b: pulp.LpVariable,
    output: pulp.LpVariable,
    sel: pulp.LpVariable,
    *,
    M: float,
):
    """
    Select between two variables a and b using a binary variable sel.
    This function adds constraints such that sel is forced to be 0 if the output should be a or 1 if the output should be b.

    Parameters:
    - problem: The pulp.LpProblem instance to which the constraints will be added.
    - a: The first variable.
    - b: The second variable.
    - c: The output variable that will be equal to either a or b.
    - sel: The binary variable that indicates which of a or b is selected.
    - M: A large constant used for the constraints.
    """
    problem += output <= a + M * sel
    problem += output >= a - M * sel
    problem += output <= b + M * (1 - sel)
    problem += output >= b - M * (1 - sel)


def pulp_or(
    problem: pulp.LpProblem,
    *constraints: list[pulp.LpConstraint],
    or_variables: list[pulp.LpVariable],
    M: float = 1e6,
    number_of_true_terms: int | None = None,
):
    """
    Adds an OR constraint between multiple groups of AND constraints.
    """

    for constraint_group, or_variable in zip(constraints, or_variables):
        for constraint in constraint_group:
            constraint_expr = constraint.expr  # lhs - rhs

            match constraint.sense:
                case pulp.LpConstraintEQ:
                    problem += constraint_expr <= M * (1 - or_variable)
                    problem += constraint_expr >= -M * (1 - or_variable)
                case pulp.LpConstraintLE:
                    problem += constraint_expr <= M * (1 - or_variable)
                case pulp.LpConstraintGE:
                    problem += constraint_expr >= -M * (1 - or_variable)
                case _:
                    raise ValueError(f"Unknown constraint sense: {constraint.sense}")

    if number_of_true_terms is not None:
        problem += (
            pulp.lpSum(or_variables[idx] for idx in range(len(constraints)))
            == number_of_true_terms
        )
    else:
        problem += pulp.lpSum([var for var in or_variables]) >= 1
