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
            "suggest": self.do_suggest,
            "options": self.do_suggest,
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
        # Strip any leading or trailing whitespace
        line = line.strip()
        
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
  :suggest       Show available options at the current context
  :options       Same as :suggest - shows what you can type next

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
        try:
            # Get the buffer from readline directly
            import readline
            line = readline.get_line_buffer()
            begidx = readline.get_begidx()
            endidx = readline.get_endidx()
            
            # Handle different types of completions
            if line.startswith(':'):
                # Command completions
                matches = self.completedefault(text, line, begidx, endidx)
            else:
                # Permission statement completions
                suggestions = self.completer.complete(line, endidx)
                matches = [s for s in suggestions if s.upper().startswith(text.upper())]
            
            # Return the match based on state
            if state < len(matches):
                return matches[state]
            return None
            
        except Exception as e:
            print(f"\nError in completion: {str(e)}")
            return None
            
    def do_EOF(self, arg: str) -> bool:
        """
        Handle Ctrl-D.
        
        Returns:
            bool: True to exit
        """
        print("\nExiting...")
        return True
    
    def do_suggest(self, arg: str) -> bool:
        """
        Show available options for the current context.
        
        Args:
            arg: Optional context to show suggestions for (e.g., "command", "access", "resource")
            
        Returns:
            bool: False to continue
        """
        context = arg.strip() if arg else ""
        
        if not context:
            print("\nAvailable Options:")
            print("\nCommands:")
            for cmd in sorted(self.commands.keys()):
                print(f"  :{cmd}")
                
            print("\nStatement Components:")
            print("  Commands: " + ", ".join(sorted(self.completer.base_commands)))
            print("  Access Types: " + ", ".join(sorted(self.completer.access_types)))
            print("  Resource Types: " + ", ".join(sorted(self.completer.resource_types)))
            print("  Structural Helpers: " + ", ".join(sorted(self.completer.structural_helpers)))
            print("  Operators: " + ", ".join(sorted(self.completer.condition_operators)))
            
            print("\nExample Syntax:")
            print("  GIVE/DENY + ACCESS_TYPE + ACCESS TO + RESOURCE_TYPE + [CONDITIONS]")
            print("  GIVE READ ACCESS TO ISSUES WITH status = Done")
            print("  DENY WRITE ACCESS TO EMAILS TAGGED = personal")
            
            return False
            
        # Show context-specific options
        context = context.upper()
        if context == "COMMAND" or context == "COMMANDS":
            print("\nAvailable Commands:")
            print(", ".join(sorted(self.completer.base_commands)))
            
        elif context == "ACCESS" or context == "ACCESS_TYPES":
            print("\nAvailable Access Types:")
            print(", ".join(sorted(self.completer.access_types)))
            
        elif context == "RESOURCE" or context == "RESOURCES":
            print("\nAvailable Resource Types:")
            print(", ".join(sorted(self.completer.resource_types)))
            
        elif context == "HELPER" or context == "HELPERS":
            print("\nAvailable Structural Helpers:")
            print(", ".join(sorted(self.completer.structural_helpers)))
            
        elif context == "OPERATOR" or context == "OPERATORS":
            print("\nAvailable Operators:")
            print(", ".join(sorted(self.completer.condition_operators)))
            
        elif context in self.completer.resource_types:
            # Show fields for this resource type
            self.do_fields(context.lower())
            
        return False


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