document.addEventListener("DOMContentLoaded", () =>
{
	const messageForm = document.getElementById("user-input");
	const messageInput = document.getElementById("message");
	const sendButton = document.getElementById("send");
	const chat = document.getElementById("chat");
	const settingsModernButton = document.getElementById("modern-open-settings");
	const settingsCliButton = document.getElementById("cli-open-settings");
	const settingsPopup = document.getElementById("settings-popup");
	const closeSettingsButton = document.getElementById("close-settings");
	const customPromptInput = document.getElementById("custom-prompt-input");
	const submitPromptButton = document.getElementById("submit-prompt");
	const resetPromptButton = document.getElementById("reset-prompt");
	const presetDropdown = document.getElementById("preset-dropdown");
	const themeDropdown = document.getElementById("theme-dropdown");
	const selectedTheme = themeDropdown.value;
	let isCooldown = false;
	let isImageSysPrompt = false;
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

        // Display user message
        const lines = message.split("\n");
        for (const line of lines) {
            displayMessage(username, line, "user");
        }
        messageInput.value = "";

        try {
            // Check if the message contains both "anime" and "image"
            if (message.toLowerCase().includes("anime") && message.toLowerCase().includes("image")) {
                if (!isImageSysPrompt || currentPromptFile !== "anime.txt") {
                    const response = await fetch("/change_prompt", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            prompt_file: "anime.txt",
                            prompt_text: ""
                        })
                    });

                    if (!response.ok) {
                        throw new Error("Failed to change prompt to anime.txt");
                    }
                    isImageSysPrompt = true;
                    currentPromptFile = "anime.txt"; // Track the current prompt file
                }
            }
            // Check for image prompt logic
            else if (message.toLowerCase().startsWith("image ")) {
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
                    currentPromptFile = "imagesys.txt"; // Track the current prompt file
                }
            } else {
                // If not an image or anime prompt, reset image prompt flag
                if (isImageSysPrompt) {
                    isImageSysPrompt = false;
                    currentPromptFile = ""; // Reset the current prompt file
                }
            }

            // Send the user's message to the server
            const chatResponse = await fetch("/chat1", {
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
            displayMessage("Nadia", data.response, "assistant");

            if (data.image_url) {
                displayImage(data.image_url, "assistant");
            }
        } catch (error) {
            console.error("Error sending message:", error);
            alert(`Failed to send message. Error: ${error.message}`);
        } finally {
            // Always reset the input state and button states
            setTimeout(() => {
                isCooldown = false;
                messageInput.disabled = false;
                sendButton.disabled = false;
            }, 10000);
        }
    }


	function displayMessage(sender, message, cssClass)
	{
		const messageContainer = document.createElement("div");
		messageContainer.className = sender === "Nadia" ? "assistant-container" : "user-container";
		const messageElement = document.createElement("div");
		messageElement.className = `message ${cssClass}`;
		const senderElement = document.createElement("strong");
		senderElement.className = "username";
		senderElement.textContent = `${sender}: `;
		messageElement.appendChild(senderElement);
		const textElement = document.createElement("span");
		messageElement.appendChild(textElement);
		messageContainer.appendChild(messageElement);
		chat.appendChild(messageContainer);
		chat.scrollTop = chat.scrollHeight;
		if (sender === "Nadia")
		{
			let i = 0;
			const typingInterval = setInterval(() =>
			{
				if (i < message.length)
				{
					textElement.textContent += message.charAt(i);
					i++;
					chat.scrollTop = chat.scrollHeight
				}
				else
				{
					clearInterval(typingInterval)
				}
			}, Math.random() * (5 - 3) + 3)
		}
		else
		{
			textElement.textContent = message
		}
		chat.scrollTop = chat.scrollHeight
	}

	function displayImage(imageUrl, cssClass)
	{
		const messageElement = document.createElement("div");
		messageElement.className = `message ${cssClass}`;
		const imageElement = document.createElement("img");
		imageElement.src = imageUrl;
		imageElement.alt = "Assistant Response Image";
		imageElement.style.maxWidth = "100%";
		imageElement.style.height = "auto";
		imageElement.style.borderRadius = "30px";
		messageElement.appendChild(imageElement);
		chat.appendChild(messageElement);
		chat.scrollTop = chat.scrollHeight
	}

	function copyToClipboard(text)
	{
		navigator.clipboard.writeText(text).then(() =>
		{
			alert("Code copied to clipboard!")
		})["catch"](err =>
		{
			console.error("Failed to copy: ", err)
		})
	}

	function dragElement(elmnt)
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