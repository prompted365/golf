#!/usr/bin/env python3
"""Interactive CLI for testing permission statements with live suggestions."""

import json
import argparse
from typing import Dict, Any

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer as PTCompleter, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import is_searching
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from core.playground.session import PlaygroundSession
from core.playground.completions import Completer


class LiveCompleter(PTCompleter):
    """
    Live completer for permission statements using prompt_toolkit.
    
    This class provides real-time suggestions as the user types.
    """
    
    def __init__(self, completer: Completer, commands: Dict[str, Any]):
        """
        Initialize the live completer.
        
        Args:
            completer: The permission statement completer
            commands: Dictionary of available commands
        """
        self.completer = completer
        self.commands = commands
    
    def get_completions(self, document, complete_event):
        """
        Get completions for the current document.
        
        Args:
            document: The document being edited
            complete_event: The completion event
            
        Yields:
            Completion: Completion suggestions
        """
        text = document.text
        cursor_position = document.cursor_position
        
        # Check if this is a command
        if text.startswith(':'):
            cmd_parts = text[1:].split()
            cmd = cmd_parts[0] if cmd_parts else ""
            
            # If we're typing a command name
            if len(cmd_parts) <= 1 and not text.endswith(' '):
                for command in self.commands:
                    if command.startswith(cmd):
                        yield Completion(
                            command, 
                            start_position=-len(cmd),
                            display_meta="Command"
                        )
            
            # Suggest arguments for specific commands
            elif len(cmd_parts) > 0 and text.endswith(' '):
                if cmd == "fields" or cmd == "suggest":
                    for rt in self.completer.resource_types:
                        yield Completion(
                            rt,
                            start_position=0,
                            display_meta="Resource Type"
                        )
                elif cmd == "suggest" or cmd == "options":
                    for context in ["command", "access", "resource", "helper", "operator"]:
                        yield Completion(
                            context,
                            start_position=0,
                            display_meta="Context"
                        )
            
        # For permission statements
        else:
            # Special case: If the text ends with "ACCESS TO " suggest resource types
            if text.upper().endswith("ACCESS TO "):
                for rt in self.completer.resource_types:
                    yield Completion(
                        rt,
                        start_position=0,
                        display_meta="Resource Type"
                    )
                return
                
            # Get suggestions from the completer
            suggestions = self.completer.complete(text, cursor_position)
            
            # If text ends with a space, suggest the next element
            if text.endswith(' '):
                # Try to determine context based on tokens so far
                words = text.strip().split()
                
                # After "GIVE" or "DENY", suggest access types
                if len(words) == 1 and words[0].upper() in self.completer.base_commands:
                    for access_type in self.completer.access_types:
                        yield Completion(
                            access_type,
                            start_position=0,
                            display_meta="Access Type"
                        )
                # After a resource type, suggest structural helpers
                elif len(words) >= 2 and words[-1].upper() in self.completer.resource_types:
                    for helper in self.completer.structural_helpers:
                        yield Completion(
                            helper,
                            start_position=0,
                            display_meta="Structural Helper"
                        )
                # After "WITH", suggest fields for the resource
                elif len(words) >= 3 and words[-1].upper() == "WITH" and words[-2].upper() in self.completer.resource_types:
                    resource_type = words[-2].upper()
                    fields = self.completer._get_fields_for_resource(resource_type)
                    for field in sorted(fields):
                        yield Completion(
                            field,
                            start_position=0,
                            display_meta=f"Field ({resource_type})"
                        )
                # After other structural helpers like TAGGED, suggest "="
                elif len(words) >= 3 and words[-1].upper() in self.completer.structural_helpers:
                    yield Completion(
                        "=",
                        start_position=0,
                        display_meta="Operator"
                    )
                # After a field name, suggest operators
                elif len(words) >= 4 and words[-2].upper() in self.completer.structural_helpers:
                    for op in ["=", "IS", "IS NOT", "CONTAINS"]:
                        yield Completion(
                            op,
                            start_position=0,
                            display_meta="Operator"
                        )
                    
                return
            
            # Get current word
            if text and cursor_position > 0:
                current_word = ""
                i = cursor_position - 1
                while i >= 0 and text[i].isalnum():
                    current_word = text[i] + current_word
                    i -= 1
                
                for suggestion in suggestions:
                    if suggestion.upper().startswith(current_word.upper()):
                        display_meta = self._get_category(suggestion)
                        yield Completion(
                            suggestion, 
                            start_position=-len(current_word),
                            display_meta=display_meta
                        )
    
    def _get_category(self, suggestion: str) -> str:
        """
        Get the category of a suggestion for display purposes.
        
        Args:
            suggestion: The suggestion text
            
        Returns:
            str: The category name
        """
        if suggestion in self.completer.base_commands:
            return "Command"
        elif suggestion in self.completer.access_types:
            return "Access Type"
        elif suggestion in self.completer.resource_types:
            return "Resource Type"
        elif suggestion in self.completer.structural_helpers:
            return "Structural Helper"
        elif suggestion in self.completer.condition_operators:
            return "Operator"
        return ""


