from email.parser import BytesParser
import os
import json
from pathlib import Path
import threading
from openai import OpenAI
from dotenv import load_dotenv
from jsonschema import validate, ValidationError
from email import policy
from config import EMAIL_FOLDER
from get_email import get_contacts
from pdf import html_to_pdf
from send_email import generate_msg, send_msg
from display_email import preview_email_html
from typing import Dict, Any
from extensions import socketio
from sockets import pending
import uuid
import time

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
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Absolute server file path (e.g. uploads/file.pdf for user uploads or documents/file.pdf for generated documents)",
                            },
                            "filename": {
                                "type": "string",
                                "description": "Informative display name of the file to be used in the email."
                            }
                        },
                        "required": ["filepath", "filename"],
                        "additionalProperties": False
                    },
                    "description": "List of attachments with file path and filename. Use empty array if none."
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
                },
                "recipients": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "email"
                    },
                    "description": "All recipients of the email.",
                }
            },
            "required": ["msg_id","recipients"],
            "additionalProperties": False
        }
    }
}

TOOL_GET_CONTACTS = {
    "type": "function",
    "function": {
        "name": "get_contacts",
        "description": "Searches through contacts with a query returning n matches.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query used to search for matches in contact list."
                },
                "n": {
                    "type": "number",
                    "minimum": 5,
                    "description": "The number of matching contacts returned."
                }
            },
            "required": ["query","n"],
            "additionalProperties": False
        }
    }
}

TOOL_CREATE_PDF = {
    "type": "function",
    "function": {
        "name": "create_pdf",
        "description": "Creates a PDF file from an HTML string and saves it using the provided filename.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "html_str": {
                    "type": "string",
                    "description": "The HTML content to render into the PDF."
                },
                "filename": {
                    "type": "string",
                    "description": "The output PDF filename including the .pdf extension."
                }
            },
            "required": ["html_str", "filename"],
            "additionalProperties": False
        }
    }
}

def exec_create_pdf(args: Dict[str, Any]) -> Dict[str, Any]:
    return html_to_pdf(**args)

def exec_get_contacts(args: Dict[str, Any]) -> Dict[str, Any]:
    return get_contacts(**args)

def exec_generate_email(args: Dict[str, Any]) -> Dict[str, Any]:
    msg, recipients = generate_msg(**args)
    if len(recipients):
        msg_id = str(uuid.uuid4())
        with open(f'{EMAIL_FOLDER}/{msg_id}.eml', 'wb') as f:
            f.write(msg.as_bytes())
        
        return {
            "recipients": recipients,
            "response": "Email message generated and displayed for user.",
            "msg_id": msg_id
        }

def exec_send_msg(args: Dict[str, Any]) -> Dict[str, Any]:
    if "msg_id" not in args and "recipieints" not in args:
        return {"error": "No msg_id specified."}
    msg_id = args["msg_id"]
    recipients = args["recipients"]
    if Path(f"{EMAIL_FOLDER}/{msg_id}.eml").is_file():
        with open(f'{EMAIL_FOLDER}/{msg_id}.eml', 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)
        request_id = str(uuid.uuid4())
        event = threading.Event()
        pending[request_id] = {"event": event, "answer": None}
        socketio.emit("show_popup", {
            "message": f"Do you want to send the email?",
            "requestId": request_id
        })
        preview_email_html(msg)
        event.wait()
        if pending[request_id]["answer"] == "yes":
            send_msg(msg, recipients)
            return {"response": "Email sent."}
        else:
            return {"response": "User denied email send request."}
    else:
        return {"error": "Unknown msg_id given."}

TOOLS = [TOOL_GENERATE_EMAIL, TOOL_SEND_EMAIL, TOOL_GET_CONTACTS, TOOL_CREATE_PDF]

# Map tool names to their executors
TOOL_EXECUTORS = {
    "generate_email": exec_generate_email,
    "send_email": exec_send_msg,
    "get_contacts": exec_get_contacts,
    "create_pdf": exec_create_pdf
}

# Map tool names to their parameter schemas (for validation)
TOOL_SCHEMAS = {
    "generate_email": TOOL_GENERATE_EMAIL["function"]["parameters"],
    "send_email": TOOL_SEND_EMAIL["function"]["parameters"],
    "get_contacts": TOOL_GET_CONTACTS["function"]["parameters"],
    "create_pdf": TOOL_CREATE_PDF["function"]["parameters"],
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

def execute_tool(tool_name: str, args: Dict[str, Any], client: OpenAI, model: str) -> Dict[str, Any]:
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
    
    if tool_name == "get_contacts":
        args['client'] = client
        args['model'] = model

    executor = TOOL_EXECUTORS[tool_name]
    return executor(args)

def run_agent(client: OpenAI, messages: Dict[str, Any], goal: str, model: str = "gpt-4o-mini") -> str:
    """
    Run a multi-turn agent controller to accomplish a goal.
    
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
    start = time.time()
    # Turn 1: Let the model pick a tool
    print("\n[Turn 1] Sending goal to model...")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    print("Response Time:",time.time()-start)

    for i in range(5):
        assistant_message = response.choices[0].message
        messages.append(assistant_message.model_dump())
        if response.usage is not None:
            print(f"Prompt Tokens: {response.usage.prompt_tokens}")
            print(f"Completion Tokens: {response.usage.completion_tokens}")
            print(f"Total Tokens: {response.usage.total_tokens}")
        # Check if the model wants to call tools
        if not assistant_message.tool_calls:
            # No tool calls, model answered directly
            print(f"[Turn {i+1}] Model answered without tools")
            return assistant_message.content or "No response generated"
        
        # Process each tool call
        tool_results = []
        for tool_call in assistant_message.tool_calls:
            start = time.time()
            tool_name = tool_call.function.name
            
            try:
                tool_args = json.loads(tool_call.function.arguments)  
            except json.JSONDecodeError as e:
                print(f"Unable to parse tool arguments for {tool_name}.\n{e}")
                continue
            
            print(f"\n[Turn {i+1}] Tool call: {tool_name}")
            print(f"         Arguments: {tool_args}")
            
            try:
                result = execute_tool(tool_name, tool_args, client, model)
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
        print(f"{tool_name}: {time.time()-start}")
        messages.extend(tool_results)

        print(f"\n[Turn {i+2}] Sending tool results to model...")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )
        
    final_message = response.choices[0].message
    messages.append(final_message.model_dump())

    if final_message.tool_calls:
        # For this simple controller, we don't do more than 2 turns
        # In production, you'd loop until done or hit a budget
        print("Model took too many tries.")
    
    final_answer = final_message.content or "No final answer generated"
    
    print(f"\n{'='*60}")
    print("FINAL ANSWER:")
    print(f"{'='*60}")
    print(final_answer)
    
    return final_answer

def run_agent_wrapper(client: OpenAI, messages: Dict[str, Any], goal: str, model: str = "gpt-4o-mini"):
    result = run_agent(client, messages, goal)
    socketio.emit("bot-reply", {
        "reply": result
    })