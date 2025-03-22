#ifndef CODETANGO_H
#define CODETANGO_H

#include <string>
#include <map>
#include <vector>
#include <iostream>
#include <sstream>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <cstring>
#include <stdexcept>

namespace codetango {

/**
 * A class for synchronizing execution with another program at barrier points.
 */
class Barrier {
public:
    /**
     * Constructor
     * 
     * @param program_id A unique identifier for this program
     */
    Barrier(const std::string& program_id);
    
    /**
     * Destructor - closes the socket connection
     */
    ~Barrier();
    
    /**
     * Wait at a barrier until both programs reach this point
     * 
     * @param barrier_id A unique identifier for this barrier point
     * @return true if the barrier was successfully synchronized
     */
    bool wait(const std::string& barrier_id);
    
    /**
     * Register an integer variable to be compared at the next barrier
     * 
     * @param name The name of the variable
     * @param value The value of the variable
     */
    void add_int(const std::string& name, int value);
    
    /**
     * Register a double variable to be compared at the next barrier
     * 
     * @param name The name of the variable
     * @param value The value of the variable
     */
    void add_double(const std::string& name, double value);
    
    /**
     * Register a string variable to be compared at the next barrier
     * 
     * @param name The name of the variable
     * @param value The value of the variable
     */
    void add_string(const std::string& name, const std::string& value);
    
    /**
     * Register a boolean variable to be compared at the next barrier
     * 
     * @param name The name of the variable
     * @param value The value of the variable
     */
    void add_bool(const std::string& name, bool value);
    
    /**
     * Register a vector of integers to be compared at the next barrier
     * 
     * @param name The name of the variable
     * @param values The vector of values
     */
    void add_int_vector(const std::string& name, const std::vector<int>& values);
    
    /**
     * Register a vector of doubles to be compared at the next barrier
     * 
     * @param name The name of the variable
     * @param values The vector of values
     */
    void add_double_vector(const std::string& name, const std::vector<double>& values);
    
private:
    // Program ID for this instance
    std::string program_id_;
    
    // Socket connection
    int socket_fd_;
    bool connected_;
    
    // Variables to be compared at the next barrier
    std::map<std::string, std::pair<std::string, std::string>> variables_;
    
    /**
     * Connect to the CodeTango control utility
     */
    void connect();
    
    /**
     * Create a JSON message for a barrier
     * 
     * @param barrier_id The ID of the barrier
     * @return A JSON string representing the barrier message
     */
    std::string make_barrier_json(const std::string& barrier_id);
    
    /**
     * Escape a string for JSON
     * 
     * @param str The string to escape
     * @return The escaped string
     */
    std::string escape_json_string(const std::string& str);
};

} // namespace codetango

#endif // CODETANGO_H
