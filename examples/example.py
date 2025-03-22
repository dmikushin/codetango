#!/usr/bin/env python3
"""
Example of using CodeTango in Python to solve a quadratic equation.
"""

import sys
import math
from codetango import Barrier

def solve_quadratic(a, b, c):
    """Solve a quadratic equation and demonstrate barrier synchronization.
    
    Args:
        a: coefficient of x^2
        b: coefficient of x
        c: constant term
        
    Returns:
        list: The solutions to the equation
    """
    # Calculate the discriminant
    discriminant = b * b - 4 * a * c
    
    # Create a barrier
    barrier = Barrier("program2")
    
    # Checkpoint 1: Initial values
    barrier.add_float("a", a)
    barrier.add_float("b", b)
    barrier.add_float("c", c)
    barrier.add_float("discriminant", discriminant)
    barrier.wait("init")
    
    solutions = []
    
    if discriminant < 0:
        # No real solutions
        
        # Checkpoint 2: No solutions case
        barrier.add_bool("has_solutions", False)
        barrier.add_int("num_solutions", 0)
        barrier.wait("check_discriminant")
        
        return solutions
        
    if discriminant == 0:
        # One real solution
        x = -b / (2 * a)
        solutions.append(x)
        
        # Checkpoint 3: One solution case
        barrier.add_bool("has_solutions", True)
        barrier.add_int("num_solutions", 1)
        barrier.add_float("x1", x)
        barrier.wait("check_discriminant")
    else:
        # Two real solutions
        sqrt_discriminant = math.sqrt(discriminant)
        x1 = (-b + sqrt_discriminant) / (2 * a)
        x2 = (-b - sqrt_discriminant) / (2 * a)
        solutions.append(x1)
        solutions.append(x2)
        
        # Checkpoint 4: Two solutions case
        barrier.add_bool("has_solutions", True)
        barrier.add_int("num_solutions", 2)
        barrier.add_float("sqrt_discriminant", sqrt_discriminant)
        barrier.add_float("x1", x1)
        barrier.add_float("x2", x2)
        barrier.wait("check_discriminant")
    
    # Final checkpoint
    barrier.add_list("solutions", solutions)
    barrier.add_int("solutions_count", len(solutions))
    barrier.wait("final")
    
    return solutions

def main():
    """Main entry point."""
    # Get coefficients from command line or use defaults
    a = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    b = float(sys.argv[2]) if len(sys.argv) > 2 else -3.0
    c = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    
    print(f"Solving {a}x^2 + {b}x + {c} = 0")
    
    solutions = solve_quadratic(a, b, c)
    
    # Print the solutions
    if not solutions:
        print("No real solutions.")
    else:
        print(f"Solutions: {', '.join(str(s) for s in solutions)}")

if __name__ == "__main__":
    main()
