#include "codetango.h"
#include <string>
#include <map>
#include <vector>
#include <iostream>
#include <sstream>
#include <iomanip>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <cstring>
#include <stdexcept>

using namespace codetango;

/**
 * Constructor
 * 
 * @param program_id A unique identifier for this program
 */
Barrier::Barrier(const std::string& program_id) : program_id_(program_id), connected_(false) {
    connect();
}

/**
 * Destructor - closes the socket connection
 */
Barrier::~Barrier() {
    if (connected_) {
        close(socket_fd_);
    }
}

/**
 * Wait at a barrier until both programs reach this point
 * 
 * @param barrier_id A unique identifier for this barrier point
 * @return true if the barrier was successfully synchronized
 */
bool Barrier::wait(const std::string& barrier_id) {
    if (!connected_) {
        throw std::runtime_error("Not connected to CodeTango utility");
    }
    
    // Prepare the JSON message
    std::string json = make_barrier_json(barrier_id);
    
    // Send the barrier message
    if (send(socket_fd_, json.c_str(), json.size(), 0) == -1) {
        std::cerr << "Error sending barrier message: " << strerror(errno) << std::endl;
        return false;
    }
    
    // Wait for the response
    char buffer[4096];
    ssize_t received = recv(socket_fd_, buffer, sizeof(buffer) - 1, 0);
    if (received <= 0) {
        std::cerr << "Error receiving barrier response: " 
                 << (received == 0 ? "Connection closed" : strerror(errno)) << std::endl;
        return false;
    }
    
    // Null-terminate the buffer
    buffer[received] = '\0';
    
    // Parse the response
    // For simplicity, we'll just check if it contains "success"
    std::string response(buffer);
    bool success = response.find("\"status\":\"success\"") != std::string::npos;
    
    // Clear the variables after the barrier
    variables_.clear();
    
    return success;
}

/**
 * Register an integer variable to be compared at the next barrier
 * 
 * @param name The name of the variable
 * @param value The value of the variable
 */
void Barrier::add_int(const std::string& name, int value) {
    std::stringstream ss;
    ss << value;
    variables_[name] = {"int", ss.str()};
}

/**
 * Register a double variable to be compared at the next barrier
 * 
 * @param name The name of the variable
 * @param value The value of the variable
 */
void Barrier::add_double(const std::string& name, double value) {
    std::stringstream ss;
    ss << value;
    variables_[name] = {"double", ss.str()};
}

/**
 * Register a string variable to be compared at the next barrier
 * 
 * @param name The name of the variable
 * @param value The value of the variable
 */
void Barrier::add_string(const std::string& name, const std::string& value) {
    variables_[name] = {"string", value};
}

/**
 * Register a boolean variable to be compared at the next barrier
 * 
 * @param name The name of the variable
 * @param value The value of the variable
 */
void Barrier::add_bool(const std::string& name, bool value) {
    variables_[name] = {"bool", value ? "true" : "false"};
}

/**
 * Register a vector of integers to be compared at the next barrier
 * 
 * @param name The name of the variable
 * @param values The vector of values
 */
void Barrier::add_int_vector(const std::string& name, const std::vector<int>& values) {
    std::stringstream ss;
    ss << "[";
    for (size_t i = 0; i < values.size(); ++i) {
        if (i > 0) ss << ",";
        ss << values[i];
    }
    ss << "]";
    variables_[name] = {"int_vector", ss.str()};
}

/**
 * Register a vector of doubles to be compared at the next barrier
 * 
 * @param name The name of the variable
 * @param values The vector of values
 */
void Barrier::add_double_vector(const std::string& name, const std::vector<double>& values) {
    std::stringstream ss;
    ss << "[";
    for (size_t i = 0; i < values.size(); ++i) {
        if (i > 0) ss << ",";
        ss << values[i];
    }
    ss << "]";
    variables_[name] = {"double_vector", ss.str()};
}

/**
 * Connect to the CodeTango control utility
 */
void Barrier::connect() {
    // Get the socket path from the environment
    const char* socket_path = getenv("CODETANGO_SOCKET");
    if (!socket_path) {
        throw std::runtime_error("CODETANGO_SOCKET environment variable not set");
    }
    
    // Create a socket
    socket_fd_ = socket(AF_UNIX, SOCK_STREAM, 0);
    if (socket_fd_ == -1) {
        throw std::runtime_error(std::string("Failed to create socket: ") + strerror(errno));
    }
    
    // Connect to the server
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, socket_path, sizeof(addr.sun_path) - 1);
    
    if (::connect(socket_fd_, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        close(socket_fd_);
        throw std::runtime_error(std::string("Failed to connect to CodeTango: ") + strerror(errno));
    }
    
    // Send the initialization message
    std::string init_json = "{\"program_id\":\"" + program_id_ + "\"}";
    if (send(socket_fd_, init_json.c_str(), init_json.size(), 0) == -1) {
        close(socket_fd_);
        throw std::runtime_error(std::string("Failed to send init message: ") + strerror(errno));
    }
    
    connected_ = true;
}

/**
 * Create a JSON message for a barrier
 * 
 * @param barrier_id The ID of the barrier
 * @return A JSON string representing the barrier message
 */
std::string Barrier::make_barrier_json(const std::string& barrier_id) {
    std::stringstream ss;
    ss << "{";
    ss << "\"barrier_id\":\"" << barrier_id << "\",";
    ss << "\"variables\":{";
    
    bool first = true;
    for (const auto& var : variables_) {
        if (!first) ss << ",";
        first = false;
        
        // Escape strings properly for JSON
        std::string escaped_name = escape_json_string(var.first);
        std::string type = var.second.first;
        std::string value = var.second.second;
        
        // For string types, we need to quote the value
        if (type == "string") {
            value = "\"" + escape_json_string(value) + "\"";
        }
        
        ss << "\"" << escaped_name << "\":" << value;
    }
    
    ss << "}}";
    return ss.str();
}

/**
 * Escape a string for JSON
 * 
 * @param str The string to escape
 * @return The escaped string
 */
std::string Barrier::escape_json_string(const std::string& str) {
    std::stringstream ss;
    for (char c : str) {
        switch (c) {
            case '\"': ss << "\\\""; break;
            case '\\': ss << "\\\\"; break;
            case '\b': ss << "\\b"; break;
            case '\f': ss << "\\f"; break;
            case '\n': ss << "\\n"; break;
            case '\r': ss << "\\r"; break;
            case '\t': ss << "\\t"; break;
            default:
                if ('\x00' <= c && c <= '\x1f') {
                    ss << "\\u" << std::hex << std::setw(4) << std::setfill('0') << (int)c;
                } else {
                    ss << c;
                }
        }
    }
    return ss.str();
}
