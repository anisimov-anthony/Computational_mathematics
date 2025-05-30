import numpy as np
import matplotlib.pyplot as plt

def system(vars, eps):
    x, y_val, a1, a2 = vars
    dxdt = x * (2*a1 - 0.5*x - (a1**2)/(a2**2)*y_val)
    dydt = y_val * (2*a2 - (a2**2)/(a1**2)*x - 0.5*y_val)
    da1dt = eps * (2 - 2*a1*y_val/(a2**2))
    da2dt = eps * (2 - 2*a2*x/(a1**2))
    return np.array([dxdt, dydt, da1dt, da2dt])

def jacobian_system(vars, eps):
    x, y_val, a1, a2 = vars
    J = np.zeros((4, 4))
    
    # Для x*(2*a1 - 0.5*x - (a1**2)/(a2**2)*y)
    J[0, 0] = 2*a1 - x - (a1**2)/(a2**2)*y_val                 # d/dx
    J[0, 1] = - x*(a1**2)/(a2**2)                                # d/dy
    J[0, 2] = x * (2 - (2*a1*y_val)/(a2**2))                     # d/da1
    J[0, 3] = 2*x*(a1**2)*y_val/(a2**3)                          # d/da2

    # Для y*(2*a2 - (a2**2)/(a1**2)*x - 0.5*y)
    J[1, 0] = - y_val*(a2**2)/(a1**2)                        
    J[1, 1] = 2*a2 - (a2**2)/(a1**2)*x - y_val                  
    J[1, 2] = y_val*(2*x*(a2**2)/(a1**3))                       
    J[1, 3] = y_val*(2 - (2*a2*x)/(a1**2))                     

    # Для eps*(2 - 2*a1*y/(a2**2))
    J[2, 0] = 0                                               
    J[2, 1] = -eps*(2*a1)/(a2**2)                              
    J[2, 2] = -eps*(2*y_val)/(a2**2)                            
    J[2, 3] = eps*(4*a1*y_val)/(a2**3)                         

    # Для eps*(2 - 2*a2*x/(a1**2))
    J[3, 0] = -eps*(2*a2)/(a1**2)                             
    J[3, 1] = 0                                               
    J[3, 2] = eps*(4*a2*x)/(a1**3)                            
    J[3, 3] = -eps*(2*x)/(a1**2)                             
    
    return J

# Коэффициенты метода Radau IIA (см. Методичку Бауманки 255 стр.)
a11, a12 = 5/12, -1/12
a21, a22 = 3/4, 1/4
b1, b2 = 3/4, 1/4
c1, c2 = 1/3, 1.0

# Функция одного шага неявного метода Radau IIA
def imp_rung3(y_n, h, eps, tol=1e-8, max_iter=20):

    z = np.concatenate([y_n, y_n]) 
    for iteration in range(max_iter):
        Y1 = z[0:4]
        Y2 = z[4:8]
        fY1 = system(Y1, eps)
        fY2 = system(Y2, eps)

        F1 = Y1 - y_n - h*(a11*fY1 + a12*fY2)
        F2 = Y2 - y_n - h*(a21*fY1 + a22*fY2)
        F = np.concatenate([F1, F2])
        normF = np.linalg.norm(F)
        if normF < tol:
            break

        Jf_Y1 = jacobian_system(Y1, eps)
        Jf_Y2 = jacobian_system(Y2, eps)
        I = np.eye(4)

        J_top_left = I - h*a11*Jf_Y1
        J_top_right = - h*a12*Jf_Y2
        J_bottom_left = - h*a21*Jf_Y1
        J_bottom_right = I - h*a22*Jf_Y2
        J_full = np.block([[J_top_left, J_top_right],
                           [J_bottom_left, J_bottom_right]])

        delta = np.linalg.solve(J_full, -F)
        z = z + delta
    else:
        print("Warning: Newton method did not converge within the maximum iterations")
    
    Y1 = z[0:4]
    Y2 = z[4:8]
    y_np1 = y_n + h*(b1*system(Y1, eps) + b2*system(Y2, eps))
    return y_np1

