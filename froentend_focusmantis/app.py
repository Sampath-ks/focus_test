from flask import Flask, request, jsonify, send_file,render_template
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
import threading

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac'}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Simple in-memory task progress store
TASK_PROGRESS = {}
TASK_LOCK = threading.Lock()

def _set_progress(task_id, *, percent=None, status=None, filename=None, error=None):
    with TASK_LOCK:
        state = TASK_PROGRESS.get(task_id, {})
        if percent is not None:
            # clamp
            state['percent'] = max(0, min(100, int(percent)))
        if status is not None:
            state['status'] = status
        if filename is not None:
            state['filename'] = filename
        if error is not None:
            state['error'] = error
        TASK_PROGRESS[task_id] = state

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_lofi(audio_data, sample_rate):
    """Convert audio to Lo-Fi style with vinyl effects and low-pass filtering"""
    y = audio_data
    from scipy import signal
    b, a = signal.butter(4, 0.3, btype='low')
    y = signal.filtfilt(b, a, y)
    crackle = np.random.normal(0, 0.01, len(y))
    y = y + crackle * 0.1
    pitch_shift = librosa.effects.pitch_shift(y, sr=sample_rate, n_steps=-1)
    y = 0.7 * y + 0.3 * pitch_shift
    target_lofi_rate = 22050
    y = librosa.resample(y, orig_sr=sample_rate, target_sr=target_lofi_rate)
    return y, target_lofi_rate

def convert_to_phonk(audio_data, sample_rate):
    """Convert audio to Phonk style quickly and robustly"""
    y = audio_data.astype(np.float32)
    y = np.tanh(y * 2.0) * 0.85
    from scipy import signal
    b, a = signal.butter(3, 200 / (sample_rate / 2.0), btype='low')
    low = signal.lfilter(b, a, y)
    y = np.clip(y + 0.9 * low, -1.0, 1.0)
    y = np.sign(y) * (np.log1p(6 * np.abs(y)) / np.log1p(6))
    y = librosa.effects.preemphasis(y, coef=0.85)
    return y.astype(np.float32), sample_rate

def convert_to_melody(audio_data, sample_rate):
    """Convert audio to Melody style quickly with clarity"""
    y = audio_data.astype(np.float32)
    from scipy import signal
    b_hp, a_hp = signal.butter(3, 120 / (sample_rate / 2.0), btype='high')
    y = signal.lfilter(b_hp, a_hp, y)
    Y = np.fft.rfft(y)
    freqs = np.fft.rfftfreq(len(y), d=1.0 / sample_rate)
    band = (freqs >= 1000) & (freqs <= 5000)
    Y[band] *= 1.3
    y = np.fft.irfft(Y, n=len(y)).astype(np.float32)
    y = librosa.effects.preemphasis(y, coef=0.9)
    y = y / (np.max(np.abs(y)) + 1e-8)
    return y.astype(np.float32), sample_rate

def convert_to_8d(audio_data, sample_rate):
    """Convert audio to 8D style with spatial audio effects"""
    y = audio_data.astype(np.float32)
    if len(y.shape) == 1:
        y = np.column_stack((y, y))
    left_channel = y[:, 0]
    right_channel = y[:, 1]
    phase_shift = int(sample_rate * 0.001)
    right_channel = np.roll(right_channel, phase_shift)
    from scipy import signal
    b_left, a_left = signal.butter(2, 0.2, btype='high')
    left_channel = signal.filtfilt(b_left, a_left, left_channel)
    b_right, a_right = signal.butter(2, 0.3, btype='low')
    right_channel = signal.filtfilt(b_right, a_right, right_channel)
    left_channel = librosa.effects.preemphasis(left_channel, coef=0.9)
    right_channel = librosa.effects.preemphasis(right_channel, coef=0.9)
    y = np.column_stack((left_channel, right_channel)).astype(np.float32)
    return y.astype(np.float32), sample_rate

@app.route('/convert/<category>', methods=['POST'])
def convert_audio(category):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    
    filename = secure_filename(file.filename)
    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_{filename}")
    output_filename = f"{task_id}_{category}_{filename}"
    output_path = os.path.join(PROCESSED_FOLDER, output_filename)
    file.save(input_path)
    _set_progress(task_id, percent=0, status='queued')

    def _worker():
        try:
            _set_progress(task_id, percent=10, status='loading')
            y, sr = librosa.load(input_path, sr=22050, mono=True)
            _set_progress(task_id, percent=35, status='processing')
            
            conversion_funcs = {
                'lofi': convert_to_lofi,
                'phonk': convert_to_phonk,
                'melody': convert_to_melody,
                '8d': convert_to_8d,
            }
            if category not in conversion_funcs:
                raise ValueError('Invalid category')
            
            processed_audio, new_sr = conversion_funcs[category](y, sr)
            _set_progress(task_id, percent=75, status='writing')
            sf.write(output_path, processed_audio, new_sr)
            _set_progress(task_id, percent=100, status='completed', filename=output_filename)
        except Exception as e:
            _set_progress(task_id, status='failed', error=str(e))
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)

    threading.Thread(target=_worker, daemon=True).start()
    return jsonify({'task_id': task_id, 'status_url': f'/progress/{task_id}'})

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(os.path.join(PROCESSED_FOLDER, filename), as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

# --- ROUTES FOR HTML AND STATIC FILES ---

@app.route('/')
def serve_index():
    # This now serves index.html from the root folder
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

# These routes correctly serve other HTML files from the 'templates' folder
@app.route('/phonk.html')
def serve_phonk():
    return render_template('phonk.html')

@app.route('/melody.html')
def serve_melody():
    return render_template('melody.html')

@app.route('/lofi.html')
def serve_lofi():
    return render_template('lofi.html')

@app.route('/8d.html')
def serve_8d():
    return render_template('8d.html')

@app.route('/progress/<task_id>')
def progress(task_id):
    with TASK_LOCK:
        data = TASK_PROGRESS.get(task_id)
    if not data:
        return jsonify({'error': 'Task not found'}), 404
    if data.get('status') == 'completed' and data.get('filename'):
        data['download_url'] = f"/download/{data['filename']}"
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
