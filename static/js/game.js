// Game state
let currentWord = null;
let wordDefinition = null;
let speechSpeed = 0.75; // Default speech speed

// Update bucket progress widget
function updateBucketProgress(wordsMastered, wordsToComplete, wordsNeed1, wordsNeed2, wordsNeed3) {
    // Update words mastered count
    const wordsMasteredEl = document.getElementById('sidebar-words-mastered');
    if (wordsMasteredEl) {
        wordsMasteredEl.textContent = wordsMastered;
    }
    
    // Update words remaining
    const wordsRemaining = wordsToComplete - wordsMastered;
    const wordsRemainingEl = document.getElementById('sidebar-words-remaining');
    if (wordsRemainingEl) {
        wordsRemainingEl.textContent = wordsRemaining;
    }
    
    // Update progress bar
    const progressPercent = Math.min(Math.round((wordsMastered / wordsToComplete) * 100), 100);
    const progressFillEl = document.getElementById('sidebar-progress-fill');
    if (progressFillEl) {
        progressFillEl.style.width = progressPercent + '%';
        
        // Update percentage text
        const percentageEl = progressFillEl.querySelector('.progress-percentage');
        if (percentageEl) {
            percentageEl.textContent = progressPercent + '%';
        }
    }
    
    // Update progress message
    const progressMessageContainer = document.querySelector('.progress-message');
    if (progressMessageContainer) {
        let messageHtml = '';
        
        if (progressPercent >= 100) {
            messageHtml = '<p class="complete-message">✅ Bucket complete! Keep playing to advance!</p>';
        } else if (progressPercent >= 75) {
            messageHtml = `<p class="almost-message">🔥 Almost there! Just ${wordsRemaining} more!</p>`;
        } else if (progressPercent >= 50) {
            messageHtml = '<p class="halfway-message">💪 Halfway there! Keep going!</p>';
        } else if (progressPercent >= 25) {
            messageHtml = `<p class="progress-message-text">📈 Making progress! ${wordsRemaining} words to go!</p>`;
        } else {
            messageHtml = '<p class="start-message">🚀 Let\'s master this bucket!</p>';
        }
        
        progressMessageContainer.innerHTML = messageHtml;
    }
    
    // Update words in progress counts
    if (wordsNeed1 !== undefined) {
        const need1El = document.querySelector('#words-need-1 .need-count');
        if (need1El) need1El.textContent = wordsNeed1;
    }
    if (wordsNeed2 !== undefined) {
        const need2El = document.querySelector('#words-need-2 .need-count');
        if (need2El) need2El.textContent = wordsNeed2;
    }
    if (wordsNeed3 !== undefined) {
        const need3El = document.querySelector('#words-need-3 .need-count');
        if (need3El) need3El.textContent = wordsNeed3;
    }
}

