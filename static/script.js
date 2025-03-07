document.addEventListener("DOMContentLoaded", () => {
    const uploadBtn = document.getElementById("upload-btn");
    const imageInput = document.getElementById("image-input");
    const faceResult = document.getElementById("face-result");
    const imagePreview = document.getElementById("image-preview");
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

    imageInput.addEventListener("change", (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = () => {
                imagePreview.src = reader.result;
                imagePreview.style.display = "block"; // Show Image Preview
            };
            reader.readAsDataURL(file);
        }
    });

    uploadBtn.addEventListener("click", async () => {
        const file = imageInput.files[0];
        if (!file) {
            faceResult.innerHTML = "<p style='color: red;'>Please select an image.</p>";
            return;
        }

        faceResult.innerHTML = "<p style='color: blue;'>Processing image, please wait...</p>";

        const formData = new FormData();
        formData.append("image", file);

        try {
            const response = await fetch("/face", { method: "POST", body: formData });
            const data = await response.json();

            if (data.error) {
                faceResult.innerHTML = `<p style='color: red;'>${data.error}</p>`;
                return;
            }

            faceResult.innerHTML = `
                <div class="result-card">
                    <h3>Facial Landmark Analysis</h3>
                    <p><strong>Age Range:</strong> ${data.face_analysis["Age Range"]}</p>
                    <p><strong>Gender:</strong> ${data.face_analysis["Gender"]}</p>
                </div>
                <div class="result-card">
                    <h3>Personality Insights</h3>
                    <p>${data.personality_insights}</p>
                </div>
                <p style="text-align: center; font-weight: bold;">💬 Have questions? Ask the FP AI Coach below! 💬</p>
            `;
        } catch (err) {
            faceResult.innerHTML = `<p style='color: red;'>Error: ${err}</p>`;
        }
    });

    // Function to format AI response (removes special characters)
    function cleanResponse(text) {
        return text.replace(/[#*_~•`]/g, "").replace(/\n\s*\n/g, "<br>"); // Remove markdown symbols and extra spaces
    }

    // Send Message Function
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === "") return;

        // Display User Message (Right-Aligned)
        const userMessage = document.createElement("div");
        userMessage.classList.add("message", "user-message");
        userMessage.innerText = message;
        chatBox.appendChild(userMessage);
        chatBox.scrollTop = chatBox.scrollHeight;
        userInput.value = "";

        // Send Message to AI Coach
        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        })
            .then((response) => response.json())
            .then((data) => {
                // Display AI Response (Left-Aligned)
                const botMessage = document.createElement("div");
                botMessage.classList.add("message", "bot-message");
                botMessage.innerHTML = cleanResponse(data.response);
                chatBox.appendChild(botMessage);
                chatBox.scrollTop = chatBox.scrollHeight;
            })
            .catch((error) => {
                console.error("Error:", error);
            });
    }

    // Click to Send
    sendBtn.addEventListener("click", sendMessage);

    // Press Enter to Send
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });
});
