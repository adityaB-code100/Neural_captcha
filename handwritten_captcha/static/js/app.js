document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const credentialsStep = document.getElementById('credentials-step');
    const captchaStep = document.getElementById('captcha-step');
    
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const nextToCaptchaBtn = document.getElementById('next-to-captcha');
    const backToCredentialsBtn = document.getElementById('back-to-credentials');
    
    const progressText = document.getElementById('progress-text');
    const progressPct = document.getElementById('progress-pct');
    const progressBar = document.getElementById('progress-bar');
    
    const targetCharEl = document.getElementById('captcha-target');
    const targetTypeEl = document.getElementById('target-type');
    
    const canvas = document.getElementById('drawing-canvas');
    const ctx = canvas.getContext('2d');
    const placeholder = document.getElementById('canvas-placeholder');
    const clearBtn = document.getElementById('clear-btn');
    const nextCharBtn = document.getElementById('next-char-btn');
    const nextBtnText = document.getElementById('next-btn-text');
    const nextBtnIcon = document.getElementById('next-btn-icon');
    
    const actionOverlay = document.getElementById('action-overlay');
    const overlayTitle = document.getElementById('overlay-status-title');
    const overlaySub = document.getElementById('overlay-status-sub');
    
    const alertBanner = document.getElementById('alert-banner');
    const alertText = document.getElementById('alert-text');
    const alertClose = document.getElementById('alert-close');

    // Drawing Canvas State
    let isDrawing = false;
    let hasDrawn = false;
    let brushRadius = 18;
    let lastX = 0;
    let lastY = 0;
    
    // CAPTCHA State Machine
    let captchaCharacters = []; // List of characters to draw (10 alphanumeric chars)
    let currentStepIndex = 0;   // Current active character drawing step (0-9)
    let drawnImages = [];       // Array of 10 base64 drawings saved sequentially

    // Initialize Canvas Configuration
    const initCanvas = () => {
        // High-precision canvas initialization (filling pure black as expected by preprocessing)
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Anti-aliased smooth brush setup
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = brushRadius;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        hasDrawn = false;
        placeholder.style.opacity = '0.6';
    };



    // Helper: Determine target character character class description
    const getCharacterTypeLabel = (char) => {
        if (!char) return "";
        if (char.isdigit || (char >= '0' && char <= '9')) {
            return "Numeric Digit";
        } else if (char === char.toUpperCase()) {
            return "Uppercase Character";
        } else {
            return "Lowercase Character";
        }
    };

    // Setup Canvas Drawing Mechanics (Mouse & Touch compatible)
    const getCoordinates = (e) => {
        const rect = canvas.getBoundingClientRect();
        // Adjust for css scaling vs actual internal canvas resolution
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        
        let clientX, clientY;
        if (e.touches && e.touches.length > 0) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }
        
        return {
            x: (clientX - rect.left) * scaleX,
            y: (clientY - rect.top) * scaleY
        };
    };

    const startDrawing = (e) => {
        e.preventDefault();
        isDrawing = true;
        hasDrawn = true;
        placeholder.style.opacity = '0';
        hideAlert();
        
        const coords = getCoordinates(e);
        lastX = coords.x;
        lastY = coords.y;
        
        // Draw initial point
        ctx.beginPath();
        ctx.arc(lastX, lastY, brushRadius / 2, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
    };

    const draw = (e) => {
        if (!isDrawing) return;
        e.preventDefault();
        
        const coords = getCoordinates(e);
        
        // High fidelity line connections for drawing smoothness
        ctx.lineTo(coords.x, coords.y);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(coords.x, coords.y);
        
        lastX = coords.x;
        lastY = coords.y;
    };

    const stopDrawing = () => {
        if (isDrawing) {
            isDrawing = false;
            ctx.beginPath();
        }
    };

    // Event Listeners for Drawing Canvas
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseleave', stopDrawing);

    canvas.addEventListener('touchstart', startDrawing, { passive: false });
    canvas.addEventListener('touchmove', draw, { passive: false });
    canvas.addEventListener('touchend', stopDrawing);

    clearBtn.addEventListener('click', initCanvas);

    // Global Alert UI handlers
    const showAlert = (message, type = 'error') => {
        alertText.textContent = message;
        alertBanner.className = 'alert-banner'; // reset classes
        if (type === 'success') {
            alertBanner.classList.add('success');
        }
        alertBanner.classList.remove('hidden');
        alertBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };

    const hideAlert = () => {
        alertBanner.classList.add('hidden');
    };

    alertClose.addEventListener('click', hideAlert);

    // Step 1 -> Step 2 UI transition
    nextToCaptchaBtn.addEventListener('click', () => {
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        
        if (!username || !password) {
            showAlert("Please fill in both system username and password credentials.");
            return;
        }
        
        hideAlert();
        // Trigger model challenge load from backend, then transition
        loadCaptchaChallenge();
    });

    backToCredentialsBtn.addEventListener('click', () => {
        captchaStep.classList.remove('active');
        credentialsStep.classList.add('active');
        hideAlert();
    });

    // API: Generate CAPTCHA Challenge from Server
    const loadCaptchaChallenge = async () => {
        // Display loading overlay during first fetch
        actionOverlay.classList.remove('hidden');
        overlayTitle.textContent = "Loading Gate...";
        overlaySub.textContent = "Configuring secure neural CAPTCHA node...";
        
        try {
            const res = await fetch('/api/generate_captcha');
            const data = await res.json();
            
            if (data.status === 'success') {
                captchaCharacters = data.captcha_chars;
                currentStepIndex = 0;
                drawnImages = [];
                
                // Show canvas step
                credentialsStep.classList.remove('active');
                captchaStep.classList.add('active');
                
                renderStep();
            } else {
                showAlert(data.message || "Failed to load verification challenge.");
            }
        } catch (err) {
            console.error(err);
            showAlert("Network communication error. Failed to reach gateway.");
        } finally {
            actionOverlay.classList.add('hidden');
        }
    };

    // Render CAPTCHA drawing queue step
    const renderStep = () => {
        initCanvas();
        
        const targetChar = captchaCharacters[currentStepIndex];
        targetCharEl.textContent = targetChar;
        targetCharEl.className = 'target-char animate-pop';
        targetTypeEl.textContent = getCharacterTypeLabel(targetChar);
        
        // Update Progress Bar
        const stepNum = currentStepIndex + 1;
        const percent = Math.round((stepNum / 10) * 100);
        
        progressText.textContent = `Character ${stepNum} of 10`;
        progressPct.textContent = `${percent}%`;
        progressBar.style.width = `${percent}%`;
        
        // If final step, update button text and icon
        if (currentStepIndex === 9) {
            nextBtnText.textContent = "Verify & Login";
            // Replace next icon with secure padlock check SVG
            nextBtnIcon.innerHTML = `<rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path>`;
        } else {
            nextBtnText.textContent = "Next Character";
            nextBtnIcon.innerHTML = `<polyline points="9 18 15 12 9 6"></polyline>`;
        }
    };

    // Sequential multi-step drawing capture
    nextCharBtn.addEventListener('click', async () => {
        if (!hasDrawn) {
            showAlert("Draw verification block before proceeding.");
            return;
        }
        
        // 1. Save base64 string
        const base64Image = canvas.toDataURL('image/png');
        drawnImages.push(base64Image);
        
        // 2. Increment steps
        if (currentStepIndex < 9) {
            currentStepIndex++;
            renderStep();
        } else {
            // 3. Final Step: Submit Entire Form via AJAX
            await submitVerification();
        }
    });

    // API: AJAX canvas submit
    const submitVerification = async () => {
        hideAlert();
        actionOverlay.classList.remove('hidden');
        overlayTitle.textContent = "Verifying Identity...";
        overlaySub.textContent = "Analyzing handwriting vectors via neural network ensemble...";
        
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        
        try {
            const response = await fetch('/api/verify_captcha', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    images: drawnImages
                })
            });
            
            const data = await response.json();
            
            if (response.status === 200 && data.status === 'success') {
                overlayTitle.textContent = "Authorized ✓";
                overlaySub.textContent = "Redirecting to Secure X Console...";
                showAlert("Verification successful! Authenticating...", "success");
                
                // Slow redirection for rich UX completion
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1200);
            } else {
                // Failure handler: reset CAPTCHA and drawing states
                actionOverlay.classList.add('hidden');
                showAlert(data.message || "CAPTCHA verification failed. Draw clearer and try again.");
                
                // Regenerate a brand new CAPTCHA challenge automatically
                loadCaptchaChallenge();
            }
        } catch (err) {
            console.error(err);
            actionOverlay.classList.add('hidden');
            showAlert("Connection failed. Portal server timed out.");
            loadCaptchaChallenge();
        }
    };
});
