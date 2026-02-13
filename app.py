from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from groq import Groq
import json
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Groq client
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Tool definitions
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Use this tool for any mathematical calculation. Input must be a valid mathematical expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A valid mathematical expression to evaluate (e.g., '245 * 678', 'sqrt(144)', '12 / 3 + 7')"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Use this tool when the user asks about weather in a specific city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city to get weather for"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_data",
            "description": "Analyze numerical data and calculate statistics like mean, median, mode, min, max, and standard deviation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numbers": {
                        "type": "string",
                        "description": "Comma-separated list of numbers to analyze (e.g., '10, 20, 30, 40, 50')"
                    }
                },
                "required": ["numbers"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_password",
            "description": "Generate a secure random password with specified length and character types.",
            "parameters": {
                "type": "object",
                "properties": {
                    "length": {
                        "type": "integer",
                        "description": "Length of the password (default: 12)"
                    },
                    "include_symbols": {
                        "type": "boolean",
                        "description": "Include special symbols (default: true)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_email",
            "description": "Validate if an email address has correct format and check domain validity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email address to validate"
                    }
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convert amount between different currencies (USD, EUR, INR, GBP).",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Amount to convert"
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code (USD, EUR, INR, GBP)"
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency code (USD, EUR, INR, GBP)"
                    }
                },
                "required": ["amount", "from_currency", "to_currency"]
            }
        }
    }
]

# System prompt
SYSTEM_PROMPT = """You are a helpful AI assistant with access to external tools.

Your job is to:
1. Answer user questions directly when possible.
2. Call a tool ONLY if it is necessary to produce an accurate answer.

You have access to the following tools:

1. calculator - Mathematical calculations
   - Use for any math operations
   - Examples: "245 * 678", "sqrt(144)", "sin(pi/2)"

2. get_weather - Weather information
   - Use when user asks about weather in a city
   - Example: city: "Chennai"

3. analyze_data - Statistical data analysis
   - Use to analyze lists of numbers
   - Calculates mean, median, mode, min, max, std dev
   - Example: numbers: "10, 20, 30, 40, 50"

4. generate_password - Secure password generation
   - Use when user wants a random password
   - Parameters: length (8-64), include_symbols (true/false)
   - Example: length: 16, include_symbols: true

5. validate_email - Email validation
   - Use to check if email format is valid
   - Example: email: "user@example.com"

6. convert_currency - Currency conversion
   - Use to convert between USD, EUR, INR, GBP, JPY, AUD, CAD
   - Example: amount: 100, from_currency: "USD", to_currency: "INR"

Rules:
- Do NOT guess math answers. Always use the calculator tool.
- Do NOT guess weather information. Always use the weather tool.
- Do NOT make up statistics. Use analyze_data for number analysis.
- Do NOT create passwords manually. Use generate_password tool.
- Use appropriate tools for their specific purposes.
- If no tool is needed, respond normally.
- Be accurate and concise."""

def calculator(expression):
    """Execute mathematical calculations safely"""
    try:
        # Import math for advanced functions
        import math
        
        # Create a safe namespace with math functions
        safe_dict = {
            'sqrt': math.sqrt,
            'pow': math.pow,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e
        }
        
        # Evaluate the expression
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return {"result": result, "expression": expression}
    except Exception as e:
        return {"error": f"Error evaluating expression: {str(e)}"}

def get_weather(city):
    """Get weather information for a city (mock data)"""
    # Mock weather data for demonstration
    weather_data = {
        "chennai": {"temperature": "32°C", "condition": "Sunny", "humidity": "65%"},
        "mumbai": {"temperature": "28°C", "condition": "Partly Cloudy", "humidity": "75%"},
        "delhi": {"temperature": "25°C", "condition": "Clear", "humidity": "45%"},
        "bangalore": {"temperature": "24°C", "condition": "Pleasant", "humidity": "60%"},
        "hyderabad": {"temperature": "30°C", "condition": "Sunny", "humidity": "55%"}
    }
    
    city_lower = city.lower()
    if city_lower in weather_data:
        data = weather_data[city_lower]
        return {
            "city": city,
            "temperature": data["temperature"],
            "condition": data["condition"],
            "humidity": data["humidity"]
        }
    else:
        # Return generic data for unknown cities
        return {
            "city": city,
            "temperature": "26°C",
            "condition": "Partly Cloudy",
            "humidity": "60%"
        }

