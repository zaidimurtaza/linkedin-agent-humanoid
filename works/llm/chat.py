import requests
import json
import base64
import time
from typing import Optional, List, Dict
from works.llm.context import get_llm_context, set_llm_context, save_llm_call

def chat_with_meta_llama(messages, step_name: str = "Unknown"):
    """
    Send messages to Meta-Llama and get the assistant's reply.
    
    messages: list of dicts, e.g.
        [
            {"role": "system", "content": "Be a helpful assistant"},
            {"role": "user", "content": "Hi"}
        ]
    step_name: Name of the step calling this function
    """
    url = "https://api.deepinfra.com/v1/openai/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "messages": messages,
        "stream": False,
        "response_format": {
        "type": "json_object"
    }
    }

    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload)
    time_taken = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        print(f"raw data: {json.dumps(data, indent=4   )}   ")
        
        # Extract assistant reply from response
        try:
            result = {
                "data": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", None)
            }
            
            # Add to context
            reasoning = data["choices"][0]["message"].get("reasoning_content", "")
            context_entry = f"""
Step: {step_name}
Input: {json.dumps(messages, indent=2)}
Reasoning: {reasoning}
Output: {json.dumps(result, indent=2)}
---
"""
            set_llm_context(get_llm_context() + context_entry)
            
            # Save to MongoDB
            save_llm_call(
                step_name=step_name,
                model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                input_data={"messages": messages},
                output_data=result,
                usage=data.get("usage"),
                time_taken=time_taken,
                is_image=False
            )
            
            return result
        except (KeyError, IndexError):
            return data  # fallback: return full response if format is different
    else:
        error_msg = f"Error {response.status_code}: {response.text}"
        context_entry = f"""
Step: {step_name}
Input: {json.dumps(messages, indent=2)}
Reasoning: N/A
Output: {error_msg}
---
"""
        set_llm_context(get_llm_context() + context_entry)
        
        # Save error to MongoDB
        save_llm_call(
            step_name=step_name,
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            input_data={"messages": messages},
            output_data={"error": error_msg},
            usage=None,
            time_taken=time_taken,
            is_image=False
        )
        
        return error_msg


def chat_with_image_model(prompt: str, step_name: str = "Unknown"):
    """
    Send messages to Flux-2-pro and get the assistant's reply.
    
    prompt: Image generation prompt
    step_name: Name of the step calling this function
    """
    url = "https://api.deepinfra.com/v1/openai/images/generations"
    headers = {"Content-Type": "application/json"}
    payload = {
            "prompt": prompt,
            "size": "1024x1024",
            "model": "black-forest-labs/FLUX-2-pro",
            "n": 1
            }

    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload)
    time_taken = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        
        # Extract base64
        b64_image = data["data"][0]["b64_json"]
        
        # Decode base64
        image_bytes = base64.b64decode(b64_image)
        
        # Write to file
        with open("generated_image.png", "wb") as f:
            f.write(image_bytes)
        
        print("Image saved successfully")
        
        # Add to context
        context_entry = f"""
Step: {step_name}
Input: {json.dumps({"prompt": prompt, "model": "black-forest-labs/FLUX-2-pro", "size": "1024x1024"}, indent=2)}
Reasoning: Image generation with prompt: {prompt}
Output: Image generated successfully and saved to generated_image.png
---
"""
        set_llm_context(get_llm_context() + context_entry)
        
        # Save to MongoDB (output_text is NULL for images)
        save_llm_call(
            step_name=step_name,
            model="black-forest-labs/FLUX-2-pro",
            input_data={"prompt": prompt, "size": "1024x1024"},
            output_data={"status": "success", "image_path": "generated_image.png"},
            usage=None,
            time_taken=time_taken,
            is_image=True
        )
        
        return {"status": "success", "image_path": "generated_image.png"}
    else:
        error_msg = f"Error {response.status_code}: {response.text}"
        context_entry = f"""
Step: {step_name}
Input: {json.dumps({"prompt": prompt, "model": "black-forest-labs/FLUX-2-pro", "size": "1024x1024"}, indent=2)}
Reasoning: Image generation failed
Output: {error_msg}
---
"""
        set_llm_context(get_llm_context() + context_entry)
        
        # Save error to MongoDB
        save_llm_call(
            step_name=step_name,
            model="black-forest-labs/FLUX-2-pro",
            input_data={"prompt": prompt, "size": "1024x1024"},
            output_data={"status": "error", "error": error_msg},
            usage=None,
            time_taken=time_taken,
            is_image=True
        )
        
        return {"status": "error", "error": error_msg}

