import os
import json
import traceback
import io

from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS

from google.cloud import texttospeech
from google.oauth2 import service_account

# 🔐 Load API key (for protecting your endpoint)
API_KEY = os.environ.get("MY_API_KEY")

if not API_KEY:
    raise Exception("MY_API_KEY environment variable not set")

# 🔐 Load Google credentials securely
credentials_json = os.environ.get("GOOGLE_CREDENTIALS")

if not credentials_json:
    raise Exception("GOOGLE_CREDENTIALS environment variable not set")

credentials_info = json.loads(credentials_json)

credentials = service_account.Credentials.from_service_account_info(
    credentials_info
)

client = texttospeech.TextToSpeechClient(credentials=credentials)

# 🌐 Initialize app
app = Flask(__name__)

# 🔒 CORS (restrict later to your domain if needed)
CORS(app, resources={r"/synthesize": {"origins": "*"}})


# 🌐 Home route
@app.route('/')
def index():
    return render_template('index.html')


# 🔇 Ignore favicon errors
@app.route('/favicon.ico')
def favicon():
    return ('', 204)


# 🎤 TTS API
@app.route('/synthesize', methods=['POST'])
def synthesize():
    try:
        # 🔐 API Key Check
        user_key = request.headers.get("x-api-key")

        if user_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({"error": "Text is required"}), 400

        text = data.get('text').strip()

        # 🛡 Prevent abuse
        MAX_TEXT_LENGTH = 500
        if len(text) == 0:
            return jsonify({"error": "Text cannot be empty"}), 400

        if len(text) > MAX_TEXT_LENGTH:
            return jsonify({"error": "Text too long (max 500 chars)"}), 400

        voice_name = data.get('voice', 'en-US-Chirp-HD-F')
        speed = float(data.get('speed', 1.0))
        pitch = float(data.get('pitch', 0.0))
        volume = float(data.get('volume', 0.0))

        print(f"🔊 Request: {text[:60]}...")

        # Input text
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Voice config
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name
        )

        # Audio config
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speed,
            pitch=pitch,
            volume_gain_db=volume
        )

        # Generate speech
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Return audio file
        return send_file(
            io.BytesIO(response.audio_content),
            mimetype='audio/mp3',
            as_attachment=False
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ▶️ Run app (local / Codespaces)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