// Update leaderboard widget with new data
function updateLeaderboard(leaderboardData) {
    if (!leaderboardData) return;
    
    const sidebar = document.querySelector('.leaderboard-sidebar');
    if (!sidebar) return;
    
    const currentStudent = leaderboardData.current_student;
    const top5 = leaderboardData.top_5;
    
    // Update rank badge
    const rankBadge = sidebar.querySelector('.rank-badge');
    if (rankBadge && currentStudent) {
        // Determine badge color class
        let colorClass = '';
        if (currentStudent.rank === 1) colorClass = 'gold';
        else if (currentStudent.rank === 2) colorClass = 'silver';
        else if (currentStudent.rank === 3) colorClass = 'bronze';
        
        rankBadge.className = `rank-badge ${colorClass}`;
        
        // Update rank number
        const rankNumber = rankBadge.querySelector('.rank-number');
        if (rankNumber) {
            if (currentStudent.rank === 1) rankNumber.textContent = '🥇';
            else if (currentStudent.rank === 2) rankNumber.textContent = '🥈';
            else if (currentStudent.rank === 3) rankNumber.textContent = '🥉';
            else rankNumber.textContent = `#${currentStudent.rank}`;
        }
        
        // Update rank total
        const rankTotal = rankBadge.querySelector('.rank-total');
        if (rankTotal) {
            rankTotal.textContent = `of ${leaderboardData.total_students}`;
        }
        
        // Update score
        const scoreDisplay = rankBadge.querySelector('.score-display');
        if (scoreDisplay) {
            scoreDisplay.textContent = `${currentStudent.score} pts`;
        }
        
        // Update gap or leader badge
        let gapOrLeaderHtml = '';
        if (currentStudent.rank === 1) {
            gapOrLeaderHtml = '<div class="leader-badge">👑 You\'re the leader!</div>';
        } else if (leaderboardData.gap_to_next && leaderboardData.next_student) {
            gapOrLeaderHtml = `<div class="gap-display">${leaderboardData.gap_to_next} pts behind ${leaderboardData.next_student.username}</div>`;
        }
        
        // Remove old gap/leader element and add new one
        const oldGapOrLeader = rankBadge.querySelector('.gap-display, .leader-badge');
        if (oldGapOrLeader) {
            oldGapOrLeader.remove();
        }
        if (gapOrLeaderHtml) {
            rankBadge.insertAdjacentHTML('beforeend', gapOrLeaderHtml);
        }
    }
    
    // Update top 5 list
    const miniLeaderboard = sidebar.querySelector('.mini-leaderboard');
    if (miniLeaderboard && top5 && top5.length > 0) {
        const container = miniLeaderboard.querySelector('.mini-leaderboard-title').nextElementSibling.parentElement;
        
        // Find all existing items (after the title)
        const existingItems = miniLeaderboard.querySelectorAll('.mini-leaderboard-item');
        
        // Update each item
        top5.forEach((student, index) => {
            let itemEl = existingItems[index];
            
            if (itemEl) {
                // Update existing item
                let itemClass = 'mini-leaderboard-item';
                if (student.is_current) itemClass += ' highlighted';
                else if (student.rank === 1) itemClass += ' top1';
                else if (student.rank === 2) itemClass += ' top2';
                else if (student.rank === 3) itemClass += ' top3';
                
                itemEl.className = itemClass;
                
                // Update medal/rank
                let medal = '';
                if (student.rank === 1) medal = '🥇';
                else if (student.rank === 2) medal = '🥈';
                else if (student.rank === 3) medal = '🥉';
                else medal = `#${student.rank}`;
                
                const nameSpan = itemEl.querySelector('.mini-student-name');
                if (nameSpan) {
                    nameSpan.innerHTML = `${medal} ${student.username}${student.is_current ? ' (You)' : ''}`;
                }
                
                const scoreSpan = itemEl.querySelector('.mini-student-score');
                if (scoreSpan) {
                    scoreSpan.textContent = student.score;
                }
            }
        });
    }
}

// Show congratulations modal
function showCongratulationsModal(message) {
    const modal = document.getElementById('congratulations-modal');
    const messageEl = document.getElementById('modal-message');
    messageEl.textContent = message;
    modal.classList.add('show');
}

// Close congratulations modal
function closeCongratulationsModal() {
    const modal = document.getElementById('congratulations-modal');
    modal.classList.remove('show');
}

// Show game complete modal and redirect to dashboard
function showGameCompleteModal(message) {
    const modal = document.getElementById('congratulations-modal');
    const messageEl = document.getElementById('modal-message');
    const modalTitle = modal.querySelector('h2');
    const continueBtn = document.getElementById('modal-continue-btn');
    
    // Update modal content for game completion
    modalTitle.textContent = '🏆 Amazing Achievement!';
    messageEl.textContent = message;
    continueBtn.textContent = 'View My Progress';
    
    // Change the button action to redirect to dashboard
    continueBtn.onclick = function() {
        window.location.href = '/dashboard/';
    };
    
    modal.classList.add('show');
}

