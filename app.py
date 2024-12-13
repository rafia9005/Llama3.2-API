import os
import time
import secrets
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from groq import Groq
from flask_cors import CORS
from flasgger import Swagger  

load_dotenv(dotenv_path='.env')

app = Flask(__name__)
CORS(app)

client = Groq(
    api_key=os.environ.get('GROQ_TOKEN'),
)

swagger = Swagger(app)

database = {}

def get_uptime():
    uptime = time.time() - os.path.getmtime('/proc/1')
    return time.strftime("%H:%M:%S", time.gmtime(uptime))


def get_server_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))


def check_groq_status():
    try:
        client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "system", "content": "ping"}],
            temperature=0.5,
            max_tokens=1,
            top_p=1,
            stream=False,
            stop=None,
        )
        return {"status": "llama3-8b-8192 is responsive", "status_class": "ok"}
    except Exception as e:
        return {"status": f"Error with Groq API: {str(e)}", "status_class": "error"}


@app.route('/', methods=['GET'])
def health():
    """
    Health check for the application
    ---
    responses:
        200:
            description: Application is healthy
            schema:
                type: object
                properties:
                    status:
                        type: string
                        example: OK
                    uptime:
                        type: string
                        example: "00:10:30"
                    groq_status:
                        type: string
                        example: "llama3-8b-8192 is responsive"
                    server_time:
                        type: string
                        example: "2024-12-13 10:30:00"
                    message:
                        type: string
                        example: "All systems are operational."
        500:
            description: Internal Server Error
            schema:
                type: object
                properties:
                    error:
                        type: string
                        example: "Error message"
    """
    try:
        uptime = get_uptime()
        groq_status = check_groq_status()

        return jsonify({
            'status': 'OK',
            'uptime': uptime,
            'groq_status': groq_status['status'],
            'server_time': get_server_time(),
            'message': 'All systems are operational.',
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/create/model', methods=['POST'])
def create_model():
    """
    Create a new model with a system message
    ---
    parameters:
      - name: system_message
        in: body
        required: true
        type: string
        description: The system message for the model
    responses:
        201:
            description: Model created successfully
            schema:
                type: object
                properties:
                    token:
                        type: string
                        example: "5f4e2b7f19d147e58d3a14d68e736820"
                    message:
                        type: string
                        example: "Model created successfully"
        400:
            description: System message is required
            schema:
                type: object
                properties:
                    error:
                        type: string
                        example: "System message is required"
        500:
            description: Internal Server Error
            schema:
                type: object
                properties:
                    error:
                        type: string
                        example: "Error message"
    """
    try:
        system_message = request.json.get('system_message')
        if not system_message:
            return jsonify({'error': 'System message is required'}), 400
        
        token = secrets.token_hex(16)

        database[token] = {
            'system_message': system_message
        }

        return jsonify({'token': token, 'message': 'Model created successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    """
    Send a message to the chat model
    ---
    parameters:
      - name: message
        in: body
        required: true
        type: string
        description: User message
      - name: token
        in: body
        required: false
        type: string
        description: Token for model to use system message
    responses:
        200:
            description: AI response to user message
            schema:
                type: object
                properties:
                    response:
                        type: string
                        example: "The AI's response based on the system message and user input."
        400:
            description: Missing message or invalid token
            schema:
                type: object
                properties:
                    error:
                        type: string
                        example: "Message is required"
        500:
            description: Internal Server Error
            schema:
                type: object
                properties:
                    error:
                        type: string
                        example: "Error message"
    """
    try:
        user_input = request.json.get('message')
        token = request.json.get('token')

        if not user_input:
            return jsonify({'error': 'Message is required'}), 400
        
        if token and token in database:
            system_message = database[token]['system_message']
            messages = [{'role': 'system', 'content': system_message}, {'role': 'user', 'content': user_input}]
        else:
            messages = [{'role': 'user', 'content': user_input}]

        completion = client.chat.completions.create(
            model='llama3-8b-8192',
            messages=messages,
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )

        groq_response = completion.choices[0].message.content
        return jsonify({'response': groq_response}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

