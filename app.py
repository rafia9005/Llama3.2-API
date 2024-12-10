import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from groq import Groq

load_dotenv(dotenv_path='.env')

app = Flask(__name__)

client = Groq(
    api_key=os.environ.get('GROQ_TOKEN'),
)


@app.route('/', methods=['GET'])
def index():
    return '<h1>Active</h1>'


@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get('message')
        if not user_input:
            return jsonify({'error': 'Message is required'}), 400

        completion = client.chat.completions.create(
            model='llama3-8b-8192',
            messages=[
                {'role': 'user', 'content': user_input},
            ],
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


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'}), 200


if __name__ == '__main__':
    app.run(debug=True)