// CSRF token for API calls
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Fetch word definition from Free Dictionary API
async function getDefinition(word) {
    try {
        const response = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${word}`);
        if (!response.ok) {
            return 'Definition not available.';
        }
        const data = await response.json();
        
        if (data && data.length > 0 && data[0].meanings && data[0].meanings.length > 0) {
            const meaning = data[0].meanings[0];
            const definition = meaning.definitions[0].definition;
            const partOfSpeech = meaning.partOfSpeech;
            return `(${partOfSpeech}) ${definition}`;
        }
        return 'Definition not available.';
    } catch (error) {
        console.error('Error fetching definition:', error);
        return 'Definition not available.';
    }
}

// Get the best available voice for natural speech
function getBestVoice() {
    const voices = window.speechSynthesis.getVoices();
    
    // Priority list of high-quality voices (by name and quality)
    const preferredVoices = [
        // Google voices (best quality, available on Chrome/Edge)
        'Google US English',
        'Google UK English Female',
        'Google UK English Male',
        
        // Microsoft voices (good quality, available on Edge/Windows)
        'Microsoft Zira - English (United States)',
        'Microsoft David - English (United States)',
        'Microsoft Mark - English (United States)',
        'Microsoft Aria - English (United States)',
        
        // Apple voices (excellent quality, available on Safari/macOS/iOS)
        'Samantha',
        'Alex',
        'Victoria',
        'Karen',
        'Moira',
        
        // Android voices
        'en-US-Language',
        'English United States'
    ];
    
    // Try to find a preferred voice
    for (const preferredName of preferredVoices) {
        const voice = voices.find(v => v.name.includes(preferredName));
        if (voice) {
            console.log('Using voice:', voice.name);
            return voice;
        }
    }
    
    // Fallback: Find any high-quality en-US voice
    const enUSVoices = voices.filter(v => 
        v.lang === 'en-US' || v.lang.startsWith('en-US')
    );
    
    if (enUSVoices.length > 0) {
        // Prefer "premium" or "enhanced" voices
        const premiumVoice = enUSVoices.find(v => 
            v.name.toLowerCase().includes('premium') ||
            v.name.toLowerCase().includes('enhanced') ||
            v.name.toLowerCase().includes('google') ||
            v.name.toLowerCase().includes('microsoft')
        );
        
        if (premiumVoice) {
            console.log('Using premium voice:', premiumVoice.name);
            return premiumVoice;
        }
        
        console.log('Using fallback voice:', enUSVoices[0].name);
        return enUSVoices[0];
    }
    
    // Last resort: any voice
    console.log('Using default voice:', voices[0]?.name || 'none');
    return voices[0];
}

// Speak word using Web Speech API with best voice
function speakWord(word) {
    if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(word);
        utterance.rate = speechSpeed; // Use slider value
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Use the best available voice
        const bestVoice = getBestVoice();
        if (bestVoice) {
            utterance.voice = bestVoice;
        }
        
        window.speechSynthesis.speak(utterance);
    } else {
        alert('Text-to-speech is not supported in your browser.');
    }
}

// Speak definition using Web Speech API with best voice
function speakDefinition(definition) {
    if ('speechSynthesis' in window) {
        // Remove parentheses and their contents for speech
        const speechText = stripParenthesesForSpeech(definition);
        
        const utterance = new SpeechSynthesisUtterance(speechText);
        utterance.rate = speechSpeed; // Use slider value
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Use the best available voice
        const bestVoice = getBestVoice();
        if (bestVoice) {
            utterance.voice = bestVoice;
        }
        
        window.speechSynthesis.speak(utterance);
    }
}

// Speak word and then definition with best voice
function speakWordAndDefinition(word, definition) {
    if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        
        // Get the best voice once for both utterances
        const bestVoice = getBestVoice();
        
        // First speak the word
        const wordUtterance = new SpeechSynthesisUtterance(word);
        wordUtterance.rate = speechSpeed; // Use slider value
        wordUtterance.pitch = 1.0;
        wordUtterance.volume = 1.0;
        
        if (bestVoice) {
            wordUtterance.voice = bestVoice;
        }
        
        // When word finishes, speak the definition
        wordUtterance.onend = function() {
            // Add a slight pause, then speak definition
            setTimeout(() => {
                // Remove parentheses and their contents for speech
                const speechText = stripParenthesesForSpeech(definition);
                
                const defUtterance = new SpeechSynthesisUtterance(speechText);
                defUtterance.rate = speechSpeed; // Use slider value
                defUtterance.pitch = 1.0;
                defUtterance.volume = 1.0;
                
                if (bestVoice) {
                    defUtterance.voice = bestVoice;
                }
                
                window.speechSynthesis.speak(defUtterance);
            }, 300); // 300ms pause between word and definition
        };
        
        window.speechSynthesis.speak(wordUtterance);
    } else {
        alert('Text-to-speech is not supported in your browser.');
    }
}

// Load voices (needed for some browsers)
if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
    };
}

// Remove parentheses and their contents for TTS (keep for display)
function stripParenthesesForSpeech(text) {
    // Remove anything in parentheses, including the parentheses
    return text.replace(/\s*\([^)]*\)/g, '').trim();
}

// Get next word from API
async function getNextWord() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('word-container').style.display = 'none';
    
    try {
        const response = await fetch('/api/next-word/');
        const data = await response.json();
        
        if (data.game_complete) {
            // Show game completion modal and redirect to dashboard
            showGameCompleteModal(data.message);
            return;
        }
        
        if (data.bucket_complete) {
            showCongratulationsModal(`You completed a bucket! Moving to bucket ${data.new_bucket}`);
            document.getElementById('current-bucket').textContent = data.new_bucket;
            // Get next word from new bucket after modal is closed
            // We'll call getNextWord when the modal button is clicked
            return;
        }
        
        currentWord = data;
        
        // Fetch definition
        wordDefinition = await getDefinition(data.word);
        
        // Reset UI
        document.getElementById('loading').style.display = 'none';
        document.getElementById('word-container').style.display = 'block';
        document.getElementById('spelling-input').value = '';
        document.getElementById('spelling-input').disabled = false;
        document.getElementById('btn-submit').disabled = false;
        document.getElementById('feedback').style.display = 'none';
        document.getElementById('btn-next').style.display = 'none';
        
        // Show definition in box
        // const definitionBox = document.getElementById('definition-box');
        // definitionBox.textContent = wordDefinition;
        // definitionBox.style.display = 'block';
        
        // Automatically speak the word and then the definition
        speakWordAndDefinition(data.word, wordDefinition);
        
        // Focus on input
        document.getElementById('spelling-input').focus();
        
    } catch (error) {
        console.error('Error fetching word:', error);
        alert('Error loading word. Please try again.');
    }
}

// Submit answer
async function submitAnswer() {
    const spelling = document.getElementById('spelling-input').value.trim();
    
    if (!spelling) {
        alert('Please enter a spelling!');
        return;
    }
    
    document.getElementById('btn-submit').disabled = true;
    document.getElementById('spelling-input').disabled = true;
    
    try {
        const response = await fetch('/api/submit-answer/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify({
                word_id: currentWord.word_id,
                spelling: spelling
            })
        });
        
        const data = await response.json();
        
        // Show feedback
        const feedbackEl = document.getElementById('feedback');
        feedbackEl.style.display = 'block';
        
        if (data.correct) {
            feedbackEl.className = 'feedback correct';
            
            // Check if word is mastered or needs more attempts
            if (data.word_correct_count >= data.word_mastery_required) {
                feedbackEl.innerHTML = `✅ Correct! The word is "${data.correct_spelling}"<br>🎉 <strong>Word Mastered!</strong>`;
            } else if (data.word_mastery_required > 1) {
                // Word has been misspelled before, needs multiple attempts
                const attemptsRemaining = data.word_mastery_required - data.word_correct_count;
                feedbackEl.innerHTML = `✅ Correct! The word is "${data.correct_spelling}"<br>📚 Progress: ${data.word_correct_count}/${data.word_mastery_required} - Need ${attemptsRemaining} more to master!`;
            } else {
                // Word never failed, mastered on first attempt
                feedbackEl.innerHTML = `✅ Correct! The word is "${data.correct_spelling}"<br>🎉 <strong>Word Mastered!</strong>`;
            }
            
            // Update stats
            document.getElementById('session-correct').textContent = data.session_correct;
            document.getElementById('session-attempted').textContent = data.session_attempted;
            document.getElementById('bucket-progress').textContent = data.words_mastered;
            document.getElementById('total-correct').textContent = data.total_correct;
            
            // Update bucket progress widget
            if (data.words_mastered !== undefined && data.words_to_complete !== undefined) {
                updateBucketProgress(
                    data.words_mastered, 
                    data.words_to_complete,
                    data.words_need_1,
                    data.words_need_2,
                    data.words_need_3
                );
            }
            
            // Update leaderboard if data is present
            if (data.leaderboard) {
                updateLeaderboard(data.leaderboard);
            }
            
            // Check if game is complete
            if (data.game_complete) {
                setTimeout(() => {
                    showGameCompleteModal(data.message);
                }, 1500);
                return;
            }
            
            // Check if bucket is complete
            if (data.bucket_complete) {
                showCongratulationsModal(`You completed bucket ${currentWord.difficulty_bucket}! Moving to bucket ${data.new_bucket}`);
                document.getElementById('current-bucket').textContent = data.new_bucket;
                return; // Don't auto-load next word, wait for modal to be dismissed
            }
            
            // Automatically load next word after short delay (let student see success)
            setTimeout(() => {
                getNextWord();
            }, 1500); // 1.5 second delay to see the success message
            
        } else {
            feedbackEl.className = 'feedback incorrect';
            feedbackEl.innerHTML = `❌ Incorrect. You spelled: "${spelling}"<br>Correct spelling: "${data.correct_spelling}"`;
            
            // Update stats
            document.getElementById('session-correct').textContent = data.session_correct;
            document.getElementById('session-attempted').textContent = data.session_attempted;
            document.getElementById('bucket-progress').textContent = data.words_mastered;
            document.getElementById('total-correct').textContent = data.total_correct;
            
            // Update bucket progress widget (even on incorrect, attempts count)
            if (data.words_mastered !== undefined && data.words_to_complete !== undefined) {
                updateBucketProgress(
                    data.words_mastered, 
                    data.words_to_complete,
                    data.words_need_1,
                    data.words_need_2,
                    data.words_need_3
                );
            }
            
            // Update leaderboard if data is present
            if (data.leaderboard) {
                updateLeaderboard(data.leaderboard);
            }
            
            // Check if game is complete (unlikely on incorrect answer, but possible)
            if (data.game_complete) {
                setTimeout(() => {
                    showGameCompleteModal(data.message);
                }, 1500);
                return;
            }
            
            // Check if bucket is complete
            if (data.bucket_complete) {
                showCongratulationsModal(`You completed bucket ${currentWord.difficulty_bucket}! Moving to bucket ${data.new_bucket}`);
                document.getElementById('current-bucket').textContent = data.new_bucket;
                return; // Don't show next button, wait for modal to be dismissed
            }
            
            // Show next button for incorrect answers (student needs to review)
            document.getElementById('btn-next').style.display = 'inline-block';
        }
        
    } catch (error) {
        console.error('Error submitting answer:', error);
        alert('Error submitting answer. Please try again.');
        document.getElementById('btn-submit').disabled = false;
        document.getElementById('spelling-input').disabled = false;
    }
}

// Show definition
function showDefinition() {
    const definitionBox = document.getElementById('definition-box');
    definitionBox.textContent = wordDefinition;
    definitionBox.style.display = 'block';
}

// End session
async function endSession() {
    // Show confirmation modal instead of confirm()
    const confirmModal = document.getElementById('end-session-modal');
    confirmModal.classList.add('show');
}

// Handle end session confirmation
async function confirmEndSession() {
    // Hide confirmation modal
    const confirmModal = document.getElementById('end-session-modal');
    confirmModal.classList.remove('show');
    
    try {
        const response = await fetch('/api/end-session/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            }
        });
        
        const data = await response.json();
        
        // Show results modal with session statistics
        const resultsModal = document.getElementById('end-session-results-modal');
        const resultsDiv = document.getElementById('session-results');
        
        resultsDiv.innerHTML = `
            <p><strong>Words Correct:</strong> ${data.words_correct}</p>
            <p><strong>Words Attempted:</strong> ${data.words_attempted}</p>
            <p><strong>Accuracy:</strong> ${data.accuracy.toFixed(1)}%</p>
        `;
        
        resultsModal.classList.add('show');
        
    } catch (error) {
        console.error('Error ending session:', error);
        alert('Error ending session.');
    }
}

// Cancel end session
function cancelEndSession() {
    const confirmModal = document.getElementById('end-session-modal');
    confirmModal.classList.remove('show');
}

// Redirect to dashboard after viewing results
function returnToDashboard() {
    window.location.href = '/dashboard/';
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Modal continue button
    document.getElementById('modal-continue-btn').addEventListener('click', () => {
        closeCongratulationsModal();
        getNextWord();
    });
    
    // End session modal buttons
    document.getElementById('modal-cancel-btn').addEventListener('click', cancelEndSession);
    document.getElementById('modal-confirm-end-btn').addEventListener('click', confirmEndSession);
    document.getElementById('modal-dashboard-btn').addEventListener('click', returnToDashboard);
    
    // Speed slider control
    const speedSlider = document.getElementById('speed-slider');
    const speedValue = document.getElementById('speed-value');
    
    // Load saved speed from localStorage
    const savedSpeed = localStorage.getItem('speechSpeed');
    if (savedSpeed) {
        speechSpeed = parseFloat(savedSpeed);
        speedSlider.value = speechSpeed;
        speedValue.textContent = speechSpeed.toFixed(2) + 'x';
    }
    
    speedSlider.addEventListener('input', function() {
        speechSpeed = parseFloat(this.value);
        speedValue.textContent = speechSpeed.toFixed(2) + 'x';
        
        // Save to localStorage so it persists
        localStorage.setItem('speechSpeed', speechSpeed);
        
        // Optional: speak a sample word when adjusting
        if (currentWord) {
            window.speechSynthesis.cancel(); // Stop current speech
        }
    });
    
    document.getElementById('btn-speak').addEventListener('click', () => {
        if (currentWord && wordDefinition) {
            speakWordAndDefinition(currentWord.word, wordDefinition);
        }
    });
    
    document.getElementById('btn-definition').addEventListener('click', () => {
        if (wordDefinition) {
            speakDefinition(wordDefinition);
        }
    });
    
    document.getElementById('btn-submit').addEventListener('click', submitAnswer);
    
    document.getElementById('btn-next').addEventListener('click', getNextWord);
    
    document.getElementById('btn-end-session').addEventListener('click', endSession);
    
    // Allow Enter key to submit
    document.getElementById('spelling-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !this.disabled) {
            submitAnswer();
        }
    });
    
    // Load first word
    getNextWord();
});
