document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const startBtn = document.getElementById('start-btn');
    const startCard = document.getElementById('start-card');
    const qCard = document.getElementById('q-card');
    const resultCard = document.getElementById('result-card');

    const qText = document.getElementById('q-text');
    const answersArea = document.getElementById('answers-area');
    const resetBtn = document.getElementById('reset-btn');
    const thinkingPulse = document.getElementById('thinking-pulse');

    // Progress
    const progressFill = document.getElementById('progress-fill');
    const qCurrent = document.getElementById('q-current');
    let questionCount = 0;
    const TOTAL_QUESTIONS = 20;

    // Result Elements
    const resTitle = document.getElementById('res-title');
    const resReasoning = document.getElementById('res-reasoning');
    const resConfidence = document.getElementById('res-confidence');
    const resSimilarList = document.getElementById('res-similar-list');
    const resSimilarDiv = document.getElementById('res-similar');
    const confirmResBtn = document.getElementById('confirm-res');
    const rejectResBtn = document.getElementById('reject-res');

    // Buttons
    document.querySelectorAll('.ans-btn').forEach(btn => {
        btn.addEventListener('click', () => handleAnswer(btn.getAttribute('data-reply')));
    });

    startBtn.addEventListener('click', startGame);
    resetBtn.addEventListener('click', () => {
        fetch('/api/reset', { method: 'POST' })
            .then(() => location.reload());
    });

    // Result Actions
    rejectResBtn.addEventListener('click', () => {
        // Go back to questioning
        resultCard.style.display = 'none';
        qCard.style.display = 'block';
        answersArea.style.display = 'grid';

        handleAnswer("That is incorrect. Please continue questioning.");
    });

    confirmResBtn.addEventListener('click', () => {
        // Just show a simple celebration state
        resTitle.textContent = "Awesome! 🎉";
        resReasoning.textContent = "Thanks for playing.";
        document.querySelector('.result-actions').style.display = 'none';
        document.querySelector('.confidence-badge').style.display = 'none';
        resSimilarDiv.style.display = 'none';
    });

    function startGame() {
        startCard.style.display = 'none';
        qCard.style.display = 'block';
        setLoading(true);

        fetch('/api/start', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                setLoading(false);
                displayQuestion(data.response);
                updateProgress(1); // Q1
                answersArea.style.display = 'grid'; // Show buttons
            })
            .catch(err => {
                qText.textContent = "Error connecting to AI.";
            });
    }

    function handleAnswer(answer) {
        setLoading(true);
        answersArea.style.opacity = '0.5';
        answersArea.style.pointerEvents = 'none';

        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: answer })
        })
            .then(res => res.json())
            .then(data => {
                setLoading(false);
                answersArea.style.opacity = '1';
                answersArea.style.pointerEvents = 'all';

                // 1. Info Bit (Did you mean?)
                if (data.info_bit) {
                    showInfoToast(data.info_bit);
                }

                // 2. Game Over (Limit Reached)
                if (data.game_over) {
                    showResolutionCard(data.final_candidates);
                    return;
                }

                // 3. Normal Guess vs Question
                if (data.guess) {
                    showResultScreen(data.guess);
                } else {
                    displayQuestion(data.response);
                    questionCount++;
                    updateProgress(questionCount);
                }
            })
            .catch(err => {
                qText.textContent = "Connection Error.";
                setLoading(false);
            });
    }

    function displayQuestion(text) {
        qCard.classList.remove('active');
        void qCard.offsetWidth; // Trigger reflow
        qCard.classList.add('active');
        if (!text) text = "Thinking...";
        qText.textContent = text;
    }

    function updateProgress(num) {
        questionCount = num;
        qCurrent.textContent = num;
        const pct = Math.min((num / 20) * 100, 100);
        progressFill.style.width = pct + '%';
    }

    let loadingTimeout;

    function setLoading(isLoading) {
        const pulse = document.getElementById('thinking-pulse');
        clearTimeout(loadingTimeout); // Clear any existing timer

        if (isLoading) {
            pulse.style.display = 'block';
            qText.style.opacity = '0.5';
            qText.innerText = "Reading your mind...";

            // Set a 30s warning timer
            loadingTimeout = setTimeout(() => {
                if (pulse.style.display === 'block') {
                    qText.innerText = "This is taking a bit long... (Processing Search)";
                }
            }, 10000);

        } else {
            pulse.style.display = 'none';
            qText.style.opacity = '1';
        }
    }

    // --- V2.1 New UI Functions ---

    function showInfoToast(text) {
        const toast = document.getElementById('info-toast');
        const span = document.getElementById('info-text');
        if (toast && span) {
            span.textContent = text;
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, 6000);
        }
    }

    window.showResolutionCard = function (candidates) {
        // Hide Question UI
        document.getElementById('q-card').style.display = 'none';
        document.getElementById('answers-area').style.display = 'none';

        const card = document.getElementById('resolution-card');
        const list = document.getElementById('candidates-list');
        list.innerHTML = '';

        if (candidates) {
            candidates.forEach(cand => {
                const btn = document.createElement('button');
                btn.className = 'candidate-btn';
                btn.textContent = cand;
                btn.onclick = () => showFinalStatus(true, "I Win! 🎉", `I knew it was ${cand}!`);
                list.appendChild(btn);
            });
        }

        card.style.display = 'flex';
    }

    window.showInputForm = function () {
        document.getElementById('btn-none').style.display = 'none';
        document.getElementById('manual-input-area').style.display = 'block';
    }

    window.submitUserBook = function () {
        const bookName = document.getElementById('user-book-input').value;
        if (!bookName) return;
        showFinalStatus(false, "You Win! 🏆", `I couldn't guess "${bookName}". Well played!`);
    }

    function showFinalStatus(aiWon, title, msg) {
        document.getElementById('resolution-card').style.display = 'none';
        document.getElementById('result-card').style.display = 'none';

        const card = document.getElementById('final-status-card');
        card.style.display = 'flex';

        document.getElementById('final-title').textContent = title;
        document.getElementById('final-msg').textContent = msg;
        document.getElementById('final-icon').textContent = aiWon ? '🤖' : '🏆';

        // Hide confetti or other elements if needed
        document.querySelector('.result-actions')?.style.setProperty('display', 'none');
    }

    function showResultScreen(data) {
        // Hide Question UI
        qCard.style.display = 'none';
        answersArea.style.display = 'none';

        // Show Result UI
        resultCard.style.display = 'flex'; // Changed to flex for centering logic often used in cards

        resConfidence.textContent = data.confidence + " Match";
        resTitle.textContent = data.book;
        resReasoning.textContent = data.reasoning;

        resSimilarList.innerHTML = '';
        if (data.similar && data.similar.length > 0) {
            resSimilarDiv.style.display = 'block';
            data.similar.forEach(book => {
                const li = document.createElement('li');
                li.textContent = book;
                resSimilarList.appendChild(li);
            });
        } else {
            resSimilarDiv.style.display = 'none';
        }
    }
});
