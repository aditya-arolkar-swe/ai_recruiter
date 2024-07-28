document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const statusElement = document.createElement('p');
    statusElement.id = 'interview-status';
    document.body.insertBefore(statusElement, chatWindow);

    let conversationStarted = false;
    let messages = [];

    const urlParams = new URLSearchParams(window.location.search);
    const candidateId = urlParams.get('id');

    // Check interview status on page load
    fetch(`/interview_status/${candidateId}`)
        .then(response => response.json())
        .then(data => {
            if (data.completed) {
                statusElement.textContent = 'Interview Status: Completed';
                startBtn.disabled = true;
                stopBtn.disabled = true;
                userInput.disabled = true;
            } else if (data.started) {
                statusElement.textContent = 'Interview Status: In Progress';
                startBtn.disabled = true;
                stopBtn.disabled = false;
                userInput.disabled = false;
                conversationStarted = true;
                // You might want to load previous messages here if you're storing them
            } else {
                statusElement.textContent = 'Interview Status: Not Started';
            }
        })
        .catch(error => console.error('Error fetching interview status:', error));

    startBtn.addEventListener('click', () => {
        if (!conversationStarted) {
            fetch(`/start_interview/${candidateId}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        conversationStarted = true;
                        startBtn.disabled = true;
                        stopBtn.disabled = false;
                        userInput.disabled = false;
                        statusElement.textContent = 'Interview Status: In Progress';
                        messages = [
                            {"role": "system", "content": "You are an AI interviewer. Conduct a professional job interview for the position the candidate is applying for. Ask relevant questions, one at a time, and provide feedback or ask follow-up questions based on the candidate's responses."},
                            {"role": "assistant", "content": "Hello! Welcome to your interview. Could you please introduce yourself and tell me which position you're applying for?"}
                        ];
                        appendMessage('AI', messages[1].content);
                    } else {
                        alert(data.message);
                    }
                })
                .catch(error => console.error('Error starting interview:', error));
        }
    });

    stopBtn.addEventListener('click', () => {
        if (conversationStarted) {
            conversationStarted = false;
            startBtn.disabled = true;
            stopBtn.disabled = true;
            userInput.disabled = true;
            appendMessage('AI', 'Thank you for your time. The interview is now complete.');

            // Update the candidate's status
            fetch(`/complete_interview/${candidateId}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log(data.message);
                    if (data.interviewCompleted) {
                        statusElement.textContent = 'Interview Status: Completed';
                    }
                })
                .catch(error => {
                    console.error('Error updating interview status:', error);
                });
        }
    });

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && conversationStarted) {
            const message = userInput.value.trim();
            if (message) {
                appendMessage('You', message);
                messages.push({"role": "user", "content": message});
                userInput.value = '';
                getAIResponse();
            }
        }
    });

    function getAIResponse() {
        fetch('/ai_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({messages: messages}),
        })
        .then(response => response.json())
        .then(data => {
            appendMessage('AI', data.message);
            messages.push({"role": "assistant", "content": data.message});
        })
        .catch((error) => {
            console.error('Error:', error);
            appendMessage('AI', "I'm sorry, I'm having trouble responding right now.");
        });
    }

    function appendMessage(sender, message) {
        const messageElement = document.createElement('p');
        messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});