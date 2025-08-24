import pulp

from talk_scheduling.helpers import pulp_min

a = 633
b = 678

problem = pulp.LpProblem("test-problem", pulp.LpMinimize)
solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=15)

x = pulp.LpVariable("x")
y = pulp.LpVariable("y")
c = pulp.LpVariable("c", cat=pulp.LpBinary)
problem += x == a
problem += y == b
pulp_min(problem, x, y, c, M=1e6)

problem.solve(solver)

print(pulp.LpStatus[problem.status])
print(pulp.value(x))
print(pulp.value(y))
print(pulp.value(c))
