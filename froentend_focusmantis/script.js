// Audio conversion and upload handling
(function () {
  const API_BASE = 'http://localhost:5000';
  
  // Initialize uploaders on all section pages
  function initializeUploaders() {
    const dropzones = document.querySelectorAll('[data-dropzone]');
    if (!dropzones.length) return;

    dropzones.forEach((zone) => {
      setupDropzone(zone);
    });
  }

  function setupDropzone(zone) {
    const uploader = zone.closest('.uploader');
    const fileInput = uploader.querySelector('input[type="file"]');
    const label = zone.querySelector('[data-file-label]');
    const category = getCategoryFromPage();

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((eventName) => {
      zone.addEventListener(eventName, preventDefaults, false);
    });

    // Handle drag events
    ['dragenter', 'dragover'].forEach((eventName) => {
      zone.addEventListener(eventName, () => highlight(zone), false);
    });
    
    ['dragleave', 'drop'].forEach((eventName) => {
      zone.addEventListener(eventName, () => unhighlight(zone), false);
    });

    // Handle file drop
    zone.addEventListener('drop', (e) => {
      handleDrop(zone, e.dataTransfer.files, category, label);
    });

    // Handle file selection
    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        handleDrop(zone, e.target.files, category, label);
      });
    }
  }

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function highlight(zone) {
    zone.classList.add('is-dragover');
  }

  function unhighlight(zone) {
    zone.classList.remove('is-dragover');
  }

  function getCategoryFromPage() {
    const body = document.body;
    if (body.classList.contains('phonk-bg')) return 'phonk';
    if (body.classList.contains('melody-bg')) return 'melody';
    if (body.classList.contains('lofi-bg')) return 'lofi';
    if (body.classList.contains('d8-bg')) return '8d';
    return 'unknown';
  }

  async function handleDrop(zone, files, category, label) {
    unhighlight(zone);
    
    if (!files || !files.length) return;

    const file = files[0];
    
    // Validate file type
    if (!isValidAudioFile(file)) {
      showMessage(label, 'Please select a valid audio file (MP3, WAV, M4A, FLAC)', 'error');
      return;
    }

    // Create UI elements for progress
    const progress = ensureProgressUI(zone, label);
    updateProgress(progress, 0, 'Uploading...');
    
    try {
      // Create FormData for upload
      const formData = new FormData();
      formData.append('file', file);

      // Send to backend with streaming upload progress
      const response = await fetch(`${API_BASE}/convert/${category}`, { method: 'POST', body: formData });
      const kickoff = await response.json();

      if (!response.ok || !kickoff.task_id) {
        throw new Error(kickoff.error || 'Upload failed');
      }

      // Poll progress
      await pollProgress(kickoff.task_id, progress, label);
      
    } catch (error) {
      console.error('Upload error:', error);
      showPopup('Song not uploaded', (error && error.message) || 'Please try again.');
      showMessage(label, 'Upload failed. Try again.', 'error');
    }
  }

  function isValidAudioFile(file) {
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/flac'];
    const validExtensions = ['.mp3', '.wav', '.m4a', '.flac'];
    
    return validTypes.includes(file.type) || 
           validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
  }

  function showMessage(label, message, type) {
    label.textContent = message;
    label.className = `message ${type}`;
    
    // Add visual feedback
    if (type === 'error') {
      label.style.color = '#ef4444';
    } else if (type === 'success') {
      label.style.color = '#10b981';
    } else if (type === 'processing') {
      label.style.color = '#3b82f6';
    }
  }

  async function pollProgress(taskId, progressEls, label) {
    let lastPercent = 0;
    updateProgress(progressEls, 10, 'Loading...');
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/progress/${taskId}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Progress error');

        const percent = typeof data.percent === 'number' ? data.percent : lastPercent;
        lastPercent = percent;
        const statusMsg = data.status === 'writing' ? 'Finalizing...' : (data.status || 'Processing...');
        updateProgress(progressEls, percent, statusMsg);

        if (data.status === 'completed' && data.download_url) {
          clearInterval(interval);
          showMessage(label, 'Conversion complete!', 'success');
          const link = document.createElement('a');
          link.href = `${API_BASE}${data.download_url}`;
          link.textContent = 'Download Converted File';
          link.className = 'download-link';
          link.download = (data.filename || 'converted.wav');
          label.innerHTML = '';
          label.appendChild(link);
        } else if (data.status === 'failed') {
          clearInterval(interval);
          showPopup('Conversion failed', data.error || 'Please try another file.');
          showMessage(label, 'Conversion failed. Please try again.', 'error');
        }
      } catch (e) {
        clearInterval(interval);
        showPopup('Conversion failed', e.message || 'Please try again.');
        showMessage(label, 'Conversion failed. Please try again.', 'error');
      }
    }, 700);
  }

  function ensureProgressUI(zone, label) {
    let bar = zone.querySelector('.progress');
    if (!bar) {
      const wrap = document.createElement('div');
      wrap.className = 'progress';
      wrap.innerHTML = '<div class="progress-bar"></div><span class="progress-text"></span>';
      zone.appendChild(wrap);
    }
    const root = zone.querySelector('.progress');
    return {
      root,
      bar: root.querySelector('.progress-bar'),
      text: root.querySelector('.progress-text'),
    };
  }

  function updateProgress(progressEls, percent, text) {
    if (!progressEls || !progressEls.bar) return;
    progressEls.bar.style.width = `${Math.max(0, Math.min(100, percent))}%`;
    if (progressEls.text) progressEls.text.textContent = text || `${percent}%`;
  }

  function showPopup(title, message) {
    const popup = document.createElement('div');
    popup.className = 'popup';
    popup.innerHTML = `<div class="popup-card"><strong>${title}</strong><p>${message}</p><button data-close>OK</button></div>`;
    document.body.appendChild(popup);
    popup.querySelector('[data-close]').addEventListener('click', () => popup.remove());
    // The line below was removed to prevent the popup from closing automatically
    // setTimeout(() => popup.remove(), 6000); 
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUploaders);
  } else {
    initializeUploaders();
  }

  // Add some visual feedback for the upload process
  function addUploadStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .message.processing {
        animation: pulse 1.5s infinite;
      }
      
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
      }
      
      .download-link:hover {
        transform: translateY(-1px);
      }
    `;
    document.head.appendChild(style);
  }

  addUploadStyles();
})();
