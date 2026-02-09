document.addEventListener('DOMContentLoaded', () => {
    const questionList = document.getElementById('question-list');
    const subjectSelect = document.getElementById('subject-select');
    const ingestBtn = document.getElementById('ingest-btn');
    const yearSelect = document.getElementById('year-select');
    const topicSelect = document.getElementById('topic-select');
    const searchInput = document.getElementById('search-input');
    const currentTitle = document.getElementById('current-title');
    const sidebarItems = document.querySelectorAll('.sidebar nav li');

    let currentExamType = 'jamb';
    let currentSubject = 'biology';
    let myschoolSubjects = [];

    async function fetchFilters() {
        try {
            const response = await fetch('/filters');
            const data = await response.json();

            // Populate Year Select
            const currentYearValue = yearSelect.value;
            yearSelect.innerHTML = '<option value="">All Years</option>' +
                data.years.map(y => `<option value="${y}" ${y == currentYearValue ? 'selected' : ''}>${y}</option>`).join('');

            // Populate Topic Select
            const currentTopicValue = topicSelect.value;
            topicSelect.innerHTML = '<option value="">All Topics</option>' +
                data.topics.map(t => `<option value="${t}" ${t == currentTopicValue ? 'selected' : ''}>${t}</option>`).join('');
        } catch (error) {
            console.error('Error fetching filters:', error);
        }
    }

    async function fetchSubjects() {
        try {
            subjectSelect.innerHTML = '<option>Loading subjects...</option>';
            const response = await fetch('/myschool-subjects');
            myschoolSubjects = await response.json();

            if (myschoolSubjects.length > 0) {
                subjectSelect.innerHTML = myschoolSubjects.map(sub =>
                    `<option value="${sub.name.toLowerCase()}" data-url="${sub.url}">${sub.name}</option>`
                ).join('');

                subjectSelect.value = 'biology';
                currentSubject = 'biology';
            } else {
                subjectSelect.innerHTML = '<option>No subjects found</option>';
            }
        } catch (error) {
            console.error('Error fetching subjects:', error);
            subjectSelect.innerHTML = '<option>Error loading subjects</option>';
        } finally {
            fetchFilters();
            fetchQuestions();
        }
    }

    async function fetchQuestions() {
        try {
            const year = yearSelect.value;
            const topic = topicSelect.value;
            const url = `/questions?subject=${currentSubject}&exam_type=${currentExamType}${year ? `&year=${year}` : ''}${topic ? `&topic=${encodeURIComponent(topic)}` : ''}`;

            const response = await fetch(url);
            let questions = await response.json();

            const searchTerm = searchInput.value.toLowerCase();
            if (searchTerm) {
                questions = questions.filter(q => q.body.toLowerCase().includes(searchTerm));
            }

            if (questions.length === 0) {
                questionList.innerHTML = '<div class="question-card"><p class="question-text">No questions found matching your filters. Try clicking "Ingest" for more data.</p></div>';
                return;
            }

            questionList.innerHTML = '';
            questions.forEach(q => {
                const card = document.createElement('div');
                card.className = 'question-card';
                card.innerHTML = `
                    <div class="q-meta">${q.exam_type.toUpperCase()} ${q.year || ''} | ${q.topic || 'General'}</div>
                    <p class="question-text">${q.body}</p>
                    <div class="options">
                        ${q.options ? q.options.map((opt, i) => `<div class="option"><strong>${String.fromCharCode(65 + i)}:</strong> ${opt}</div>`).join('') : ''}
                    </div>
                    <button class="toggle-exp" onclick="this.nextElementSibling.classList.toggle('hidden')">Show Explanation</button>
                    <div class="explanation hidden">
                        <strong>Correct Answer: Option ${q.answer}</strong><br><br>
                        ${q.explanation || 'No further explanation provided.'}
                    </div>
                `;
                questionList.appendChild(card);
            });

            currentTitle.innerText = `${currentExamType.toUpperCase()} ${currentSubject.charAt(0).toUpperCase() + currentSubject.slice(1)} Past Questions`;
        } catch (error) {
            console.error('Error fetching questions:', error);
            questionList.innerHTML = '<div class="question-card"><p class="question-text">Error connecting to backend API or loading filters.</p></div>';
        }
    }

    const clearDbBtn = document.getElementById('clear-db-btn');

    async function clearDatabase() {
        if (!confirm('Are you sure you want to delete ALL questions from the database? This cannot be undone.')) return;

        clearDbBtn.disabled = true;
        clearDbBtn.textContent = 'Clearing...';
        try {
            const response = await fetch('/clear-questions');
            const result = await response.json();
            alert(result.message);
            fetchQuestions(); // Refresh UI
        } catch (error) {
            console.error('Error clearing database:', error);
            alert('Failed to clear database');
        } finally {
            clearDbBtn.disabled = false;
            clearDbBtn.textContent = 'Clear DB';
        }
    }

    async function ingestQuestions() {
        const source = document.getElementById('source-select').value;
        const selectedOption = subjectSelect.options[subjectSelect.selectedIndex];

        if (!selectedOption) {
            alert('Please select a subject.');
            return;
        }

        const subjectName = selectedOption.text;

        ingestBtn.disabled = true;
        ingestBtn.textContent = 'Ingesting...';

        try {
            let url;
            if (source === 'myschool') {
                if (!selectedOption.dataset.url) {
                    throw new Error('Subject URL not found for MySchool ingestion.');
                }
                const subjectUrl = selectedOption.dataset.url;
                // Add currentExamType to filter scraper results
                url = `/scrape/myschool?subject_url=${encodeURIComponent(subjectUrl)}&subject_name=${encodeURIComponent(subjectName)}&limit=200&min_year=2000&exam_type=${currentExamType}`;
            } else if (source === 'aloc') {
                url = `/fetch-aloc?subject=${encodeURIComponent(subjectName)}&count=100`;
            }

            const response = await fetch(url);
            const result = await response.json();

            if (!response.ok) {
                if (response.status === 403) {
                    throw new Error("Cloudflare is blocking Render's IP address. Please use the ALOC source for ingestion, or run the app locally to use MySchool.");
                }
                throw new Error(result.detail || 'Ingestion failed');
            }

            alert(result.message);
            fetchFilters();
            fetchQuestions();
        } catch (error) {
            console.error('Error ingesting questions:', error);
            alert(`Attention: ${error.message}`);
        } finally {
            ingestBtn.disabled = false;
            ingestBtn.textContent = 'Ingest Questions';
        }
    }

    // Event Listeners
    sidebarItems.forEach(item => {
        item.addEventListener('click', () => {
            sidebarItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            currentExamType = item.dataset.type;

            // Update title immediately for better responsiveness
            const subjectText = subjectSelect.options[subjectSelect.selectedIndex]?.text || currentSubject;
            currentTitle.innerText = `${currentExamType.toUpperCase()} ${subjectText} Past Questions`;

            fetchQuestions();
        });
    });

    subjectSelect.addEventListener('change', () => {
        currentSubject = subjectSelect.value;
        fetchQuestions();
    });

    yearSelect.addEventListener('change', fetchQuestions);
    topicSelect.addEventListener('change', fetchQuestions);

    ingestBtn.addEventListener('click', ingestQuestions);
    clearDbBtn.addEventListener('click', clearDatabase);
    searchInput.addEventListener('input', fetchQuestions);

    // Initial load
    fetchSubjects();
});
