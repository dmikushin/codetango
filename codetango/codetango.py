"""
CodeTango Python Library

This module provides a Barrier class for synchronizing execution with another program
at barrier points and comparing state variables.
"""

import os
import json
import socket
from typing import Any, Dict, List, Union

class Barrier:
    """A class for synchronizing execution with another program at barrier points."""
    
    def __init__(self, program_id: str):
        """Initialize the Barrier.
        
        Args:
            program_id: A unique identifier for this program
        """
        self.program_id = program_id
        self.variables: Dict[str, Any] = {}
        self.socket = None
        self.connect()
    
    def connect(self) -> None:
        """Connect to the CodeTango control utility."""
        # Get the socket path from the environment
        socket_path = os.environ.get("CODETANGO_SOCKET")
        if not socket_path:
            raise RuntimeError("CODETANGO_SOCKET environment variable not set")
        
        # Create a socket
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        # Connect to the server
        try:
            self.socket.connect(socket_path)
        except socket.error as e:
            self.socket = None
            raise RuntimeError(f"Failed to connect to CodeTango: {e}")
        
        # Send the initialization message
        init_msg = {"program_id": self.program_id}
        try:
            self.socket.sendall(json.dumps(init_msg).encode('utf-8'))
        except socket.error as e:
            self.socket.close()
            self.socket = None
            raise RuntimeError(f"Failed to send init message: {e}")
    
    def wait(self, barrier_id: str) -> bool:
        """Wait at a barrier until both programs reach this point.
        
        Args:
            barrier_id: A unique identifier for this barrier point
            
        Returns:
            bool: True if the barrier was successfully synchronized
            
        Raises:
            RuntimeError: If not connected to CodeTango utility
        """
        if not self.socket:
            raise RuntimeError("Not connected to CodeTango utility")
        
        # Prepare the barrier message
        barrier_msg = {
            "barrier_id": barrier_id,
            "variables": self.variables
        }
        
        # Send the barrier message
        try:
            self.socket.sendall(json.dumps(barrier_msg).encode('utf-8'))
        except socket.error as e:
            print(f"Error sending barrier message: {e}")
            return False
        
        # Wait for the response
        try:
            response = self.socket.recv(4096)
            if not response:
                print("Connection closed by CodeTango utility")
                return False
            
            # Parse the response
            response_data = json.loads(response.decode('utf-8'))
            success = response_data.get("status") == "success"
            
            if not success and "message" in response_data:
                print(f"Barrier failed: {response_data['message']}")
            
            # Clear the variables after the barrier
            self.variables = {}
            
            return success
            
        except socket.error as e:
            print(f"Error receiving barrier response: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error parsing barrier response: {e}")
            return False
    
    def add_int(self, name: str, value: int) -> None:
        """Register an integer variable to be compared at the next barrier.
        
        Args:
            name: The name of the variable
            value: The value of the variable
        """
        self.variables[name] = value
    
    def add_float(self, name: str, value: float) -> None:
        """Register a float variable to be compared at the next barrier.
        
        Args:
            name: The name of the variable
            value: The value of the variable
        """
        self.variables[name] = value
    
    def add_str(self, name: str, value: str) -> None:
        """Register a string variable to be compared at the next barrier.
        
        Args:
            name: The name of the variable
            value: The value of the variable
        """
        self.variables[name] = value
    
    def add_bool(self, name: str, value: bool) -> None:
        """Register a boolean variable to be compared at the next barrier.
        
        Args:
            name: The name of the variable
            value: The value of the variable
        """
        self.variables[name] = value
    
    def add_list(self, name: str, value: List[Any]) -> None:
        """Register a list variable to be compared at the next barrier.
        
        Args:
            name: The name of the variable
            value: The value of the variable
        """
        self.variables[name] = value
    
    def add_dict(self, name: str, value: Dict[str, Any]) -> None:
        """Register a dictionary variable to be compared at the next barrier.
        
        Args:
            name: The name of the variable
            value: The value of the variable
        """
        self.variables[name] = value
    
    def add_variable(self, name: str, value: Any) -> None:
        """Register any variable to be compared at the next barrier.
        
        Args:
            name: The name of the variable
            value: The value of the variable
            
        Notes:
            The value must be JSON serializable.
        """
        self.variables[name] = value
    
    def __del__(self) -> None:
        """Close the socket connection when the object is garbage collected."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
