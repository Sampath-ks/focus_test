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

    // Show processing state
    showMessage(label, `Converting to ${category}...`, 'processing');
    
    try {
      // Create FormData for upload
      const formData = new FormData();
      formData.append('file', file);

      // Send to backend
      const response = await fetch(`${API_BASE}/convert/${category}`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (result.success) {
        showMessage(label, `${category} conversion complete!`, 'success');
        
        // Create download link
        const downloadLink = document.createElement('a');
        downloadLink.href = `${API_BASE}${result.download_url}`;
        downloadLink.textContent = 'Download Converted File';
        downloadLink.className = 'download-link';
        downloadLink.download = result.filename;
        
        // Replace label with download link
        label.innerHTML = '';
        label.appendChild(downloadLink);
        
        // Add download button styling
        downloadLink.style.cssText = `
          display: inline-block;
          padding: 8px 16px;
          background: #10b981;
          color: white;
          text-decoration: none;
          border-radius: 8px;
          font-weight: 600;
          transition: background 0.2s;
        `;
        
        downloadLink.addEventListener('mouseenter', () => {
          downloadLink.style.background = '#059669';
        });
        
        downloadLink.addEventListener('mouseleave', () => {
          downloadLink.style.background = '#10b981';
        });
        
      } else {
        showMessage(label, `Conversion failed: ${result.error}`, 'error');
      }
      
    } catch (error) {
      console.error('Upload error:', error);
      showMessage(label, 'Conversion failed. Please try again.', 'error');
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


