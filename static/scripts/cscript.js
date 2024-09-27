document.addEventListener("DOMContentLoaded", () => {
    const messageForm = document.getElementById("user-input");
    const messageInput = document.getElementById("message");
    const sendButton = document.getElementById("send");
    const chat = document.getElementById("chat");
    const settingsModernButton = document.getElementById("modern-open-settings");
    const settingsCliButton = document.getElementById("cli-open-settings");
    let websocket = null;  // WebSocket variable to handle streaming
    const settingsPopup = document.getElementById("settings-popup");
    const closeSettingsButton = document.getElementById("close-settings");
    const customPromptInput = document.getElementById("custom-prompt-input");
    const submitPromptButton = document.getElementById("submit-prompt");
    const regenerationCounts = new Map(); // To track regeneration counts
    const resetPromptButton = document.getElementById("reset-prompt");
    const presetDropdown = document.getElementById("preset-dropdown");
    const themeDropdown = document.getElementById("theme-dropdown");
    const selectedTheme = themeDropdown.value;
    let isCooldown = false;
    let isImageSysPrompt = false;
    let lastUserMessage = ""; // Save the last user message
	settingsModernButton.addEventListener("click", () =>
	{
		settingsPopup.style.display = "block"
	});
	settingsCliButton.addEventListener("click", () =>
	{
		settingsPopup.style.display = "block"
	});
	closeSettingsButton.addEventListener("click", () =>
	{
		settingsPopup.style.display = "none"
	});


	function updateInputState()
	{
		const selectedPreset = presetDropdown.value;
		customPromptInput.disabled = selectedPreset !== "custom";
		customPromptInput.value = ""
	}
	themeDropdown.addEventListener("change", () =>
	{
		const selectedTheme = themeDropdown.value;
		if (selectedTheme === "cli")
		{
			document.querySelector('link[href="static/styles_url/global.css"]').href = "static/styles_url/cli.css";
			settingsModernButton.style.display = "none";
			settingsCliButton.style.display = "block"
		}
		else
		{
			document.querySelector('link[href="static/styles_url/cli.css"]').href = "static/styles_url/global.css";
			settingsModernButton.style.display = "block";
			settingsCliButton.style.display = "none"
		}
	});

	presetDropdown.addEventListener("change", updateInputState);
	resetPromptButton.addEventListener("click", async () =>
	{
		try
		{
			const response = await fetch("/reset_prompt",
			{
				method: "POST",
				headers:
				{
					"Content-Type": "application/json"
				}
			});
			if (response.ok)
			{
				presetDropdown.value = "prompt.txt";
				customPromptInput.value = "";
				settingsPopup.style.display = "none";
				updateInputState();
				alert("Conversation history and custom prompt reset successfully!")
			}
			else
			{
				throw new Error("Failed to reset conversation history and custom prompt")
			}
		}
		catch (error)
		{
			console.error("Error resetting conversation history and custom prompt:", error);
			alert("Failed to reset conversation history and custom prompt. Please try again later.")
		}
	});
	submitPromptButton.addEventListener("click", async () =>
	{
		const promptText = customPromptInput.value.trim();
		const selectedPreset = presetDropdown.value;
		if (selectedPreset !== "prompt.txt" && selectedPreset !== "custom" || selectedPreset === "custom" && promptText.length > 0)
		{
			try
			{
				await fetch("/reset_prompt",
				{
					method: "POST",
					headers:
					{
						"Content-Type": "application/json"
					}
				});
				const response = await fetch("/change_prompt",
				{
					method: "POST",
					headers:
					{
						"Content-Type": "application/json"
					},
					body: JSON.stringify(
					{
						prompt_file: selectedPreset,
						prompt_text: promptText
					})
				});
				if (response.ok)
				{
					console.log("Custom Prompt Submitted:", promptText.length > 0 ? promptText : selectedPreset);
					settingsPopup.style.display = "none";
					customPromptInput.value = "";
					alert("System prompt updated successfully!")
				}
				else
				{
					throw new Error("Failed to update system prompt")
				}
			}
			catch (error)
			{
				console.error("Error updating system prompt:", error);
				alert("Failed to update system prompt. Please try again later.")
			}
		}
		else
		{
			alert("Please enter a prompt or select a preset before submitting.")
		}
	});
	messageForm.addEventListener("submit", async event =>
	{
		event.preventDefault();
		if (!isCooldown)
		{
			await sendMessage()
		}
	});
	messageInput.addEventListener("keydown", event =>
	{
		if (event.key === "Enter" && !event.shiftKey && !isCooldown)
		{
			event.preventDefault();
			sendMessage()
		}
	});
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (message === "") return;  // Exit early if message is empty

        isCooldown = true;
        messageInput.disabled = true;
        sendButton.disabled = true;

        // Display user message with newlines preserved
        displayMessage(username, message.replace(/\n/g, "<br>"), "user");

        messageInput.value = "";

        try {
            // Handle "image" or "generate" messages
            if (message.toLowerCase().startsWith("image ") || message.toLowerCase().startsWith("generate ")) {
                if (!isImageSysPrompt || currentPromptFile !== "imagesys.txt") {
                    const response = await fetch("/change_prompt", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            prompt_file: "imagesys.txt",
                            prompt_text: ""
                        })
                    });

                    if (!response.ok) {
                        throw new Error("Failed to change prompt to imagesys.txt");
                    }
                    isImageSysPrompt = true;
                    currentPromptFile = "imagesys.txt";
                }
            } else {
                if (isImageSysPrompt) {
                    isImageSysPrompt = false;
                    currentPromptFile = "";
                }
            }

            // Send the user's message to the server
            const chatResponse = await fetch("/fetch_response", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: message
                })
            });

            if (!chatResponse.ok) {
                throw new Error("Failed to fetch response from chat server");
            }

            const data = await chatResponse.json();
            displayMessage("Nadia", data.response.replace(/\n/g, "<br>"), "assistant");

            if (data.image_url) {
                displayImage(data.image_url, "assistant");
            }
        } catch (error) {
            console.error("Error sending message:", error);
            alert(`Failed to send message. Error: ${error.message}`);
        } finally {
            setTimeout(() => {
                isCooldown = false;
                messageInput.disabled = false;
                sendButton.disabled = false;
            }, 0);
        }
    }

    function displayMessage(sender, message, cssClass) {
    const messageContainer = document.createElement("div");
    messageContainer.className = sender === "Nadia" ? "assistant-container" : "user-container";

    const messageElement = document.createElement("div");
    messageElement.className = `message ${cssClass}`;

    const senderElement = document.createElement("strong");
    senderElement.className = "username";
    senderElement.textContent = `${sender}: `;

    messageElement.appendChild(senderElement);

    const textElement = document.createElement("span");

    // Regex to check for code blocks and ignore anything immediately after the opening backticks
    const codeBlockRegex = /```(?:\w+)?\n?([\s\S]*?)```/g;

    // Check if the message contains bold text like **text**
    const boldTextRegex = /\*\*(.*?)\*\*/g;

    // Apply formatting for code blocks first
    let formattedMessage = message.replace(codeBlockRegex, (match, p1) => {
        // Trim whitespace and remove empty lines from the start and end
        const codeContent = p1.split('\n')
            .map(line => line.trim()) // Trim each line
            .filter(line => line !== '') // Remove empty lines
            .join('<br>'); // Join lines back with <br> for HTML rendering

        // Add the copy icon inside the code block container
        return `
            <div class="code-container" style="position: relative;">
                <i class="fas fa-copy copy-icon" title="Copy Code" style="position: absolute; top: 10px; right: 10px; cursor: pointer;"></i>
                <code>${codeContent}</code>
            </div>`;
    });

    // Then apply formatting for bold text
    formattedMessage = formattedMessage.replace(boldTextRegex, (match, p1) => {
        // Wrap the bold text inside <strong></strong> tags
        return `<strong>${p1}</strong>`;
    });

    // Update the message content with formatted code blocks and bold text
    textElement.innerHTML = formattedMessage;

    messageElement.appendChild(textElement);
    messageContainer.appendChild(messageElement);

    // Initialize the regeneration count for this message
    let currentCount = regenerationCounts.get(message) || 0;

    // If the message is from the assistant, add a regenerate icon
    if (sender === "Nadia") {
        const regenerateIcon = document.createElement("i");
        regenerateIcon.className = "fas fa-sync regenerate-icon"; // Font Awesome icon class

        // Disable icon if the count has reached the cap
        if (currentCount >= 3) {
            regenerateIcon.style.pointerEvents = "none"; // Disable clicking
            regenerateIcon.classList.add("disabled"); // Optionally add a class for styling
        }

        regenerateIcon.addEventListener("click", async () => {
            if (currentCount >= 3) return; // Prevent further regeneration if cap is reached

            // Disable the icon to prevent multiple clicks
            regenerateIcon.style.pointerEvents = "none";

            // Get the last assistant message
            const lastAssistantMessage = messageContainer;

            try {
                const regenerateResponse = await fetch("/regenerate_response", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    }
                });

                if (!regenerateResponse.ok) {
                    throw new Error("Failed to regenerate response.");
                }

                const data = await regenerateResponse.json();

                // Replace the old response with the new one
                let newMessage = data.response;

                // Apply the same formatting logic for code blocks
                newMessage = newMessage.replace(codeBlockRegex, (match, p1) => {
                    // Trim whitespace and remove empty lines from the start and end
                    const codeContent = p1.split('\n')
                        .map(line => line.trim()) // Trim each line
                        .filter(line => line !== '') // Remove empty lines
                        .join('<br>'); // Join lines back with <br> for HTML rendering

                    return `<div class="code-container" style="position: relative;">
                                <i class="fas fa-copy copy-icon" title="Copy Code" style="position: absolute; top: 10px; right: 10px; cursor: pointer;"></i>
                                <code>${codeContent}</code>
                            </div>`;
                });

                // Apply the same formatting logic for bold text
                newMessage = newMessage.replace(boldTextRegex, (match, p1) => {
                    return `<strong>${p1}</strong>`;
                });

                lastAssistantMessage.querySelector("span").innerHTML = newMessage;

                // Update the regeneration count
                currentCount++;
                regenerationCounts.set(message, currentCount);

                // Disable the icon if the count has reached the cap
                if (currentCount >= 3) {
                    regenerateIcon.style.pointerEvents = "none"; // Disable clicking
                    regenerateIcon.classList.add("disabled"); // Add disabled class
                }
            } catch (error) {
                console.error("Error regenerating response:", error);
                alert(`Failed to regenerate response. Error: ${error.message}`);
            } finally {
                // Re-enable the icon
                regenerateIcon.style.pointerEvents = "auto";
                regenerateIcon.classList.remove("fa-spin"); // Remove spinning effect
            }
        });

        messageContainer.appendChild(regenerateIcon);
    }

    chat.appendChild(messageContainer);

    // Add copy functionality for code blocks
    messageContainer.querySelectorAll('.copy-icon').forEach(icon => {
        icon.addEventListener('click', () => {
            const codeBlock = icon.closest('.code-container').querySelector('code');

            // Get the raw text content without HTML tags
            let codeText = codeBlock.innerText || codeBlock.textContent; // Use textContent to get raw text
            codeText = codeText.replace(/\n/g, '\n'); // Ensure line breaks are preserved

            // Check for clipboard support
            if (navigator.clipboard && navigator.clipboard.writeText) {
                // Copy the code to the clipboard
                navigator.clipboard.writeText(codeText).then(() => {
                    alert('Code copied to clipboard!');
                }).catch(err => {
                    console.error('Failed to copy code:', err);
                    alert('Failed to copy code. Please try again.');
                });
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = codeText;
                document.body.appendChild(textArea);
                textArea.select();
                try {
                    document.execCommand('copy');
                    alert('Code copied to clipboard!');
                } catch (err) {
                    console.error('Fallback copy failed:', err);
                    alert('Failed to copy code. Please try again.');
                }
                document.body.removeChild(textArea); // Clean up
            }
        });
    });

    // Trigger MathJax to typeset the new content
    MathJax.typeset();

    chat.scrollTop = chat.scrollHeight;
}

    
    














    function updateStreamedMessage(newToken) {
        const assistantMessages = document.querySelectorAll(".assistant-container .message");
        let lastMessage = assistantMessages[assistantMessages.length - 1];

        if (!lastMessage) {
            // If no assistant message exists yet, create one
            displayMessage("Nadia", newToken, "assistant");
        } else {
            // If a message exists, append the new token
            const textElement = lastMessage.querySelector("span");
            textElement.innerHTML += newToken;

            // Trigger MathJax to typeset the updated content
            MathJax.typeset();
        }

        chat.scrollTop = chat.scrollHeight;  // Scroll to the bottom
    }

    function displayImage(imageUrl, cssClass) {
        const messageElement = document.createElement("div");
        messageElement.className = `message ${cssClass}`;
        const imageElement = document.createElement("img");
        imageElement.src = imageUrl;
        imageElement.alt = "Assistant Response Image";
        imageElement.style.maxWidth = "65%";
        imageElement.style.height = "65%";
        imageElement.style.borderRadius = "25px";
        messageElement.appendChild(imageElement);
        chat.appendChild(messageElement);
        chat.scrollTop = chat.scrollHeight;
    }
    function draggable(elmnt)
    {
    	let pos1 = 0,
    		pos2 = 0,
    		pos3 = 0,
    		pos4 = 0;
    	if (document.getElementById(elmnt.id + "-header"))
    	{
    		document.getElementById(elmnt.id + "-header").onmousedown = dragMouseDown
    	}
    	else
    	{
    		elmnt.onmousedown = dragMouseDown
    	}

    	function dragMouseDown(e)
    	{
    		e = e || window.event;
    		e.preventDefault();
    		pos3 = e.clientX;
    		pos4 = e.clientY;
    		document.onmouseup = closeDragElement;
    		document.onmousemove = elementDrag
    	}

    	function elementDrag(e)
    	{
    		e = e || window.event;
    		e.preventDefault();
    		pos1 = pos3 - e.clientX;
    		pos2 = pos4 - e.clientY;
    		pos3 = e.clientX;
    		pos4 = e.clientY;
    		elmnt.style.top = elmnt.offsetTop - pos2 + "px";
    		elmnt.style.left = elmnt.offsetLeft - pos1 + "px"
    	}

    	function closeDragElement()
    	{
    		document.onmouseup = null;
    		document.onmousemove = null
    	}
    }

});