class PermissionCLI:
    """
    Interactive CLI for testing permission statements with live suggestions.
    
    This class provides a command-line interface for experimenting
    with permission statements, seeing how they are tokenized, interpreted,
    and eventually translated into OPA inputs.
    """
    
    def __init__(self):
        """Initialize the CLI with a playground session."""
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
        
        # Create prompt session with live completion
        self.history = InMemoryHistory()
        
        # Create key bindings
        kb = KeyBindings()
        
        # Add keybinding for Tab to show completions
        @kb.add('tab')
        def _(event):
            # Force completions to show
            event.app.current_buffer.start_completion(select_first=False)
        
        # Define styles
        style = Style.from_dict({
            'completion-menu.completion': 'bg:#008888 #ffffff',
            'completion-menu.completion.current': 'bg:#00aaaa #000000',
            'completion-menu.meta.completion': 'bg:#44aaff #ffffff',
            'completion-menu.meta.completion.current': 'bg:#00aaaa #000000',
        })
        
        # Configure prompt_toolkit with more aggressive settings
        self.prompt_session = PromptSession(
            completer=LiveCompleter(self.completer, self.commands),
            history=self.history,
            complete_while_typing=True,
            complete_in_thread=False,  # Disable threading to ensure completions appear
            enable_history_search=True,
            key_bindings=kb,
            style=style,
            complete_style='MULTI_COLUMN',  # Show completions in columns
            auto_suggest=None,  # Disable auto-suggest which can interfere
            mouse_support=True,  # Enable mouse support
            bottom_toolbar=HTML('<b>Press TAB for completions</b>'),
        )
    
    def process_line(self, line: str) -> bool:
        """
        Process a line of input from the user.
        
        Args:
            line: The input line
            
        Returns:
            bool: True to exit, False to continue
        """
        # Strip any leading or trailing whitespace
        line = line.strip()
        
        # Skip empty lines
        if not line:
            return False
        
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
    
    def run(self):
        """Run the CLI."""
        print("""
Permission Statement Playground
==============================
Type permission statements to see how they are processed.
Type :help or ? to see available commands.
Type :exit or Ctrl-D to exit.

Suggestions appear as you type! Press TAB to force completion menu.
""")

        # Main command loop
        try:
            # Try using the prompt_toolkit interface
            while True:
                try:
                    # Get input with live completion
                    line = self.prompt_session.prompt('> ')
                    
                    # Process input - if it returns True, exit
                    if self.process_line(line):
                        break
                        
                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    print("\nOperation interrupted.")
                    continue
                except EOFError:
                    # Handle Ctrl+D
                    print("\nExiting...")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    continue
        except Exception as e:
            # If prompt_toolkit fails, fall back to basic input mode
            print(f"\nAdvanced completion mode failed: {e}")
            print("Falling back to basic input mode (no completions).")
            print("Type :suggest to see available options.")
            
            # Basic input loop
            while True:
                try:
                    line = input('> ')
                    if self.process_line(line):
                        break
                except KeyboardInterrupt:
                    print("\nOperation interrupted.")
                    continue
                except EOFError:
                    print("\nExiting...")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    continue
    
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

TIP: As you type, suggestions will appear automatically!
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
    cli = PermissionCLI()
    cli.run()


if __name__ == '__main__':
    start_cli() 