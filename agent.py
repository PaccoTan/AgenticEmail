import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from jsonschema import validate, ValidationError
from send_email import generate_msg, send_msg
from typing import Dict, Any

load_dotenv()

def get_openai_client() -> OpenAI:
    """
    Create and return an OpenAI client using API key from environment.
    
    Returns:
        Configured OpenAI client instance.
        
    Raises:
        EnvironmentError: If OPENAI_API_KEY is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not found in environment variables")
    return OpenAI(api_key=api_key)

TOOL_GENERATE_EMAIL = {
    "type": "function",
    "function": {
        "name": "generate_email",
        "description": "Create an email message. User can include attachments or specify CC and BCC."
                       "Returns a valid email message ready to be sent."
                       "Displays a simple preivew of the message.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "email"
                    },
                    "description": "Primary recipients of the email."
                },
                "subject": {
                    "type": "string",
                    "description": "Subject line of the email."
                },
                "body": {
                    "type": "string",
                    "description": "Body content of the email in markdown."
                },
                "cc": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "email"
                    },
                    "description": "CC recipients. Use empty array if none.",
                },
                "bcc": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "email"
                    },
                    "description": "BCC recipients. Use empty array if none.",
                },
                "attachments": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "File paths or identifiers for attachments. Use empty array if none.",
                }
                },
            "required": ["to", "subject", "body", "cc", "bcc", "attachments"],
            "additionalProperties": False
        }
    }
}

TOOL_SEND_EMAIL = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": "Sends email with the corresponding msg_id.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "msg_id": {
                    "type": "string",
                    "description": "Message id of the message to be transmitted."
                }
            },
            "required": ["msg_id"],
            "additionalProperties": False
        }
    }
}

def exec_generate_email(args: Dict[str, Any]) -> Dict[str, Any]:
    msg, recipients = generate_msg(**args)   

def exec_send_msg(args: Dict[str, Any]) -> Dict[str, Any]:
    print(args)

TOOLS = [TOOL_GENERATE_EMAIL, TOOL_SEND_EMAIL]

# Map tool names to their executors
TOOL_EXECUTORS = {
    "generate_email": exec_generate_email,
    "send_email": exec_send_msg
}

# Map tool names to their parameter schemas (for validation)
TOOL_SCHEMAS = {
    "generate_email": TOOL_GENERATE_EMAIL["function"]["parameters"],
    "send_email": TOOL_SEND_EMAIL["function"]["parameters"]
}

def validate_tool_args(tool_name: str, args: Dict[str, Any]) -> None:
    """
    Validate tool arguments against the tool's JSON Schema.
    
    Args:
        tool_name: Name of the tool.
        args: Arguments to validate.
        
    Raises:
        ValidationError: If arguments don't match the schema.
        KeyError: If tool name is not recognized.
    """
    if tool_name not in TOOL_SCHEMAS:
        raise KeyError(f"Unknown tool: {tool_name}")
    
    schema = TOOL_SCHEMAS[tool_name]
    validate(instance=args, schema=schema)

def execute_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and execute a tool.
    
    Args:
        tool_name: Name of the tool to execute.
        args: Arguments for the tool.
        
    Returns:
        Tool execution result as a dictionary.
        
    Raises:
        ValidationError: If arguments are invalid.
        KeyError: If tool is not recognized.
    """
    # Validate arguments before execution (DO NOT REMOVE)
    validate_tool_args(tool_name, args)
    
    # Get and execute the tool
    if tool_name not in TOOL_EXECUTORS:
        raise KeyError(f"No executor found for tool: {tool_name}")
    
    executor = TOOL_EXECUTORS[tool_name]
    return executor(args)

def run_agent(client: OpenAI, messages: Dict[str, Any], goal: str, model: str = "gpt-4o-mini") -> str:
    """
    Run a two-turn agent controller to accomplish a goal.
    
    Turn 1: Send goal to model, let it pick a tool and supply arguments.
    Turn 2: Execute tool, send result back, get final answer.
    
    Args:
        client: OpenAI client instance.
        goal: The user's goal or question.
        model: Chat model to use.
        
    Returns:
        The final answer from the model.
    """
    print(f"\n{'='*60}")
    print(f"GOAL: {messages[-1]["content"]}")
    print(f"{'='*60}")
    
    # Turn 1: Let the model pick a tool
    print("\n[Turn 1] Sending goal to model...")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    
    assistant_message = response.choices[0].message
    messages.append(assistant_message.model_dump())
    
    # Check if the model wants to call tools
    if not assistant_message.tool_calls:
        # No tool calls, model answered directly
        print("[Turn 1] Model answered without tools")
        return assistant_message.content or "No response generated"
    
    # Process each tool call
    tool_results = []
    for tool_call in assistant_message.tool_calls:
        tool_name = tool_call.function.name
        
        try:
            tool_args = json.loads(tool_call.function.arguments)  
        except json.JSONDecodeError as e:
            print(f"Unable to parse tool arguments for {tool_name}.\n{e}")
            continue
        
        print(f"\n[Turn 1] Tool call: {tool_name}")
        print(f"         Arguments: {tool_args}")
        
        try:
            result = execute_tool(tool_name, tool_args)
            print(f"         Result: {result}")
            tool_results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": json.dumps(result)
            })
        except ValidationError as e:
            print(f"[Error] Validation failed: {e.message}")
            tool_results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": json.dumps({"error": f"Validation failed: {e.message}"})
            })
        except Exception as e:
            print(f"[Error] Tool execution failed: {e}")
            tool_results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": json.dumps({"error": str(e)})
            })
    
    # Add tool results to messages
    messages.extend(tool_results)
    
    # Turn 2: Send tool results back and get final answer
    print("\n[Turn 2] Sending tool results to model...")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    final_message = response.choices[0].message
    messages.append(final_message.model_dump())
    # Handle case where model wants more tool calls (simplified: just take content)
    if final_message.tool_calls:
        # For this simple controller, we don't do more than 2 turns
        # In production, you'd loop until done or hit a budget
        print("[Turn 2] Model requested more tools (not supported in this simple controller)")
    
    final_answer = final_message.content or "No final answer generated"
    
    print(f"\n{'='*60}")
    print("FINAL ANSWER:")
    print(f"{'='*60}")
    print(final_answer)
    
    return final_answer