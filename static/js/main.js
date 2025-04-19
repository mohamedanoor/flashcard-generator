document.addEventListener('DOMContentLoaded', function() {
    // Check which page we're on
    const isHomePage = document.getElementById('flashcard-form') !== null;
    const isStudyPage = document.getElementById('study-card') !== null;
    
    if (isHomePage) {
        setupHomePage();
    } else if (isStudyPage) {
        setupStudyPage();
    }
});

function setupHomePage() {
    // Form elements
    const textForm = document.getElementById('flashcard-form');
    const topicForm = document.getElementById('topic-form');
    const fileForm = document.getElementById('file-form');
    
    // Tab selectors
    const textSelector = document.getElementById('text-selector');
    const topicSelector = document.getElementById('topic-selector');
    const fileSelector = document.getElementById('file-selector');
    
    // Input containers
    const textInputContainer = document.getElementById('text-input-container');
    const topicInputContainer = document.getElementById('topic-input-container');
    const fileInputContainer = document.getElementById('file-input-container');
    
    // Results elements
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const flashcardContainer = document.getElementById('flashcard-container');
    
    // Button elements
    const saveBtn = document.getElementById('save-btn');
    const startStudyBtn = document.getElementById('start-study-btn');
    const editBtn = document.getElementById('edit-btn');
    
    // Deck tabs
    const deckTabs = document.getElementById('deck-tabs')?.querySelectorAll('.tab-item');
    
    // Format options
    const formatOptions = document.querySelectorAll('.format-option');
    
    // Difficulty options
    const difficultyOptions = document.querySelectorAll('.difficulty-option');
    
    // File upload zone
    const fileUploadZone = document.getElementById('file-upload-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    
    // Store generated flashcards
    let currentFlashcards = [];
    let currentFormat = 'plain';
    let currentDifficulty = 'easy';
    let uploadedFiles = [];
    
    // Toggle between input types
    if (textSelector) {
        textSelector.addEventListener('click', function() {
            setActiveTab(textSelector, [topicSelector, fileSelector]);
            showContainer(textInputContainer, [topicInputContainer, fileInputContainer]);
        });
    }
    
    if (topicSelector) {
        topicSelector.addEventListener('click', function() {
            setActiveTab(topicSelector, [textSelector, fileSelector]);
            showContainer(topicInputContainer, [textInputContainer, fileInputContainer]);
        });
    }
    
    if (fileSelector) {
        fileSelector.addEventListener('click', function() {
            setActiveTab(fileSelector, [textSelector, topicSelector]);
            showContainer(fileInputContainer, [textInputContainer, topicInputContainer]);
        });
    }
    
    // Toggle format options
    formatOptions.forEach(option => {
        option.addEventListener('click', function() {
            formatOptions.forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
            currentFormat = this.getAttribute('data-format');
            
            // Change placeholder based on format
            const textInput = document.getElementById('text-input');
            if (currentFormat === 'plain') {
                textInput.placeholder = 'Paste your text here...';
            } else if (currentFormat === 'markdown') {
                textInput.placeholder = 'Paste markdown content here...';
            } else if (currentFormat === 'url') {
                textInput.placeholder = 'Enter a URL (e.g., https://example.com/article)';
            }
        });
    });
    
    // Toggle difficulty options
    difficultyOptions.forEach(option => {
        option.addEventListener('click', function() {
            const parent = this.parentElement;
            parent.querySelectorAll('.difficulty-option').forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
            currentDifficulty = this.getAttribute('data-level');
        });
    });
    
    // File upload functionality
    if (fileUploadZone) {
        fileUploadZone.addEventListener('click', function() {
            fileInput.click();
        });
        
        fileUploadZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.borderColor = '#9b59b6';
            this.style.backgroundColor = 'rgba(142, 68, 173, 0.1)';
        });
        
        fileUploadZone.addEventListener('dragleave', function() {
            this.style.borderColor = '';
            this.style.backgroundColor = '';
        });
        
        fileUploadZone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.style.borderColor = '';
            this.style.backgroundColor = '';
            
            const files = e.dataTransfer.files;
            handleFiles(files);
        });
        
        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });
    }
    
    function handleFiles(files) {
        uploadedFiles = Array.from(files);
        
        // Clear previous file list
        fileList.innerHTML = '';
        
        // Display file list
        uploadedFiles.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <span>${file.name}</span>
                <span class="file-size">(${formatFileSize(file.size)})</span>
                <button class="remove-file" data-name="${file.name}">×</button>
            `;
            fileList.appendChild(fileItem);
        });
        
        // Add event listeners to remove buttons
        document.querySelectorAll('.remove-file').forEach(btn => {
            btn.addEventListener('click', function() {
                const fileName = this.getAttribute('data-name');
                uploadedFiles = uploadedFiles.filter(file => file.name !== fileName);
                this.parentElement.remove();
            });
        });
    }
    
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' bytes';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    }
    
    // Text form submission
    if (textForm) {
        textForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const textInput = document.getElementById('text-input').value.trim();
            
            if (!textInput) {
                alert('Please enter some text to generate flashcards.');
                return;
            }
            
            // Get options
            const extractDefinitions = document.getElementById('extract-definitions')?.checked || false;
            const createCloze = document.getElementById('create-cloze')?.checked || false;
            const questionAnswer = document.getElementById('question-answer')?.checked || true;
            
            // Show loading spinner
            loadingSection.style.display = 'block';
            resultsSection.style.display = 'none';
            
            // Send text to server for processing
            const formData = new FormData();
            formData.append('text_input', textInput);
            formData.append('format', currentFormat);
            formData.append('difficulty', currentDifficulty);
            formData.append('extract_definitions', extractDefinitions);
            formData.append('create_cloze', createCloze);
            formData.append('question_answer', questionAnswer);
            
            fetch('/generate', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Server error');
                }
                return response.json();
            })
            .then(data => {
                // Hide loading spinner
                loadingSection.style.display = 'none';
                
                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }
                
                // Store the flashcards
                currentFlashcards = data.flashcards || [];
                
                // Display flashcards
                displayFlashcards(currentFlashcards);
                
                // Show results section
                resultsSection.style.display = 'block';
                
                // Set up deck tabs
                setupDeckTabs(data);
            })
            .catch(error => {
                loadingSection.style.display = 'none';
                alert('Error generating flashcards: ' + error.message);
            });
        });
    }
    
    // Topic form submission
    if (topicForm) {
        topicForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const topicInput = document.getElementById('topic-input').value.trim();
            
            if (!topicInput) {
                alert('Please enter a topic to generate flashcards.');
                return;
            }
            
            // Get options
            const includeDefinitions = document.getElementById('topic-definitions')?.checked || true;
            const includeFacts = document.getElementById('topic-facts')?.checked || true;
            const includeDates = document.getElementById('topic-dates')?.checked || false;
            
            // Show loading spinner
            loadingSection.style.display = 'block';
            resultsSection.style.display = 'none';
            
            // Send topic to server for processing
            const formData = new FormData();
            formData.append('topic_input', topicInput);
            formData.append('difficulty', currentDifficulty);
            formData.append('include_definitions', includeDefinitions);
            formData.append('include_facts', includeFacts);
            formData.append('include_dates', includeDates);
            
            fetch('/generate_from_topic', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Server error');
                }
                return response.json();
            })
            .then(data => {
                // Hide loading spinner
                loadingSection.style.display = 'none';
                
                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }
                
                // Store the flashcards
                currentFlashcards = data.flashcards || [];
                
                // Display flashcards
                displayFlashcards(currentFlashcards);
                
                // Show results section
                resultsSection.style.display = 'block';
                
                // Set up deck tabs
                setupDeckTabs(data);
            })
            .catch(error => {
                loadingSection.style.display = 'none';
                alert('Error generating flashcards: ' + error.message);
            });
        });
    }
    
    // File form submission
    if (fileForm) {
        fileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (uploadedFiles.length === 0) {
                alert('Please upload at least one file.');
                return;
            }
            
            // Get options
            const extractAll = document.getElementById('file-extract-all')?.checked || true;
            const useOcr = document.getElementById('file-ocr')?.checked || false;
            
            // Show loading spinner
            loadingSection.style.display = 'block';
            resultsSection.style.display = 'none';
            
            // Send files to server for processing
            const formData = new FormData();
            uploadedFiles.forEach(file => {
                formData.append('files', file);
            });
            formData.append('extract_all', extractAll);
            formData.append('use_ocr', useOcr);
            formData.append('difficulty', currentDifficulty);
            
            fetch('/generate_from_files', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Server error');
                }
                return response.json();
            })
            .then(data => {
                // Hide loading spinner
                loadingSection.style.display = 'none';
                
                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }
                
                // Store the flashcards
                currentFlashcards = data.flashcards || [];
                
                // Display flashcards
                displayFlashcards(currentFlashcards);
                
                // Show results section
                resultsSection.style.display = 'block';
                
                // Set up deck tabs
                setupDeckTabs(data);
            })
            .catch(error => {
                loadingSection.style.display = 'none';
                alert('Error generating flashcards: ' + error.message);
            });
        });
    }
    
    // Setup deck tabs
    function setupDeckTabs(data) {
        if (!deckTabs) return;
        
        // Show/hide tabs based on available data
        deckTabs.forEach(tab => {
            const deckType = tab.getAttribute('data-deck');
            if (data[deckType] && data[deckType].length > 0) {
                tab.style.display = 'block';
            } else {
                tab.style.display = 'none';
            }
        });
        
        // Set first visible tab as active
        const visibleTabs = Array.from(deckTabs).filter(tab => tab.style.display !== 'none');
        if (visibleTabs.length > 0) {
            deckTabs.forEach(tab => tab.classList.remove('active'));
            visibleTabs[0].classList.add('active');
        }
    }
    
    // Handle deck tab clicks
    if (deckTabs) {
        deckTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                deckTabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                const deckType = this.getAttribute('data-deck');
                displayFlashcards(currentFlashcards, deckType);
            });
        });
    }
    
    // Function to display flashcards
    function displayFlashcards(flashcards, deckType = 'main') {
        flashcardContainer.innerHTML = '';
        
        // Filter flashcards based on deck type if needed
        let cardsToDisplay = flashcards;
        if (deckType === 'definitions' && flashcards.definitions) {
            cardsToDisplay = flashcards.definitions;
        } else if (deckType === 'cloze' && flashcards.cloze) {
            cardsToDisplay = flashcards.cloze;
        } else if (flashcards.main) {
            cardsToDisplay = flashcards.main;
        }
        
        // Handle array of cards or object with card types
        if (!Array.isArray(cardsToDisplay)) {
            if (cardsToDisplay.main) {
                cardsToDisplay = cardsToDisplay.main;
            } else {
                cardsToDisplay = [];
            }
        }
        
        if (cardsToDisplay.length === 0) {
            flashcardContainer.innerHTML = '<p style="text-align: center; color: var(--dark-gray);">No flashcards found for this section.</p>';
            return;
        }
        
        cardsToDisplay.forEach((card, index) => {
            const flashcardElement = document.createElement('div');
            flashcardElement.className = 'flashcard';
            flashcardElement.innerHTML = `
                <div class="flashcard-inner">
                    <div class="flashcard-front">
                        <p>${card.question || card.front}</p>
                    </div>
                    <div class="flashcard-back">
                        <p>${card.answer || card.back}</p>
                    </div>
                </div>
            `;
            
            // Add click event to flip the card
            flashcardElement.addEventListener('click', function() {
                this.classList.toggle('flipped');
            });
            
            flashcardContainer.appendChild(flashcardElement);
        });
    }
    
    // Save flashcards to localStorage
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            if (!currentFlashcards || (Array.isArray(currentFlashcards) && currentFlashcards.length === 0)) {
                alert('No flashcards to save!');
                return;
            }
            
            // Create a deck object with metadata
            const deck = {
                cards: currentFlashcards,
                title: prompt('Enter a name for this deck:', 'My Flashcards'),
                created: new Date().toISOString(),
                lastStudied: null
            };
            
            // Get existing decks or initialize empty array
            const existingDecks = JSON.parse(localStorage.getItem('savedDecks')) || [];
            
            // Add new deck
            existingDecks.push(deck);
            
            // Save back to localStorage
            localStorage.setItem('savedDecks', JSON.stringify(existingDecks));
            localStorage.setItem('studyFlashcards', JSON.stringify(currentFlashcards));
            
            alert('Flashcards saved successfully!');
        });
    }
    
    // Start studying button
    if (startStudyBtn) {
        startStudyBtn.addEventListener('click', function() {
            if (!currentFlashcards || (Array.isArray(currentFlashcards) && currentFlashcards.length === 0)) {
                alert('No flashcards to study!');
                return;
            }
            
            localStorage.setItem('studyFlashcards', JSON.stringify(currentFlashcards));
            window.location.href = '/flashcards';
        });
    }
    
    // Edit flashcards button
    if (editBtn) {
        editBtn.addEventListener('click', function() {
            alert('Edit mode is coming soon!');
        });
    }
    
    // Helper function to set active tab
    function setActiveTab(activeTab, inactiveTabs) {
        activeTab.classList.add('active');
        inactiveTabs.forEach(tab => tab.classList.remove('active'));
    }
    
    // Helper function to show container
    function showContainer(containerToShow, containersToHide) {
        containerToShow.style.display = 'block';
        containersToHide.forEach(container => container.style.display = 'none');
    }
}

function setupStudyPage() {
    const studyCard = document.getElementById('study-card');
    const questionText = document.getElementById('question-text');
    const answerText = document.getElementById('answer-text');
    const startBtn = document.getElementById('start-btn');
    const flipBtn = document.getElementById('flip-btn');
    const nextBtn = document.getElementById('next-btn');
    const progressText = document.getElementById('progress-text');
    
    // Study mode selectors
    const flashcardMode = document.getElementById('flashcard-mode');
    const quizMode = document.getElementById('quiz-mode');
    const writeMode = document.getElementById('write-mode');
    
    // Self assessment
    const selfAssessment = document.getElementById('self-assessment');
    const hardBtn = document.getElementById('hard-btn');
    const mediumBtn = document.getElementById('medium-btn');
    const easyBtn = document.getElementById('easy-btn');
    
    // Quiz mode elements (created dynamically)
    let quizOptions = null;
    
    // Written mode elements (created dynamically)
    let answerInput = null;
    let checkAnswerBtn = null;
    
    // Analytics
    const statValues = document.querySelectorAll('.stat-value');
    
    let flashcards = [];
    let currentCardIndex = 0;
    let isFlipped = false;
    let studyStartTime = null;
    let currentStudyMode = 'flashcard';
    let studyStats = {
        cardsReviewed: 0,
        correct: 0,
        timeSpent: 0,
        streak: 0
    };
    
    // Toggle between study modes
    flashcardMode.addEventListener('click', function() {
        setActiveTab(flashcardMode, [quizMode, writeMode]);
        switchStudyMode('flashcard');
    });
    
    quizMode.addEventListener('click', function() {
        setActiveTab(quizMode, [flashcardMode, writeMode]);
        switchStudyMode('quiz');
    });
    
    writeMode.addEventListener('click', function() {
        setActiveTab(writeMode, [flashcardMode, quizMode]);
        switchStudyMode('write');
    });
    
    // Function to switch study modes
    function switchStudyMode(mode) {
        currentStudyMode = mode;
        
        // Reset card state
        if (isFlipped) {
            toggleFlip();
        }
        
        // Clear any existing UI elements
        clearStudyModeElements();
        
        // Update UI based on mode
        if (mode === 'quiz') {
            flipBtn.style.display = 'none';
            setupQuizMode();
        } else if (mode === 'write') {
            flipBtn.style.display = 'none';
            setupWrittenMode();
        } else {
            // Default flashcard mode
            flipBtn.style.display = 'inline-block';
        }
        
        // Redisplay current card if we're already studying
        if (flashcards.length > 0 && !startBtn.disabled) {
            showCard(currentCardIndex);
        }
    }
    
    // Setup quiz mode UI
    function setupQuizMode() {
        // Create quiz options container if it doesn't exist
        if (!quizOptions) {
            quizOptions = document.createElement('div');
            quizOptions.className = 'quiz-options';
            quizOptions.style.display = 'none';
            
            // Add after the study card
            studyCard.parentNode.insertBefore(quizOptions, studyCard.nextSibling);
        }
    }
    
    // Setup written mode UI
    function setupWrittenMode() {
        // Create answer input and check button if they don't exist
        if (!answerInput) {
            const inputContainer = document.createElement('div');
            inputContainer.className = 'written-answer-container';
            inputContainer.style.marginTop = '20px';
            inputContainer.style.display = 'none';
            
            answerInput = document.createElement('input');
            answerInput.type = 'text';
            answerInput.className = 'written-answer-input';
            answerInput.placeholder = 'Type your answer here...';
            
            checkAnswerBtn = document.createElement('button');
            checkAnswerBtn.textContent = 'Check Answer';
            checkAnswerBtn.className = 'check-answer-btn';
            
            // Bind the check answer functionality
            checkAnswerBtn.addEventListener('click', checkWrittenAnswer);
            
            // Add to the container
            inputContainer.appendChild(answerInput);
            inputContainer.appendChild(checkAnswerBtn);
            
            // Add after the study card
            studyCard.parentNode.insertBefore(inputContainer, studyCard.nextSibling);
        }
    }
    
    // Clear any special study mode elements
    function clearStudyModeElements() {
        if (quizOptions) {
            quizOptions.style.display = 'none';
        }
        
        if (answerInput) {
            answerInput.parentNode.style.display = 'none';
        }
        
        selfAssessment.style.display = 'none';
    }
    
    // Generate quiz options for current card
    function generateQuizOptions() {
        if (!quizOptions) return;
        
        quizOptions.innerHTML = '';
        quizOptions.style.display = 'block';
        quizOptions.className = 'quiz-options';
        
        const correctAnswer = flashcards[currentCardIndex].answer;
        
        // Generate 3 incorrect options
        let options = [correctAnswer];
        
        // Add other flashcard answers as wrong answers
        for (let i = 0; i < flashcards.length; i++) {
            if (i !== currentCardIndex && options.length < 4) {
                options.push(flashcards[i].answer);
            }
        }
        
        // If we don't have enough options, add some generic wrong answers
        while (options.length < 4) {
            options.push(`Another possible answer ${options.length}`);
        }
        
        // Shuffle the options
        shuffleArray(options);
        
        // Create option buttons
        options.forEach(option => {
            const optionElement = document.createElement('div');
            optionElement.className = 'quiz-option';
            optionElement.textContent = option;
            
            // Check if the option is correct
            optionElement.addEventListener('click', function() {
                if (optionElement.classList.contains('disabled')) return;
                
                const isCorrect = option === correctAnswer;
                
                // Mark this option as selected
                optionElement.classList.add('selected');
                
                // Style based on correctness
                if (isCorrect) {
                    optionElement.classList.add('correct');
                    studyStats.correct++;
                } else {
                    optionElement.classList.add('incorrect');
                    
                    // Highlight the correct answer
                    const options = quizOptions.querySelectorAll('.quiz-option');
                    options.forEach(opt => {
                        if (opt.textContent === correctAnswer) {
                            opt.classList.add('correct');
                        }
                    });
                }
                
                // Disable all options after selection
                const options = quizOptions.querySelectorAll('.quiz-option');
                options.forEach(opt => {
                    opt.classList.add('disabled');
                });
                
                // Show next button
                nextBtn.disabled = false;
                
                // Update stats
                studyStats.cardsReviewed++;
                updateStudyStats();
            });
            
            quizOptions.appendChild(optionElement);
        });
    }
    
    // Check written answer
    function checkWrittenAnswer() {
        const userAnswer = answerInput.value.trim().toLowerCase();
        const correctAnswer = flashcards[currentCardIndex].answer.toLowerCase();
        
        // Simple string comparison - could be enhanced with fuzzy matching
        const isCorrect = userAnswer === correctAnswer;
        
        // Show the correct answer
        if (isFlipped) {
            toggleFlip();
        }
        toggleFlip(); // Flip to show the answer
        
        // Style the input based on correctness
        if (isCorrect) {
            answerInput.style.borderColor = '#2ecc71';
            answerInput.style.backgroundColor = 'rgba(46, 204, 113, 0.1)';
            studyStats.correct++;
        } else {
            answerInput.style.borderColor = '#e74c3c';
            answerInput.style.backgroundColor = 'rgba(231, 76, 60, 0.1)';
        }
        
        // Disable input after submission
        answerInput.disabled = true;
        checkAnswerBtn.disabled = true;
        
        // Enable next button
        nextBtn.disabled = false;
        
        // Update stats
        studyStats.cardsReviewed++;
        updateStudyStats();
    }
    
    // Load flashcards from localStorage
    function loadFlashcards() {
        const savedCards = localStorage.getItem('studyFlashcards');
        if (savedCards) {
            let parsed = JSON.parse(savedCards);
            
            // Handle different formats
            if (Array.isArray(parsed)) {
                flashcards = parsed;
            } else if (parsed.main) {
                flashcards = parsed.main;
            } else if (parsed.cards && Array.isArray(parsed.cards)) {
                flashcards = parsed.cards;
            }
            
            // Ensure each card has the expected properties
            flashcards = flashcards.map(card => {
                return {
                    question: card.question || card.front,
                    answer: card.answer || card.back
                };
            });
            
            progressText.textContent = `0/${flashcards.length}`;
            return flashcards.length > 0;
        }
        return false;
    }
    
    // Start button handler
    startBtn.addEventListener('click', function() {
        if (!loadFlashcards()) {
            alert('No flashcards found! Please generate and save flashcards first.');
            return;
        }
        
        startBtn.disabled = true;
        if (currentStudyMode === 'flashcard') {
            flipBtn.disabled = false;
        }
        nextBtn.disabled = false;
        
        // Shuffle the flashcards
        shuffleArray(flashcards);
        
        // Show first card
        showCard(0);
        
        // Start timer
        studyStartTime = new Date();
        updateStudyStats();
        
        // Start timer for updating study time
        setInterval(updateStudyTime, 60000); // Update every minute
    });
    
    // Flip button handler
    flipBtn.addEventListener('click', function() {
        toggleFlip();
        
        // Show self assessment after flip
        if (isFlipped) {
            selfAssessment.style.display = 'block';
        } else {
            selfAssessment.style.display = 'none';
        }
    });
    
    // Self assessment buttons
    hardBtn.addEventListener('click', function() {
        recordAssessment('hard');
        nextCard();
    });
    
    mediumBtn.addEventListener('click', function() {
        recordAssessment('medium');
        nextCard();
    });
    
    easyBtn.addEventListener('click', function() {
        recordAssessment('easy');
        nextCard();
    });
    
    // Next button handler
    nextBtn.addEventListener('click', function() {
        nextCard();
    });
    
    function nextCard() {
        if (isFlipped) {
            toggleFlip();
        }
        
        // Hide assessment UI
        selfAssessment.style.display = 'none';
        
        // Reset UI for next card
        if (currentStudyMode === 'quiz') {
            quizOptions.style.display = 'none';
            nextBtn.disabled = true;
        } else if (currentStudyMode === 'write') {
            // Reset written mode
            if (answerInput) {
                answerInput.value = '';
                answerInput.disabled = false;
                answerInput.style.borderColor = '';
                answerInput.style.backgroundColor = '';
                checkAnswerBtn.disabled = false;
                nextBtn.disabled = true;
            }
        }
        
        if (currentCardIndex < flashcards.length - 1) {
            showCard(currentCardIndex + 1);
        } else {
            // End of deck
            questionText.textContent = "You've completed the deck!";
            answerText.textContent = "";
            nextBtn.disabled = true;
            flipBtn.disabled = true;
            startBtn.disabled = false;
            startBtn.textContent = "Restart";
            
            // Hide any mode-specific elements
            clearStudyModeElements();
            
            // Update stats for completion
            studyStats.streak++;
            updateStudyStats();
        }
    }
    
    // Record user's self assessment
    function recordAssessment(level) {
        studyStats.cardsReviewed++;
        
        if (level === 'easy') {
            studyStats.correct++;
        }
        
        updateStudyStats();
    }
    
    // Function to show a specific card
    function showCard(index) {
        currentCardIndex = index;
        questionText.textContent = flashcards[index].question;
        answerText.textContent = flashcards[index].answer;
        progressText.textContent = `${index + 1}/${flashcards.length}`;
        
        // Mode-specific setup
        if (currentStudyMode === 'quiz') {
            generateQuizOptions();
        } else if (currentStudyMode === 'write') {
            if (answerInput && answerInput.parentNode) {
                answerInput.parentNode.style.display = 'block';
            }
        }
    }
    
    // Function to toggle card flip
    function toggleFlip() {
        isFlipped = !isFlipped;
        if (isFlipped) {
            studyCard.querySelector('.flashcard-inner').style.transform = 'rotateY(180deg)';
        } else {
            studyCard.querySelector('.flashcard-inner').style.transform = 'rotateY(0deg)';
        }
    }
    
    // Update study statistics
    function updateStudyStats() {
        // Calculate accuracy
        const accuracy = studyStats.cardsReviewed > 0 
            ? Math.round((studyStats.correct / studyStats.cardsReviewed) * 100) 
            : 0;
        
        // Update the stats display
        if (statValues.length >= 4) {
            statValues[0].textContent = studyStats.cardsReviewed;
            statValues[1].textContent = accuracy + '%';
            statValues[2].textContent = studyStats.timeSpent;
            statValues[3].textContent = studyStats.streak;
        }
    }
    
    // Update study time
    function updateStudyTime() {
        if (studyStartTime) {
            const now = new Date();
            const diffInMs = now - studyStartTime;
            const diffInMins = Math.floor(diffInMs / 60000);
            studyStats.timeSpent = diffInMins;
            updateStudyStats();
        }
    }
    
    // Shuffle array (Fisher-Yates algorithm)
    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }
    
    // Helper function to set active tab
    function setActiveTab(activeTab, inactiveTabs) {
        activeTab.classList.add('active');
        inactiveTabs.forEach(tab => tab.classList.remove('active'));
    }
}