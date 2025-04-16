document.addEventListener("DOMContentLoaded", function() {
    const queryInput = document.getElementById("query-input");
    const getAnswerButton = document.getElementById("get-answer-btn");
    const chatContainer = document.getElementById("chat-container");
    const uploadForm = document.getElementById("upload-form");
    const fileInput = document.getElementById("file-input");
    const fileName = document.getElementById("file-name");
    const processingDiv = document.getElementById("processing");
    const uploadStatus = document.getElementById("upload-status");
    const loadingSpinner = document.getElementById("loading");

    // Handle the PDF upload form
    uploadForm.addEventListener("submit", function(e) {
        e.preventDefault();
        
        const formData = new FormData(uploadForm);
        
        // Show selected file name and processing spinner
        const selectedFile = fileInput.files[0];
        fileName.textContent = selectedFile.name;
        processingDiv.classList.remove("hidden");
        uploadStatus.classList.add("hidden");

        fetch("/chatbot/upload_pdf", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                processingDiv.classList.add("hidden");  // Hide processing spinner after success
                uploadStatus.classList.remove("hidden"); // Show success message
            } else {
                uploadStatus.classList.add("hidden");
                alert("Error processing PDF.");
                processingDiv.classList.add("hidden");
            }
        })
        .catch(error => {
            console.error("Error uploading PDF:", error);
            processingDiv.classList.add("hidden");
        });
    });

    // Handle the query submission
    getAnswerButton.addEventListener("click", function() {
        const query = queryInput.value.trim();
        if (query) {
            addChatMessage("user", query);
            queryInput.value = ""; // Clear the input field after submission

            // Show loading spinner
            loadingSpinner.style.display = "block";

            fetch(`/chatbot/get_answer?query=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.answer) {
                        addChatMessage("ai", data.answer);
                    }
                })
                .finally(() => {
                    loadingSpinner.style.display = "none"; // Hide loading spinner once the answer is fetched
                });
        }
    });

    // Add chat message to the chat container
    function addChatMessage(type, message) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add(type === "user" ? "user-question" : "ai-answer");
        messageDiv.textContent = type === "user" ? "🧑 Question: " + message : "🤖 AI: " + message;
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
