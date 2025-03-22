#!/usr/bin/env python3
"""
CodeTango - A utility to run two programs in sync and check state equality at barriers.

This utility launches two programs, synchronizes them at barrier points, and validates
that they have matching state variables at each barrier.
"""

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

# Socket path for communication
SOCKET_PATH = "/tmp/codetango.sock"

# Import the Barrier class from codetango.py
from .codetango import Barrier

@dataclass
class ProgramInfo:
    """Information about a running program."""
    process: subprocess.Popen
    program_id: str
    connection: Optional[socket.socket] = None
    barrier_data: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        self.barrier_data = {}

class CodeTango:
    """Main control utility for synchronizing programs at barrier points."""
    
    def __init__(self, program1_cmd: List[str], program2_cmd: List[str],
                 timeout: int = 60, verbose: bool = False):
        """Initialize the CodeTango utility.
        
        Args:
            program1_cmd: Command to launch the first program
            program2_cmd: Command to launch the second program
            timeout: Timeout in seconds for waiting at barriers
            verbose: Whether to print verbose output
        """
        self.program1_cmd = program1_cmd
        self.program2_cmd = program2_cmd
        self.timeout = timeout
        self.verbose = verbose
        
        # Programs keyed by their ID
        self.programs: Dict[str, ProgramInfo] = {}
        
        # Barriers that have been reached by each program
        self.barriers: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Barrier order for validation
        self.barrier_sequence = []
        
        # Set up socket server
        self.server = None
        self.setup_socket()
        
    def setup_socket(self) -> None:
        """Set up the Unix domain socket for communication."""
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
            
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(SOCKET_PATH)
        self.server.listen(2)  # Accept up to 2 connections
        
        if self.verbose:
            print(f"Socket server listening at {SOCKET_PATH}")
        
    def launch_programs(self) -> None:
        """Launch both programs with the necessary environment."""
        env = os.environ.copy()
        env["CODETANGO_SOCKET"] = SOCKET_PATH
        
        # Start first program
        program1 = subprocess.Popen(
            self.program1_cmd,
            env=env,
            stdout=subprocess.PIPE if not self.verbose else None,
            stderr=subprocess.PIPE if not self.verbose else None,
            text=True
        )
        self.programs["program1"] = ProgramInfo(process=program1, program_id="program1")
        
        # Start second program
        program2 = subprocess.Popen(
            self.program2_cmd,
            env=env,
            stdout=subprocess.PIPE if not self.verbose else None,
            stderr=subprocess.PIPE if not self.verbose else None,
            text=True
        )
        self.programs["program2"] = ProgramInfo(process=program2, program_id="program2")
        
        if self.verbose:
            print(f"Launched program 1: {' '.join(self.program1_cmd)}")
            print(f"Launched program 2: {' '.join(self.program2_cmd)}")
    
    def accept_connections(self) -> None:
        """Accept connections from the launched programs."""
        self.server.settimeout(self.timeout)
        
        # Accept 2 connections
        for _ in range(2):
            try:
                conn, addr = self.server.accept()
                
                # Get the program ID
                data = conn.recv(1024)
                if not data:
                    print("Error: Empty connection data")
                    continue
                    
                init_msg = json.loads(data.decode('utf-8'))
                program_id = init_msg["program_id"]
                
                # Store the connection with the program info
                if program_id in self.programs:
                    self.programs[program_id].connection = conn
                    if self.verbose:
                        print(f"Connection established with {program_id}")
                else:
                    print(f"Warning: Unknown program ID: {program_id}")
                    conn.close()
                    
            except socket.timeout:
                print(f"Timeout waiting for program connections after {self.timeout} seconds")
                self.cleanup()
                sys.exit(1)
    
    def handle_barrier(self, program_id: str, conn: socket.socket) -> None:
        """Handle barrier messages from programs.
        
        Args:
            program_id: The ID of the program sending the barrier message
            conn: The socket connection to the program
        """
        while True:
            try:
                # Set a timeout to check if process is still alive
                conn.settimeout(1.0)
                
                # Check if process is still running
                if self.programs[program_id].process.poll() is not None:
                    if self.verbose:
                        print(f"{program_id} has terminated")
                    break
                
                # Receive barrier message
                data = conn.recv(4096)
                if not data:
                    # Connection closed
                    break
                
                # Parse the barrier message
                message = json.loads(data.decode('utf-8'))
                barrier_id = message["barrier_id"]
                variables = message["variables"]
                
                with self.lock:
                    if self.verbose:
                        print(f"{program_id} reached barrier '{barrier_id}'")
                    
                    # Add to barrier sequence (for first program only)
                    if program_id == "program1" and barrier_id not in self.barrier_sequence:
                        self.barrier_sequence.append(barrier_id)
                    
                    # Create barrier entry if it doesn't exist
                    if barrier_id not in self.barriers:
                        self.barriers[barrier_id] = {}
                    
                    # Store variables for this program at this barrier
                    self.barriers[barrier_id][program_id] = variables
                    
                    # Check if both programs have reached this barrier
                    if len(self.barriers[barrier_id]) == 2:
                        # Both programs have reached this barrier
                        self.compare_variables(barrier_id)
                        
                        # Allow both programs to continue
                        self.release_programs(barrier_id)
                    
            except socket.timeout:
                # This is just a timeout for the socket recv, continue
                continue
            except json.JSONDecodeError as e:
                print(f"Error decoding message from {program_id}: {e}")
                # Send error and allow continue
                self.send_result(program_id, False, f"Invalid message format: {e}")
            except Exception as e:
                print(f"Error handling barrier for {program_id}: {e}")
                self.send_result(program_id, False, f"Internal error: {e}")
    
    def compare_variables(self, barrier_id: str) -> bool:
        """Compare variables between programs at a specific barrier.
        
        Args:
            barrier_id: The ID of the barrier to compare
            
        Returns:
            bool: True if all variables match, False otherwise
        """
        program1_vars = self.barriers[barrier_id]["program1"]
        program2_vars = self.barriers[barrier_id]["program2"]
        
        # Check for missing or different variables
        all_keys = set(program1_vars.keys()) | set(program2_vars.keys())
        differences = []
        
        for key in all_keys:
            if key not in program1_vars:
                differences.append(f"Variable '{key}' exists in program2 but not in program1")
            elif key not in program2_vars:
                differences.append(f"Variable '{key}' exists in program1 but not in program2")
            elif program1_vars[key] != program2_vars[key]:
                differences.append(
                    f"Variable '{key}' differs:\n"
                    f"  program1: {program1_vars[key]}\n"
                    f"  program2: {program2_vars[key]}"
                )
        
        # Report differences
        if differences:
            print(f"\nDifferences detected at barrier '{barrier_id}':")
            for diff in differences:
                print(f"  - {diff}")
            return False
        else:
            if self.verbose:
                print(f"All variables match at barrier '{barrier_id}'")
            return True
    
    def release_programs(self, barrier_id: str) -> None:
        """Release programs waiting at a barrier.
        
        Args:
            barrier_id: The ID of the barrier
        """
        matched = self.compare_variables(barrier_id)
        
        # Send result to both programs
        if matched:
            result_msg = {"status": "success", "message": "Variables match"}
        else:
            result_msg = {"status": "failure", "message": "Variables differ"}
            
        for program_id, program in self.programs.items():
            if program.connection:
                try:
                    program.connection.sendall(json.dumps(result_msg).encode('utf-8'))
                except Exception as e:
                    print(f"Error sending result to {program_id}: {e}")
    
    def send_result(self, program_id: str, success: bool, message: str) -> None:
        """Send a result message to a specific program.
        
        Args:
            program_id: The ID of the program
            success: Whether the operation was successful
            message: A message describing the result
        """
        result_msg = {"status": "success" if success else "failure", "message": message}
        try:
            if self.programs[program_id].connection:
                self.programs[program_id].connection.sendall(json.dumps(result_msg).encode('utf-8'))
        except Exception as e:
            print(f"Error sending result to {program_id}: {e}")
    
    def run(self) -> bool:
        """Run the CodeTango utility.
        
        Returns:
            bool: True if all barriers were passed, False otherwise
        """
        try:
            # Launch programs
            self.launch_programs()
            
            # Accept connections
            self.accept_connections()
            
            # Create threads for each program
            threads = []
            for program_id, program in self.programs.items():
                if program.connection:
                    thread = threading.Thread(
                        target=self.handle_barrier,
                        args=(program_id, program.connection)
                    )
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
            
            # Wait for both programs to complete
            exit_codes = []
            for program_id, program in self.programs.items():
                exit_code = program.process.wait()
                exit_codes.append(exit_code)
                if self.verbose:
                    print(f"{program_id} exited with code {exit_code}")
            
            # Check exit codes
            if any(code != 0 for code in exit_codes):
                print("Warning: One or more programs exited with non-zero status")
            
            # Print final barrier sequence
            print(f"\nBarrier sequence: {' -> '.join(self.barrier_sequence)}")
            
            # Check if all barriers were passed
            all_passed = True
            for barrier_id in self.barrier_sequence:
                if len(self.barriers[barrier_id]) != 2:
                    print(f"Warning: Barrier '{barrier_id}' was not reached by both programs")
                    all_passed = False
            
            if all_passed:
                print("\nAll barriers passed successfully!")
            else:
                print("\nSome barriers failed or were not reached by both programs.")
            
            return all_passed
            
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.cleanup()
        
        return False
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        # Close socket connections
        for program_id, program in self.programs.items():
            if program.connection:
                try:
                    program.connection.close()
                except:
                    pass
        
        # Close socket server
        if self.server:
            try:
                self.server.close()
            except:
                pass
        
        # Remove socket file
        if os.path.exists(SOCKET_PATH):
            try:
                os.unlink(SOCKET_PATH)
            except:
                pass
        
        # Terminate any running processes
        for program_id, program in self.programs.items():
            if program.process.poll() is None:
                try:
                    program.process.terminate()
                    # Wait a bit for graceful termination
                    time.sleep(0.5)
                    if program.process.poll() is None:
                        program.process.kill()
                except:
                    pass

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CodeTango - Run two programs in sync and check state equality at barriers"
    )
    parser.add_argument(
        "program1", 
        nargs="+", 
        help="Command to run the first program (e.g. './my_program arg1 arg2')"
    )
    parser.add_argument(
        "program2", 
        nargs="+", 
        help="Command to run the second program (e.g. 'python3 other_program.py')"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=60,
        help="Timeout in seconds for waiting at barriers (default: 60)"
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true",
        help="Print verbose output"
    )
    
    args = parser.parse_args()
    
    # Split the commands
    codetango = CodeTango(
        program1_cmd=args.program1,
        program2_cmd=args.program2,
        timeout=args.timeout,
        verbose=args.verbose
    )
    
    success = codetango.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