def imp_rung4(y_n, h, eps, tol=1e-8, max_iter=20):
    c1 = 0.5 - np.sqrt(3) / 6
    c2 = 0.5 + np.sqrt(3) / 6
    a11 = 0.25
    a12 = 0.25 - np.sqrt(3) / 6
    a21 = 0.25 + np.sqrt(3) / 6
    a22 = 0.25
    b1 = 0.5
    b2 = 0.5

    k1 = system(y_n, eps)
    k2 = system(y_n, eps)

    for _ in range(max_iter):
        Y1 = y_n + h * (a11 * k1 + a12 * k2)
        Y2 = y_n + h * (a21 * k1 + a22 * k2)

        F1 = k1 - system(Y1, eps)
        F2 = k2 - system(Y2, eps)
        F = np.concatenate([F1, F2])

        if np.linalg.norm(F) < tol:
            break

        J11 = np.eye(4) - h * a11 * jacobian_system(Y1, eps)
        J12 = -h * a12 * jacobian_system(Y1, eps)
        J21 = -h * a21 * jacobian_system(Y2, eps)
        J22 = np.eye(4) - h * a22 * jacobian_system(Y2, eps)
        J = np.block([[J11, J12], [J21, J22]])

        delta = np.linalg.solve(J, -F)
        k1 += delta[:4]
        k2 += delta[4:]
    else:
        print("Warning: Newton method did not converge within the maximum iterations")

    y_next = y_n + h * (b1 * k1 + b2 * k2)
    return y_next

def solver(nach_usl, T, h, eps, method='radau'):
    N = int(T / h)
    t = np.linspace(0, T, N + 1)
    sol = np.zeros((N + 1, len(nach_usl)))
    sol[0] = nach_usl
    y_current = nach_usl.copy()

    for i in range(N):
        if method == 'imp_rung_3':
            y_next = imp_rung3(y_current, h, eps)
        elif method == 'imp_rung_4':
            y_next = imp_rung4(y_current, h, eps)
        else:
            raise ValueError("Unknown method")
        
        sol[i + 1] = y_next
        y_current = y_next
        if i % 100 == 0:
            print(f"Step {i}/{N}")

    return t, sol


eps = 0.001
nach_usl = np.array([10.0, 10.0, 0.4, 10.0])
T = 100
h = 0.001  


t_irk3, sol_irk3 = solver(nach_usl, T, h, eps, method='imp_rung_3')
t_irk4, sol_irk4 = solver(nach_usl, T, h, eps, method='imp_rung_4')


plt.figure(figsize=(12, 8))
plt.suptitle("imp_rung_3")

plt.subplot(2, 2, 1)
plt.plot(t_irk3, sol_irk3[:, 0], 'b-')
plt.xlabel("t")
plt.ylabel("x")
plt.title("x(t)")

plt.subplot(2, 2, 2)
plt.plot(t_irk3, sol_irk3[:, 1], 'r-')
plt.xlabel("t")
plt.ylabel("y")
plt.title("y(t)")

plt.subplot(2, 2, 3)
plt.plot(t_irk3, sol_irk3[:, 2], 'g-')
plt.xlabel("t")
plt.ylabel("a1")
plt.title("a1(t)")

plt.subplot(2, 2, 4)
plt.plot(t_irk3, sol_irk3[:, 3], 'm-')
plt.xlabel("t")
plt.ylabel("a2")
plt.title("a2(t)")

plt.tight_layout()
plt.savefig("imp_rung_3.png")

###

plt.figure(figsize=(12, 8))
plt.suptitle("imp_rung_4")

plt.subplot(2, 2, 1)
plt.plot(t_irk4, sol_irk4[:, 0], 'b-')
plt.xlabel("t")
plt.ylabel("x")
plt.title("x(t)")

plt.subplot(2, 2, 2)
plt.plot(t_irk4, sol_irk4[:, 1], 'r-')
plt.xlabel("t")
plt.ylabel("y")
plt.title("y(t)")

plt.subplot(2, 2, 3)
plt.plot(t_irk4, sol_irk4[:, 2], 'g-')
plt.xlabel("t")
plt.ylabel("a1")
plt.title("a1(t)")

plt.subplot(2, 2, 4)
plt.plot(t_irk4, sol_irk4[:, 3], 'm-')
plt.xlabel("t")
plt.ylabel("a2")
plt.title("a2(t)")

plt.tight_layout()
plt.savefig("imp_rung_4.png")