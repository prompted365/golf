#!/usr/bin/env python3
"""Interactive CLI for testing permission statements."""

import cmd
import json
import argparse

from permissions.playground.session import PlaygroundSession
from permissions.playground.completions import Completer


class PermissionShell(cmd.Cmd):
    """
    Interactive shell for testing permission statements.
    
    This class provides a command-line interface for experimenting
    with permission statements, seeing how they are tokenized, interpreted,
    and eventually translated into OPA inputs.
    """
    
    intro = """
Permission Statement Playground
==============================
Type permission statements to see how they are processed.
Type :help or ? to see available commands.
Type :exit or Ctrl-D to exit.
"""
    prompt = '> '
    
    def __init__(self):
        """Initialize the shell with a playground session."""
        super().__init__()
        self.session = PlaygroundSession()
        self.completer = Completer()
        
        # Register built-in commands
        self.commands = {
            "help": self.do_help,
            "exit": self.do_exit,
            "quit": self.do_exit,
            "fields": self.do_fields,
            "examples": self.do_examples,
            "tokens": self.do_tokens,
            "interpret": self.do_interpret,
            "statement": self.do_statement,
            "opa_input": self.do_opa_input,
        }
    
    def default(self, line: str) -> bool:
        """
        Process permission statements or handle custom commands.
        
        This method is called when the line is not recognized as a built-in command.
        It handles both custom commands (starting with :) and permission statements.
        
        Args:
            line: The permission statement or command
            
        Returns:
            bool: False to continue
        """
        # Check if this is a command (starts with : or .)
        if line.startswith(':'):
            cmd_name = line[1:].split()[0]
            args = line[1:].split()[1:] if len(line[1:].split()) > 1 else []
            
            if cmd_name in self.commands:
                return self.commands[cmd_name](' '.join(args))
            else:
                print(f"Unknown command: {cmd_name}")
                print("Type :help to see available commands.")
                return False
        
        # Process as a permission statement
        print("\nProcessing statement:", line)
        try:
            # Process the statement
            result = self.session.process_statement(line)
            
            # Show debug output
            if result.tokenization:
                print("Tokens:", result.tokenization.tokens)
                
            # Check if there was an error
            if result.error:
                print(f"Error: {result.error}")
                return False
                
            # Print success message
            print("\nStatement processed successfully.")
            statement = result.statement.statement
            print(f"Command: {statement.command.value}")
            print(f"Access: {', '.join([access.value for access in statement.access_types])}")
            print(f"Resource: {statement.resource_type.value}")
            
            if statement.conditions:
                print(f"Conditions: {len(statement.conditions)}")
                for i, condition in enumerate(statement.conditions, 1):
                    print(f"  {i}. {condition.field} {condition.operator.value} {condition.value}")
            else:
                print("No conditions.")
                
            # Display OPA input
            if result.opa_input:
                print("\nOPA Input:")
                print(json.dumps(result.opa_input.input, indent=2))
                
        except Exception as e:
            # Print detailed error
            import traceback
            print(f"Error processing statement: {str(e)}")
            traceback.print_exc()
            
        return False
    
    def do_exit(self, arg: str) -> bool:
        """
        Exit the shell.
        
        Args:
            arg: Command arguments (ignored)
            
        Returns:
            bool: True to exit
        """
        print("Exiting...")
        return True
    
    def do_help(self, arg: str) -> bool:
        """
        Display help information.
        
        Args:
            arg: Optional specific command name
            
        Returns:
            bool: False to continue
        """
        if arg:
            # Help for a specific command
            if arg in self.commands:
                print(self.commands[arg].__doc__ or "No help available.")
            else:
                print(f"Unknown command: {arg}")
        else:
            # General help
            print("""
Available commands:
  :help          Show this help message
  :exit          Exit the shell
  :fields TYPE   Show available fields for a resource type (e.g., :fields ISSUES)
  :examples      Show example permission statements
  :tokens        Show the tokens from the last processed statement
  :interpret     Show the interpreted data from the last processed statement
  :statement     Show the structured permission statement from the last processed statement
  :opa_input     Show the OPA input from the last processed statement

You can also type permission statements directly:
  GIVE READ ACCESS TO ISSUES TAGGED = urgent
  DENY WRITE ACCESS TO ISSUES ASSIGNED TO antoni
""")
        return False
    
    def do_fields(self, arg: str) -> bool:
        """
        Show available fields for a resource type.
        
        Args:
            arg: The resource type (e.g., "ISSUES")
            
        Returns:
            bool: False to continue
        """
        if not arg:
            print("Usage: :fields RESOURCE_TYPE")
            print("Available resource types:", ", ".join(self.completer.resource_types))
            return False
        
        fields = self.session.get_resource_fields(arg)
        if not fields:
            print(f"No fields found for resource type: {arg}")
            return False
        
        print(f"\nFields for {arg}:")
        for field_name, field_info in fields.items():
            # Skip metadata
            if field_name == "metadata":
                continue
            
            # Print field info with data type
            data_type = field_info.get("data_type", "unknown")
            description = field_info.get("description", "")
            print(f"  {field_name} ({data_type}): {description}")
        
        return False
    
    def do_examples(self, arg: str) -> bool:
        """
        Show example permission statements.
        
        Args:
            arg: Ignored
            
        Returns:
            bool: False to continue
        """
        examples = self.session.get_example_statements()
        
        print("\nExample permission statements:")
        for example in examples:
            print(f"  {example}")
        
        return False
    
    def do_tokens(self, arg: str) -> bool:
        """
        Show the tokens from the last processed statement.
        
        Args:
            arg: Ignored
            
        Returns:
            bool: False to continue
        """
        if not self.session.last_result or not self.session.last_result.tokenization:
            print("No tokens available. Process a statement first.")
            return False
        
        print("\nTokens:")
        print(self.session.last_result.tokenization.tokens)
        return False
    
    def do_interpret(self, arg: str) -> bool:
        """
        Show the interpreted data from the last processed statement.
        
        Args:
            arg: Ignored
            
        Returns:
            bool: False to continue
        """
        if not self.session.last_result or not self.session.last_result.interpretation:
            print("No interpreted data available. Process a statement first.")
            return False
        
        print("\nInterpreted Data:")
        print(json.dumps(self.session.last_result.interpretation.parsed_data, indent=2))
        return False
    
    def do_statement(self, arg: str) -> bool:
        """
        Show the structured permission statement from the last processed statement.
        
        Args:
            arg: Ignored
            
        Returns:
            bool: False to continue
        """
        if not self.session.last_result or not self.session.last_result.statement:
            print("No statement available. Process a statement first.")
            return False
        
        print("\nStructured Statement:")
        print(json.dumps(self.session.last_result.statement.json_representation, indent=2))
        return False
    
    def do_opa_input(self, arg: str) -> bool:
        """
        Show the OPA input from the last processed statement.
        
        Args:
            arg: Ignored
            
        Returns:
            bool: False to continue
        """
        if not self.session.last_result or not self.session.last_result.opa_input:
            print("No OPA input available. Process a statement first.")
            return False
        
        print("\nOPA Input:")
        print(json.dumps(self.session.last_result.opa_input.input, indent=2))
        return False
    
    def emptyline(self) -> bool:
        """
        Handle empty line input.
        
        Returns:
            bool: False to continue
        """
        return False
    
    def completedefault(self, text, line, begidx, endidx):
        """
        Provide tab completions for permission statements.
        
        This method is called by the cmd module when tab is pressed.
        It uses the Completer class to generate context-aware suggestions.
        
        Args:
            text: The text to complete
            line: The complete line
            begidx: The beginning index of the text
            endidx: The ending index of the text
            
        Returns:
            List[str]: Completion options
        """
        # Check if line starts with a command
        if line.startswith(':'):
            # Get command name
            cmd_name = line[1:].split()[0] if len(line) > 1 else ""
            
            # If we're still typing the command name, suggest command names
            if begidx <= len(cmd_name) + 1:
                return [cmd + " " for cmd in self.commands if cmd.startswith(text)]
            
            # For the :fields command, suggest resource types
            if cmd_name == "fields" and len(line.split()) <= 2:
                return [rt for rt in self.completer.resource_types if rt.startswith(text.upper())]
                
            return []
        
        # For permission statements, use the completer
        suggestions = self.completer.complete(line, endidx)
        
        # Filter suggestions by the text being completed
        return [s for s in suggestions if s.upper().startswith(text.upper())]
    
    def complete(self, text, state):
        """
        Return the next possible completion for 'text'.
        
        This overrides the default complete method to provide more control.
        
        Args:
            text: The text to complete
            state: The state of completion (0 for first match, 1 for second, etc.)
            
        Returns:
            str: The completion option or None if no more options
        """
        # If the default method works, use it
        try:
            matches = self.get_matches(text, self.line_buffer)
            if state < len(matches):
                return matches[state]
            else:
                return None
        except Exception as e:
            print(f"\nError in completion: {str(e)}")
            return None
            
    def get_matches(self, text, line):
        """
        Get all matches for the current text.
        
        Args:
            text: The text to complete
            line: The complete line
            
        Returns:
            List[str]: All matching completions
        """
        # Use readline for begidx/endidx
        import readline
        begidx = readline.get_begidx()
        endidx = readline.get_endidx()
        
        # Call the appropriate completion method
        if line.startswith(':'):
            return self.completedefault(text, line, begidx, endidx)
        
        # For permission statements
        suggestions = self.completer.complete(line, endidx)
        return [s for s in suggestions if s.upper().startswith(text.upper())]
    
    def do_EOF(self, arg: str) -> bool:
        """
        Handle Ctrl-D.
        
        Returns:
            bool: True to exit
        """
        print("\nExiting...")
        return True


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Interactive CLI for testing permission statements.')
    return parser.parse_args()


def start_cli():
    """Start the interactive CLI."""
    args = parse_args()
    shell = PermissionShell()
    shell.cmdloop()


if __name__ == '__main__':
    start_cli() 