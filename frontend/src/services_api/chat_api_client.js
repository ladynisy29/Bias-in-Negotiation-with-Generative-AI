document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('send-btn');
    const messageInput = document.getElementById('message-input');
    const offerInput = document.getElementById('offer-input');
    const chatHistory = document.getElementById('chat-history');
    const offerTbody = document.getElementById('offer-tbody');
    const turnCounter = document.getElementById('turn-counter');

    let currentTurn = 0;
    const MAX_TURNS = 5;

    sendBtn.addEventListener('click', async () => {
        const message = messageInput.value.trim();
        const offer = parseFloat(offerInput.value);

        if (!message || isNaN(offer)) {
            alert("Please provide both an offer and a message.");
            return;
        }

        if (currentTurn >= MAX_TURNS) {
            alert("The negotiation has reached its maximum limit of 5 turns.");
            return;
        }

        currentTurn++;
        updateTurnCounter();

        // 1. Display Human Message
        appendMessage(message, 'human-message');
        
        // Disable inputs while waiting for AI
        toggleInputs(true);

        try {
            // Requête vers la future API locale du backend
            const response = await fetch('http://127.0.0.1:8000/api/negotiate/', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    turn: currentTurn,
                    message: message,
                    offer: offer
                })
            });

            if (!response.ok) throw new Error("Network response was not ok");

            const data = await response.json();
            
            // 2. Display AI Message
            appendMessage(data.message, 'ai-message');
            
            // 3. Update Offer Tracker
            updateTracker(currentTurn, offer, data.interpreted_offer);

            if (currentTurn === MAX_TURNS) {
                appendMessage("This was the final turn. The AI will now evaluate your final offer.", 'ai-message');
                toggleInputs(true); // Keep disabled after turn 5
            } else {
                toggleInputs(false);
            }

        } catch (error) {
            console.error("Error during API call:", error);
            appendMessage("Connection error with the negotiation server.", 'ai-message');
            toggleInputs(false);
            currentTurn--; // Revert turn count on error
            updateTurnCounter();
        }

        // Clear inputs
        messageInput.value = '';
        offerInput.value = '';
    });

    function appendMessage(text, className) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${className}`;
        msgDiv.innerHTML = `<p>${text}</p>`;
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function updateTracker(turn, humanOffer, aiOffer) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${turn}</td>
            <td>$${humanOffer.toLocaleString()}</td>
            <td>$${aiOffer.toLocaleString()}</td>
        `;
        offerTbody.appendChild(row);
    }

    function updateTurnCounter() {
        turnCounter.innerText = `Turn: ${currentTurn} / ${MAX_TURNS}`;
    }

    function toggleInputs(disabled) {
        messageInput.disabled = disabled;
        offerInput.disabled = disabled;
        sendBtn.disabled = disabled;
    }
});