def analyze_data(numbers):
    """Analyze numerical data and calculate statistics"""
    try:
        # Parse comma-separated numbers
        num_list = [float(x.strip()) for x in numbers.split(',')]
        
        if not num_list:
            return {"error": "No valid numbers provided"}
        
        # Calculate statistics
        import statistics
        
        result = {
            "count": len(num_list),
            "sum": sum(num_list),
            "mean": round(statistics.mean(num_list), 2),
            "median": round(statistics.median(num_list), 2),
            "min": min(num_list),
            "max": max(num_list),
            "range": round(max(num_list) - min(num_list), 2)
        }
        
        # Add mode if it exists
        try:
            result["mode"] = round(statistics.mode(num_list), 2)
        except statistics.StatisticsError:
            result["mode"] = "No unique mode"
        
        # Add standard deviation if more than one number
        if len(num_list) > 1:
            result["std_dev"] = round(statistics.stdev(num_list), 2)
        
        return result
    except Exception as e:
        return {"error": f"Error analyzing data: {str(e)}"}

def generate_password(length=12, include_symbols=True):
    """Generate a secure random password"""
    try:
        import random
        import string
        
        # Ensure minimum length
        length = max(8, min(length, 64))
        
        # Character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?" if include_symbols else ""
        
        # Build character pool
        all_chars = lowercase + uppercase + digits + symbols
        
        # Ensure at least one of each type
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits)
        ]
        
        if include_symbols:
            password.append(random.choice(symbols))
        
        # Fill remaining length
        remaining_length = length - len(password)
        password.extend(random.choice(all_chars) for _ in range(remaining_length))
        
        # Shuffle to avoid predictable patterns
        random.shuffle(password)
        
        return {
            "password": ''.join(password),
            "length": length,
            "strength": "Strong" if length >= 12 and include_symbols else "Medium"
        }
    except Exception as e:
        return {"error": f"Error generating password: {str(e)}"}

def validate_email(email):
    """Validate email address format and domain"""
    try:
        import re
        
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        is_valid = bool(re.match(pattern, email))
        
        result = {
            "email": email,
            "is_valid": is_valid
        }
        
        if is_valid:
            # Extract domain
            domain = email.split('@')[1]
            result["domain"] = domain
            result["message"] = "Email format is valid"
            
            # Check common domains
            common_domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"]
            result["is_common_provider"] = domain.lower() in common_domains
        else:
            result["message"] = "Invalid email format"
            result["suggestions"] = [
                "Ensure email has @ symbol",
                "Check for valid domain (e.g., example.com)",
                "Avoid spaces and special characters"
            ]
        
        return result
    except Exception as e:
        return {"error": f"Error validating email: {str(e)}"}

def convert_currency(amount, from_currency, to_currency):
    """Convert between currencies using exchange rates"""
    try:
        # Exchange rates relative to USD (as of example data)
        rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "INR": 83.12,
            "JPY": 149.50,
            "AUD": 1.52,
            "CAD": 1.36
        }
        
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency not in rates:
            return {"error": f"Unsupported currency: {from_currency}"}
        
        if to_currency not in rates:
            return {"error": f"Unsupported currency: {to_currency}"}
        
        # Convert to USD first, then to target currency
        usd_amount = amount / rates[from_currency]
        converted_amount = usd_amount * rates[to_currency]
        
        return {
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": round(converted_amount, 2),
            "exchange_rate": round(rates[to_currency] / rates[from_currency], 4),
            "note": "Exchange rates are approximate and for demonstration purposes"
        }
    except Exception as e:
        return {"error": f"Error converting currency: {str(e)}"}


def execute_tool(tool_name, tool_args):
    """Execute the requested tool"""
    if tool_name == "calculator":
        return calculator(tool_args.get("expression", ""))
    elif tool_name == "get_weather":
        return get_weather(tool_args.get("city", ""))
    elif tool_name == "analyze_data":
        return analyze_data(tool_args.get("numbers", ""))
    elif tool_name == "generate_password":
        return generate_password(
            tool_args.get("length", 12),
            tool_args.get("include_symbols", True)
        )
    elif tool_name == "validate_email":
        return validate_email(tool_args.get("email", ""))
    elif tool_name == "convert_currency":
        return convert_currency(
            tool_args.get("amount", 0),
            tool_args.get("from_currency", "USD"),
            tool_args.get("to_currency", "INR")
        )
    else:
        return {"error": f"Unknown tool: {tool_name}"}

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Create messages for the AI
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        # First AI call - decide if tools are needed
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.1
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        # If no tool calls, return the direct response
        if not tool_calls:
            return jsonify({
                "response": response_message.content,
                "tool_used": None
            })
        
        # Execute tool calls
        messages.append(response_message)
        
        tool_results = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Execute the tool
            tool_result = execute_tool(function_name, function_args)
            tool_results.append({
                "name": function_name,
                "arguments": function_args,
                "result": tool_result
            })
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(tool_result)
            })
        
        # Get final response from AI with tool results
        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.1
        )
        
        return jsonify({
            "response": final_response.choices[0].message.content,
            "tool_used": tool_results[0] if tool_results else None
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
