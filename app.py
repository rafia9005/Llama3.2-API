import os
import time
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from groq import Groq

load_dotenv(dotenv_path='.env')

app = Flask(__name__)

client = Groq(
    api_key=os.environ.get('GROQ_TOKEN'),
)

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

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get('message')
        if not user_input:
            return jsonify({'error': 'Message is required'}), 400

        completion = client.chat.completions.create(
            model='llama3-8b-8192',
            messages=[{'role': 'user', 'content': user_input}],
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

@app.route('/docs', methods=['GET'])
def docs():
    documentation = {
      "api_version": "1.0",
      "documentation": [
        {
          "method": "GET",
          "url": "/",
          "description": "Returns a health check status of the API, including uptime, Groq API status, and server time.",
          "response": {
            "status": "OK",
            "uptime": "HH:MM:SS",
            "groq_status": "llama3-8b-8192 is responsive",
            "server_time": "YYYY-MM-DD HH:MM:SS",
            "message": "All systems are operational."
          }
        },
        {
          "method": "POST",
          "url": "/chat",
          "description": "Handles user messages and generates responses using the Groq API.",
          "request_body": {
            "message": "The input message sent by the user that is to be processed."
          },
          "response": {
            "response": "The response from the Groq API based on the user input."
          },
          "errors": [
            {
              "code": "400",
              "message": "Message is required"
            },
            {
              "code": "500",
              "message": "Internal server error or error while processing Groq API."
            }
          ]
        }
      ]
    }
    return jsonify(documentation), 200


if __name__ == '__main__':
    app.run(debug=True)