def tool_caller_llm(tools: str, prompt: str, step_name: str = "Unknown"):
    """
    Send messages to Meta-Llama and get the assistant's reply.
    
    messages: list of dicts, e.g.
        [
            {"role": "system", "content": "Be a helpful assistant"},
            {"role": "user", "content": "Hi"}
        ]
    step_name: Name of the step calling this function
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant that can call tools to perform actions. concisely"},
        {"role": "user", "content": f" {prompt}"}
    ]
    url = "https://api.deepinfra.com/v1/openai/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "nvidia/Nemotron-3-Nano-30B-A3B",
        "messages": messages,
        "stream": False,
        "tools": tools,
        "tool_choice": "auto"
    }

    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload)
    time_taken = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        print(f"raw data: {json.dumps(data, indent=4   )}   ")
        # Extract assistant reply from response
        try:
            message = data["choices"][0]["message"]
            result = {
                "data": message.get("content", ""),
                "tool_calls": message.get("tool_calls", []),
                "usage": data.get("usage", None)
            }
            
            # Add to context
            reasoning = message.get("reasoning_content", "")
            # Format input for context (include prompt and tools summary)
            tools_summary = f"{len(tools)} tools available" if isinstance(tools, list) else "tools provided"
            input_data = {
                "prompt": prompt,
                "messages": messages,
                "tools": tools_summary
            }
            context_entry = f"""
Step: {step_name}
Input: {json.dumps(input_data, indent=2)}
Reasoning: {reasoning}
Output: {json.dumps(result, indent=2)}
---
"""
            set_llm_context(get_llm_context() + context_entry)
            
            # Save to MongoDB
            save_llm_call(
                step_name=step_name,
                model="nvidia/Nemotron-3-Nano-30B-A3B",
                input_data=input_data,
                output_data=result,
                usage=data.get("usage"),
                time_taken=time_taken,
                is_image=False
            )
            
            return result
        except (KeyError, IndexError):
            return data  # fallback: return full response if format is different
    else:
        error_msg = f"Error {response.status_code}: {response.text}"
        tools_summary = f"{len(tools)} tools available" if isinstance(tools, list) else "tools provided"
        input_data = {
            "prompt": prompt,
            "messages": messages,
            "tools": tools_summary
        }
        context_entry = f"""
Step: {step_name}
Input: {json.dumps(input_data, indent=2)}
Reasoning: N/A
Output: {error_msg}
---
"""
        set_llm_context(get_llm_context() + context_entry)
        
        # Save error to MongoDB
        save_llm_call(
            step_name=step_name,
            model="nvidia/Nemotron-3-Nano-30B-A3B",
            input_data=input_data,
            output_data={"error": error_msg},
            usage=None,
            time_taken=time_taken,
            is_image=False
        )
        
        return error_msg


if __name__ == "__main__":
    tools = [
    {
        "type": "function",
        "function": {
            "name": "chat_with_image_model",
            "description": "Generates an image from a text prompt for LinkedIn post",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The text prompt to generate the image from"
                    }
                },
                "required": ["prompt"]
            }
        }
    }
]
    messages = [
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
            "url": "https://m.media-amazon.com/images/I/51OzKuZk0iL._SY741_.jpg"
          } 
        },
        {
          "type": "text",
          "text": f"""Generate an image for a LinkedIn post about the product. 
For performing any action, you have tools: {tools}. 
Your output should be in the format of messages, which is a list of dicts, e.g.:
JUST THIS FORMAT exactly:
messages = [
    {{"role": "system", "content": "abut the toll nd nrrd"}},
    {{"role": "user", "content": "call the tool <> and get the result"}}
]

Explicitly tell me the tool you want to use and the arguments you want to pass to the tool."""

        }
      ]
    }
  ]
    
    


    reply = chat_with_meta_llama(messages)

    print("=" * 50)
    print(reply)
    print("=" * 50)
    call_tool_reply = tool_caller_llm(tools=tools, prompt=reply["data"])
    print("=" * 50)
    print(call_tool_reply)
    print("=" * 50)
    
    # Check if tool_calls exist and execute them
    # if isinstance(call_tool_reply, dict) and call_tool_reply.get("tool_calls"):
    #     for tool_call in call_tool_reply["tool_calls"]:
    #         if tool_call.get("function", {}).get("name") == "chat_with_image_model":
    #             args = json.loads(tool_call["function"]["arguments"])
    #             prompt = args.get("prompt")
    #             print(f"Executing tool: chat_with_image_model with prompt: {prompt}")
    #             image_result = chat_with_image_model(prompt=prompt)
    #             print("=" * 50)
    #             print(f"Image generation completed!")
    #             print("=" * 50)
    # reply = chat_with_image_model(prompt="A photo of an astronaut riding a horse on Mars.")
    # print(reply)