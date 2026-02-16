import numpy as np
from scipy.optimize import linprog, minimize, LinearConstraint, Bounds

def test_linprog_sign():
    print("Testing linprog sign...")
    # min x + 1000y
    # s.t. x + y = 2
    # x in [0, 1], y in [0, 1]
    # Smallest x=1, so y must be 1. Total cost = 1 + 1000 = 1001.
    # If load (2) increases to 2.1, y increases to 1.1, cost increases by 100.
    c = np.array([1, 1000])
    A_eq = np.array([[1, 1]])
    b_eq = np.array([2])
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=[(0, 1), (0, 1)], method='highs')
    print(f"Status: {res.message}")
    print(f"x: {res.x}")
    print(f"Marginals (dual of balance): {res.eqlin.marginals}")

def test_minimize_sign():
    print("\nTesting minimize (trust-constr) sign...")
    def obj(x): return 1.0*x[0] + 1000.0*x[1]
    def jac(x): return np.array([1.0, 1000.0])
    A_eq = np.array([[1.0, 1.0]])
    lc = LinearConstraint(A_eq, 2.0, 2.0)
    res = minimize(obj, [0.0, 0.0], jac=jac, method='trust-constr', constraints=[lc], bounds=Bounds([0.0, 0.0], [1.0, 1.0]))
    print(f"Status: {res.message}")
    print(f"x: {res.x}")
    print(f"Duals (v): {res.v}")

if __name__ == "__main__":
    test_linprog_sign()
    test_minimize_sign()
