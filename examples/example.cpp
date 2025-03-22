#include "codetango.h"
#include <iostream>
#include <vector>
#include <cmath>

// A simple implementation of a quadratic equation solver
std::vector<double> solve_quadratic(double a, double b, double c) {
    // Calculate the discriminant
    double discriminant = b * b - 4 * a * c;
    
    codetango::Barrier barrier("program1");
    
    // Checkpoint 1: Initial values
    barrier.add_double("a", a);
    barrier.add_double("b", b);
    barrier.add_double("c", c);
    barrier.add_double("discriminant", discriminant);
    barrier.wait("init");
    
    std::vector<double> solutions;
    
    if (discriminant < 0) {
        // No real solutions
        
        // Checkpoint 2: No solutions case
        barrier.add_bool("has_solutions", false);
        barrier.add_int("num_solutions", 0);
        barrier.wait("check_discriminant");
        
        return solutions;
    }
    
    if (discriminant == 0) {
        // One real solution
        double x = -b / (2 * a);
        solutions.push_back(x);
        
        // Checkpoint 3: One solution case
        barrier.add_bool("has_solutions", true);
        barrier.add_int("num_solutions", 1);
        barrier.add_double("x1", x);
        barrier.wait("check_discriminant");
    } else {
        // Two real solutions
        double sqrt_discriminant = std::sqrt(discriminant);
        double x1 = (-b + sqrt_discriminant) / (2 * a);
        double x2 = (-b - sqrt_discriminant) / (2 * a);
        solutions.push_back(x1);
        solutions.push_back(x2);
        
        // Checkpoint 4: Two solutions case
        barrier.add_bool("has_solutions", true);
        barrier.add_int("num_solutions", 2);
        barrier.add_double("sqrt_discriminant", sqrt_discriminant);
        barrier.add_double("x1", x1);
        barrier.add_double("x2", x2);
        barrier.wait("check_discriminant");
    }
    
    // Final checkpoint
    barrier.add_int_vector("solutions", std::vector<int>(solutions.begin(), solutions.end()));
    barrier.add_int("solutions_count", solutions.size());
    barrier.wait("final");
    
    return solutions;
}

int main(int argc, char** argv) {
    // Get coefficients from command line or use defaults
    double a = (argc > 1) ? std::stod(argv[1]) : 1.0;
    double b = (argc > 2) ? std::stod(argv[2]) : -3.0;
    double c = (argc > 3) ? std::stod(argv[3]) : 2.0;
    
    std::cout << "Solving " << a << "x^2 + " << b << "x + " << c << " = 0" << std::endl;
    
    std::vector<double> solutions = solve_quadratic(a, b, c);
    
    // Print the solutions
    if (solutions.empty()) {
        std::cout << "No real solutions." << std::endl;
    } else {
        std::cout << "Solutions: ";
        for (size_t i = 0; i < solutions.size(); ++i) {
            if (i > 0) std::cout << ", ";
            std::cout << solutions[i];
        }
        std::cout << std::endl;
    }
    
    return 0;
}
