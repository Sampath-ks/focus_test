from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment
import io

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac'}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_lofi(audio_data, sample_rate):
    """Convert audio to Lo-Fi style with vinyl effects and low-pass filtering"""
    # Load audio
    y = audio_data
    
    # Apply low-pass filter for warm, muffled sound
    from scipy import signal
    b, a = signal.butter(4, 0.3, btype='low')
    y = signal.filtfilt(b, a, y)
    
    # Add vinyl crackle effect
    crackle = np.random.normal(0, 0.01, len(y))
    y = y + crackle * 0.1
    
    # Add slight pitch variation (vinyl warping effect)
    pitch_shift = librosa.effects.pitch_shift(y, sr=sample_rate, n_steps=-1)
    y = 0.7 * y + 0.3 * pitch_shift
    
    # Reduce sample rate for vintage feel
    y = librosa.resample(y, orig_sr=sample_rate, target_sr=int(sample_rate * 0.8))
    
    return y, int(sample_rate * 0.8)

def convert_to_phonk(audio_data, sample_rate):
    """Convert audio to Phonk style with heavy bass and distortion"""
    y = audio_data
    
    # Boost bass frequencies
    y = librosa.effects.harmonic(y)
    
    # Add distortion/saturation
    y = np.tanh(y * 2) * 0.8
    
    # Apply heavy compression
    y = np.sign(y) * np.log1p(np.abs(y) * 10) / 10
    
    # Add reverb effect
    y = librosa.effects.preemphasis(y, coef=0.95)
    
    # Boost low frequencies
    freqs = librosa.fft_frequencies(sr=sample_rate)
    y_fft = np.fft.fft(y)
    bass_boost = np.ones_like(freqs)
    bass_boost[freqs < 200] = 2.0
    y_fft = y_fft * bass_boost[:len(y_fft)]
    y = np.real(np.fft.ifft(y_fft))
    
    return y, sample_rate

def convert_to_melody(audio_data, sample_rate):
    """Convert audio to Melody style with enhanced harmonics and clarity"""
    y = audio_data
    
    # Enhance harmonics
    y = librosa.effects.harmonic(y)
    
    # Apply high-pass filter to remove mud
    from scipy import signal
    b, a = signal.butter(4, 0.1, btype='high')
    y = signal.filtfilt(b, a, y)
    
    # Add slight reverb
    y = librosa.effects.preemphasis(y, coef=0.97)
    
    # Enhance mid frequencies for melody clarity
    freqs = librosa.fft_frequencies(sr=sample_rate)
    y_fft = np.fft.fft(y)
    mid_boost = np.ones_like(freqs)
    mid_boost[(freqs >= 1000) & (freqs <= 5000)] = 1.5
    y_fft = y_fft * mid_boost[:len(y_fft)]
    y = np.real(np.fft.ifft(y_fft))
    
    # Normalize
    y = librosa.util.normalize(y)
    
    return y, sample_rate

def convert_to_8d(audio_data, sample_rate):
    """Convert audio to 8D style with spatial audio effects"""
    y = audio_data
    
    # Create stereo effect if mono
    if len(y.shape) == 1:
        y = np.column_stack((y, y))
    
    # Apply binaural processing for 3D effect
    # Simulate head-related transfer function (HRTF)
    left_channel = y[:, 0] if len(y.shape) > 1 else y
    right_channel = y[:, 1] if len(y.shape) > 1 else y
    
    # Add phase differences for spatial effect
    phase_shift = int(sample_rate * 0.001)  # 1ms delay
    right_channel = np.roll(right_channel, phase_shift)
    
    # Apply frequency-dependent filtering for each ear
    from scipy import signal
    
    # Left ear filter (slight high-pass)
    b_left, a_left = signal.butter(2, 0.2, btype='high')
    left_channel = signal.filtfilt(b_left, a_left, left_channel)
    
    # Right ear filter (slight low-pass)
    b_right, a_right = signal.butter(2, 0.3, btype='low')
    right_channel = signal.filtfilt(b_right, a_right, right_channel)
    
    # Combine channels
    y = np.column_stack((left_channel, right_channel))
    
    # Add slight reverb for depth
    y = librosa.effects.preemphasis(y, coef=0.95)
    
    return y, sample_rate

@app.route('/convert/<category>', methods=['POST'])
def convert_audio(category):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{filename}")
        output_path = os.path.join(PROCESSED_FOLDER, f"{unique_id}_{category}_{filename}")
        
        # Save uploaded file
        file.save(input_path)
        
        # Load audio
        y, sr = librosa.load(input_path, sr=None)
        
        # Convert based on category
        if category == 'lofi':
            processed_audio, new_sr = convert_to_lofi(y, sr)
        elif category == 'phonk':
            processed_audio, new_sr = convert_to_phonk(y, sr)
        elif category == 'melody':
            processed_audio, new_sr = convert_to_melody(y, sr)
        elif category == '8d':
            processed_audio, new_sr = convert_to_8d(y, sr)
        else:
            return jsonify({'error': 'Invalid category'}), 400
        
        # Save processed audio
        sf.write(output_path, processed_audio, new_sr)
        
        # Clean up input file
        os.remove(input_path)
        
        return jsonify({
            'success': True,
            'message': f'Audio converted to {category} successfully',
            'filename': f"{unique_id}_{category}_{filename}",
            'download_url': f'/download/{unique_id}_{category}_{filename}'
        })
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(input_path):
            os.remove(input_path)
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(
            os.path.join(PROCESSED_FOLDER, filename),
            as_attachment=True,
            download_name=filename
        )
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Audio conversion service is running'})

# ---------------------
# Static file routes
# ---------------------
@app.route('/')
def serve_index():
    return send_file(os.path.join(BASE_DIR, 'index.html'))


@app.route('/style.css')
def serve_css():
    return send_file(os.path.join(BASE_DIR, 'style.css'))


@app.route('/script.js')
def serve_js():
    return send_file(os.path.join(BASE_DIR, 'script.js'))


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_file(os.path.join(BASE_DIR, 'assets', filename))


@app.route('/phonk.html')
def serve_phonk():
    return send_file(os.path.join(BASE_DIR, 'phonk.html'))


@app.route('/melody.html')
def serve_melody():
    return send_file(os.path.join(BASE_DIR, 'melody.html'))


@app.route('/lofi.html')
def serve_lofi():
    return send_file(os.path.join(BASE_DIR, 'lofi.html'))


@app.route('/8d.html')
def serve_8d():
    return send_file(os.path.join(BASE_DIR, '8d.html'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

