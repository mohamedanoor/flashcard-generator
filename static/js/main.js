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
    const form = document.getElementById('flashcard-form');
    const topicForm = document.getElementById('topic-form');
    const textSelector = document.getElementById('text-selector');
    const topicSelector = document.getElementById('topic-selector');
    const textInputContainer = document.getElementById('text-input-container');
    const topicInputContainer = document.getElementById('topic-input-container');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const flashcardContainer = document.getElementById('flashcard-container');
    const saveBtn = document.getElementById('save-btn');
    const startStudyBtn = document.getElementById('start-study-btn');
    
    // Store generated flashcards
    let currentFlashcards = [];
    
    // Toggle between text and topic input
    textSelector.addEventListener('click', function() {
        textSelector.classList.add('active');
        topicSelector.classList.remove('active');
        textInputContainer.style.display = 'block';
        topicInputContainer.style.display = 'none';
    });
    
    topicSelector.addEventListener('click', function() {
        topicSelector.classList.add('active');
        textSelector.classList.remove('active');
        topicInputContainer.style.display = 'block';
        textInputContainer.style.display = 'none';
    });
    
    // Text form submission handler
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const textInput = document.getElementById('text-input').value.trim();
        
        if (!textInput) {
            alert('Please enter some text to generate flashcards.');
            return;
        }
        
        // Show loading spinner
        loadingSection.style.display = 'block';
        resultsSection.style.display = 'none';
        
        // Send text to server for processing
        const formData = new FormData();
        formData.append('text_input', textInput);
        
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
            currentFlashcards = data.flashcards;
            
            // Display flashcards
            displayFlashcards(currentFlashcards);
            
            // Show results section
            resultsSection.style.display = 'block';
        })
        .catch(error => {
            loadingSection.style.display = 'none';
            alert('Error generating flashcards: ' + error.message);
        });
    });
    
    // Topic form submission handler
    topicForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const topicInput = document.getElementById('topic-input').value.trim();
        
        if (!topicInput) {
            alert('Please enter a topic to generate flashcards.');
            return;
        }
        
        // Show loading spinner
        loadingSection.style.display = 'block';
        resultsSection.style.display = 'none';
        
        // Send topic to server for processing
        const formData = new FormData();
        formData.append('topic_input', topicInput);
        
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
            currentFlashcards = data.flashcards;
            
            // Display flashcards
            displayFlashcards(currentFlashcards);
            
            // Show results section
            resultsSection.style.display = 'block';
        })
        .catch(error => {
            loadingSection.style.display = 'none';
            alert('Error generating flashcards: ' + error.message);
        });
    });
    
    // Function to display flashcards
    function displayFlashcards(flashcards) {
        flashcardContainer.innerHTML = '';
        
        flashcards.forEach((card, index) => {
            const flashcardElement = document.createElement('div');
            flashcardElement.className = 'flashcard';
            flashcardElement.innerHTML = `
                <div class="flashcard-inner">
                    <div class="flashcard-front">
                        <p>${card.question}</p>
                    </div>
                    <div class="flashcard-back">
                        <p>${card.answer}</p>
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
    saveBtn.addEventListener('click', function() {
        if (currentFlashcards.length === 0) {
            alert('No flashcards to save!');
            return;
        }
        
        localStorage.setItem('savedFlashcards', JSON.stringify(currentFlashcards));
        alert('Flashcards saved successfully!');
    });
    
    // Start studying button
    startStudyBtn.addEventListener('click', function() {
        if (currentFlashcards.length === 0) {
            alert('No flashcards to study!');
            return;
        }
        
        localStorage.setItem('studyFlashcards', JSON.stringify(currentFlashcards));
        window.location.href = '/flashcards';
    });
}

function setupStudyPage() {
    const studyCard = document.getElementById('study-card');
    const questionText = document.getElementById('question-text');
    const answerText = document.getElementById('answer-text');
    const startBtn = document.getElementById('start-btn');
    const flipBtn = document.getElementById('flip-btn');
    const nextBtn = document.getElementById('next-btn');
    const progressText = document.getElementById('progress-text');
    
    let flashcards = [];
    let currentCardIndex = 0;
    let isFlipped = false;
    
    // Load flashcards from localStorage
    function loadFlashcards() {
        const savedCards = localStorage.getItem('studyFlashcards');
        if (savedCards) {
            flashcards = JSON.parse(savedCards);
            progressText.textContent = `0/${flashcards.length}`;
            return true;
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
        flipBtn.disabled = false;
        nextBtn.disabled = false;
        
        // Show first card
        showCard(0);
    });
    
    // Flip button handler
    flipBtn.addEventListener('click', function() {
        toggleFlip();
    });
    
    // Next button handler
    nextBtn.addEventListener('click', function() {
        if (isFlipped) {
            toggleFlip();
        }
        
        if (currentCardIndex < flashcards.length - 1) {
            showCard(currentCardIndex + 1);
        } else {
            // End of deck
            questionText.textContent = "End of flashcards!";
            answerText.textContent = "";
            nextBtn.disabled = true;
            flipBtn.disabled = true;
            startBtn.disabled = false;
            startBtn.textContent = "Restart";
        }
    });
    
    // Function to show a specific card
    function showCard(index) {
        currentCardIndex = index;
        questionText.textContent = flashcards[index].question;
        answerText.textContent = flashcards[index].answer;
        progressText.textContent = `${index + 1}/${flashcards.length}`;
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
}