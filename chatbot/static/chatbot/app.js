const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const messagesContainer = document.getElementById("messages");
const sendButton = document.getElementById("send-button");
const newChatButton = document.getElementById("new-chat-button");

const csrfToken = document.querySelector(
    "[name=csrfmiddlewaretoken]"
).value;


const STORAGE_KEY = "edubot_history";

let conversationHistory = loadHistory();


function loadHistory() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);

        if (!saved) {
            return [];
        }

        const parsed = JSON.parse(saved);

        if (!Array.isArray(parsed)) {
            return [];
        }

        return parsed;
    } catch (error) {
        console.error(error);
        return [];
    }
}


function saveHistory() {
    localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(conversationHistory)
    );
}


function addMessage(role, content) {

    const message = document.createElement("div");

    message.classList.add("message", role);


    const avatar = document.createElement("div");

    avatar.classList.add("avatar");

    avatar.textContent =
        role === "assistant"
            ? "E"
            : "U";


    const bubble = document.createElement("div");

    bubble.classList.add("bubble");


    const name = document.createElement("strong");

    name.textContent =
        role === "assistant"
            ? "EduBot"
            : "Vous";


    const text = document.createElement("p");

    text.textContent = content;


    bubble.appendChild(name);
    bubble.appendChild(text);


    if (role === "assistant") {

        message.appendChild(avatar);
        message.appendChild(bubble);

    } else {

        message.appendChild(bubble);
        message.appendChild(avatar);
    }


    messagesContainer.appendChild(message);

    scrollToBottom();
}


function renderHistory() {

    for (const item of conversationHistory) {

        if (
            item.role === "user" ||
            item.role === "assistant"
        ) {
            addMessage(
                item.role,
                item.content
            );
        }
    }
}


function showTyping() {

    const wrapper = document.createElement("div");

    wrapper.classList.add(
        "message",
        "assistant"
    );

    wrapper.id = "typing-indicator";


    const avatar = document.createElement("div");

    avatar.classList.add("avatar");

    avatar.textContent = "E";


    const bubble = document.createElement("div");

    bubble.classList.add("bubble");


    const typing = document.createElement("div");

    typing.classList.add("typing");


    for (let i = 0; i < 3; i++) {

        const dot = document.createElement("span");

        dot.classList.add("dot");

        typing.appendChild(dot);
    }


    bubble.appendChild(typing);

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    messagesContainer.appendChild(wrapper);

    scrollToBottom();
}


function removeTyping() {

    const typing =
        document.getElementById(
            "typing-indicator"
        );

    if (typing) {
        typing.remove();
    }
}


function scrollToBottom() {

    messagesContainer.parentElement.scrollTop =
        messagesContainer.parentElement.scrollHeight;
}


async function sendMessage(message) {

    sendButton.disabled = true;
    input.disabled = true;

    showTyping();


    try {

        const response = await fetch(
            "/api/chat/",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest"
                },

                body: JSON.stringify({
                    message: message,
                    history: conversationHistory
                })
            }
        );


        const data = await response.json();


        removeTyping();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Une erreur est survenue."
            );
        }


        addMessage(
            "assistant",
            data.reply
        );


        conversationHistory.push({
            role: "user",
            content: message
        });


        conversationHistory.push({
            role: "assistant",
            content: data.reply
        });


        saveHistory();


    } catch (error) {

        removeTyping();

        console.error(error);


        addMessage(
            "assistant",
            "Désolé, une erreur est survenue : " +
            error.message
        );

    } finally {

        sendButton.disabled = false;
        input.disabled = false;

        input.focus();
    }
}


form.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        const message =
            input.value.trim();


        if (!message) {
            return;
        }


        addMessage(
            "user",
            message
        );


        input.value = "";

        await sendMessage(message);
    }
);


input.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            form.requestSubmit();
        }
    }
);


newChatButton.addEventListener(
    "click",
    function () {

        const confirmation = confirm(
            "Supprimer cette conversation ?"
        );


        if (!confirmation) {
            return;
        }


        conversationHistory = [];

        localStorage.removeItem(
            STORAGE_KEY
        );


        messagesContainer.innerHTML = `
            <div class="message assistant">

                <div class="avatar">
                    E
                </div>

                <div class="bubble">

                    <strong>EduBot</strong>

                    <p>
                        Nouvelle conversation.
                        Comment puis-je t'aider ?
                    </p>

                </div>

            </div>
        `;
    }
);


if (conversationHistory.length > 0) {
    renderHistory();
}