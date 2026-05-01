import os
import json
import traceback
import io

from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS

from google.cloud import texttospeech
from google.oauth2 import service_account

app = Flask(__name__)
CORS(app)

# 🔐 Load credentials securely from environment variable
credentials_json = os.environ.get("GOOGLE_CREDENTIALS")

if not credentials_json:
    raise Exception("GOOGLE_CREDENTIALS environment variable not set")

credentials_info = json.loads(credentials_json)

credentials = service_account.Credentials.from_service_account_info(
    credentials_info
)

client = texttospeech.TextToSpeechClient(credentials=credentials)


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
        data = request.json

        if not data or 'text' not in data:
            return jsonify({"error": "Text is required"}), 400

        text = data.get('text')
        voice_name = data.get('voice', 'en-US-Chirp-HD-F')
        speed = float(data.get('speed', 1.0))
        pitch = float(data.get('pitch', 0.0))
        volume = float(data.get('volume', 0.0))

        # Input text
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Voice settings
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

        # Return audio
        return send_file(
            io.BytesIO(response.audio_content),
            mimetype='audio/mp3',
            as_attachment=False
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ▶️ Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
