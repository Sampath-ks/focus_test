# Focus Mantis - Audio Conversion Platform

A responsive web application that converts regular audio files into different styles: Phonk, Melody, Lo-Fi, and 8D audio.

## Features

- **4 Audio Styles**: Convert any audio file to Phonk, Melody, Lo-Fi, or 8D
- **Drag & Drop**: Easy file upload with drag-and-drop support
- **Real-time Processing**: Audio conversion with progress feedback
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean, animated interface with hover effects

## Audio Conversion Styles

### 🎵 Phonk
- Heavy bass boost
- Distortion and saturation effects
- Compression and reverb
- Aggressive low-frequency enhancement

### 🎼 Melody
- Enhanced harmonics
- High-pass filtering for clarity
- Mid-frequency boost
- Clean, focused sound

### 🎧 Lo-Fi
- Vinyl crackle effects
- Low-pass filtering for warmth
- Pitch variation (vinyl warping)
- Reduced sample rate for vintage feel

### 🌟 8D Audio
- Spatial audio processing
- Binaural effects
- Head-related transfer function simulation
- 3D audio experience

## Project Structure

```
project/
├── index.html          # Main page with 4 category cards
├── phonk.html          # Phonk conversion page
├── melody.html         # Melody conversion page
├── lofi.html           # Lo-Fi conversion page
├── 8d.html            # 8D conversion page
├── style.css           # All styles and animations
├── script.js           # Frontend JavaScript
├── app.py              # Flask backend server
├── requirements.txt    # Python dependencies
├── uploads/            # Temporary upload storage
├── processed/          # Converted audio files
└── assets/images/      # Logo and background images
```

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note**: Some audio processing libraries may require additional system dependencies:

- **Ubuntu/Debian**: `sudo apt-get install libsndfile1-dev ffmpeg`
- **macOS**: `brew install libsndfile ffmpeg`
- **Windows**: Download and install FFmpeg from https://ffmpeg.org/

### 2. Start the Backend Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 3. Open the Frontend

Open `index.html` in your web browser, or serve the folder with a simple HTTP server:

```bash
# Python 3
python -m http.server 8000

# Then open http://localhost:8000
```

## Usage

1. **Navigate to a category page** (Phonk, Melody, Lo-Fi, or 8D)
2. **Upload an audio file** by dragging and dropping or clicking "Choose MP3"
3. **Wait for conversion** - the backend will process your audio
4. **Download the converted file** when processing is complete

## Supported Audio Formats

- **Input**: MP3, WAV, M4A, FLAC
- **Output**: WAV (high quality)

## API Endpoints

- `POST /convert/<category>` - Convert audio to specified style
- `GET /download/<filename>` - Download converted audio file
- `GET /health` - Server health check

## Technical Details

### Backend
- **Framework**: Flask with CORS support
- **Audio Processing**: librosa, scipy, soundfile
- **File Handling**: Secure upload/download with unique IDs

### Frontend
- **Vanilla JavaScript**: No external frameworks
- **CSS Grid/Flexbox**: Responsive layout
- **Drag & Drop**: HTML5 File API
- **Real-time Updates**: Fetch API for backend communication

## Customization

### Adding New Audio Styles
1. Create a new conversion function in `app.py`
2. Add the route to handle the new category
3. Update the frontend to include the new style

### Modifying Audio Effects
Edit the conversion functions in `app.py`:
- `convert_to_phonk()` - Bass and distortion effects
- `convert_to_melody()` - Harmonic enhancement
- `convert_to_lofi()` - Vinyl and vintage effects
- `convert_to_8d()` - Spatial audio processing

## Troubleshooting

### Common Issues

1. **Audio conversion fails**
   - Check if FFmpeg is installed
   - Verify audio file format is supported
   - Check server logs for error details

2. **Frontend can't connect to backend**
   - Ensure Flask server is running on port 5000
   - Check CORS settings if accessing from different domain

3. **Large files fail to upload**
   - Check Flask upload size limits
   - Consider chunked upload for very large files

### Performance Tips

- **Audio Quality**: Higher sample rates increase processing time
- **File Size**: Larger files take longer to convert
- **Server Resources**: Audio processing is CPU-intensive

## License

This project is open source. Feel free to modify and distribute.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review server logs
3. Open an issue on the repository

