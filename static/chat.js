// ================================== CHAT SIDEBAR STRATS HERE (ASIDE) =================================
// Setting up the chat sidebar toggle functionality

document.querySelector('.chat-sidebar-profile-toggle').addEventListener('click', function (e) {
    e.preventDefault()
    this.parentElement.classList.toggle('active')
})

document.addEventListener('click', function (e) {
    if (!e.target.matches('.chat-sidebar-profile, .chat-sidebar-profile *')) {
        document.querySelector('.chat-sidebar-profile').classList.remove('active')
    }
})

// ================================ CHAT SIDEBAR ENDS HERE (ASIDE) ======================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ================================== CHAT AREA TOGGLE STRATS HERE ======================================
// Chat conversation toggle functionality

document.querySelectorAll('.conversation-item-dropdown-toggle').forEach(function (item) {
    item.addEventListener('click', function (e) {
        e.preventDefault()
        if (this.parentElement.classList.contains('active')) {
            this.parentElement.classList.remove('active')
        } else {
            document.querySelectorAll('.conversation-item-dropdown').forEach(function (i) {
                i.classList.remove('active')
            })
            this.parentElement.classList.add('active')
        }
    })
})

document.addEventListener('click', function (e) {
    if (!e.target.matches('.conversation-item-dropdown, .conversation-item-dropdown *')) {
        document.querySelectorAll('.conversation-item-dropdown').forEach(function (i) {
            i.classList.remove('active')
        })
    }
})
// ========================= CHAT AREA TOGGLE ENDS HERE ===================================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ===================== CHAT INPUT/SEND CONVERSATION FORM STARTS HERE ====================================

document.querySelectorAll('.conversation-form-input').forEach(function (item) {
    item.addEventListener('input', function () {
        this.rows = this.value.split('\n').length
    })
})

document.querySelectorAll('[data-conversation]').forEach(function (item) {
    item.addEventListener('click', function (e) {
        e.preventDefault()
        document.querySelectorAll('.conversation').forEach(function (i) {
            i.classList.remove('active')
        })
        document.querySelector(this.dataset.conversation).classList.add('active')
    })
})

// =================================== CHAT INPUT/SEND CONVERSATION FORM ENDS HERE =========================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ================================== CHAT AREA TOGGLE STARTS HERE =========================================

document.querySelectorAll('.conversation-back').forEach(function (item) {
    item.addEventListener('click', function (e) {
        e.preventDefault()
        this.closest('.conversation').classList.remove('active')
        document.querySelector('.conversation-default').classList.add('active')
    })
})

// =================================== CHAT AREA TOTGGLE ENDS HERE =========================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ====================== FLASK SOCKETIO CONNECTION SET UP STARTS HERE  ====================================


var sessionUserId = "{{ user_id }}";
var groupId = "{{ group_id }}" || null;
var privateChatId = "{{ private_chat_id }}" || null;
window.activeChatId = groupId || privateChatId;
window.activeChatType = groupId ? "group" : privateChatId ? "private" : null;

const socket = io.connect("http://127.0.0.1:5005/");


socket.on("connect", function () {
    console.log("Connected to the server!");

    if (window.activeChatType === "group") {
        socket.emit("join_group", { group_id: parseInt(window.activeChatId) });
    } else if (window.activeChatType === "private") {
        socket.emit("join_private_chat", { chat_id: parseInt(window.activeChatId), user_id: sessionUserId });
    }
});


// ================================ FLASK SOCKETIO CONNECTION SET UP ENDS HERE  ================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// =============================== USER SESSION STORAGE STARTS HERE ============================================

window.onload = async function () {
    const sessionData = await fetchSessionData();

    if (sessionData) {
        let chatId = sessionStorage.getItem("active_chat_id");
        let chatType = sessionStorage.getItem("active_chat_type");

        if (chatId && chatType) {
            switchChat(chatId, chatType);
        }
    }
};

// ------------------------------------ FUNCTION TO FETCH USER SESSION DATA -------------------------------------
// Ensure session data is loaded before setting sessionStorage values
async function fetchSessionData() {
    try {
        let response = await fetch('/get_session_data', { credentials: 'include' });
        let data = await response.json();

        if (!data.success || !data.user_id) {
            console.warn("⚠️ Invalid session data! Redirecting to login...");
            window.location.href = "/login";
            return null;
        }

        sessionStorage.setItem("user_id", data.user_id);
        sessionStorage.setItem("firstname", data.firstname);
        sessionStorage.setItem("lastname", data.lastname);
        sessionStorage.setItem("staffid", data.staffid);

        // Store only if they exist
        if (data.group_id) sessionStorage.setItem("group_id", data.group_id);
        if (data.private_chat_id) sessionStorage.setItem("private_chat_id", data.private_chat_id);

        return data;
    } catch (error) {
        console.error("❌ ERROR: Fetching session data failed:", error);
        return null;
    }
}

// ================================ USER SESSION STORAGE ENDS HERE =============================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ======================================== SWITCH FUNCTION STARTS HERE ========================================

function switchChat(chat_id, chat_type) {
    if (!chat_id || !chat_type) {
        console.error("❌ Invalid chat switch request!");
        return;
    }

    console.log(`✅ Switching to ${chat_type} chat (ID: ${chat_id})`);

    sessionStorage.setItem("active_chat_id", chat_id);
    sessionStorage.setItem("active_chat_type", chat_type);


    window.activeChatId = chat_id;
    window.activeChatType = chat_type;

    let sessionUserId = sessionStorage.getItem("user_id");
    if (!sessionUserId) {
        console.error("⚠️ User ID missing from sessionStorage!");
        return;
    }

    socket.emit("leave_group", { group_id: chat_id });
    socket.emit("leave_private_chat", { chat_id: chat_id });

    if (chat_type === "group") {
        socket.emit("leave_private_chat", { chat_id: window.activeChatId }); // Leave the previous private chat (if any)
        socket.emit("join_group", { group_id: chat_id });
    } else if (chat_type === "private") {
        socket.emit("leave_group", { group_id: window.activeChatId }); // Leave the previous group chat (if any)
        socket.emit("join_private_chat", { chat_id: chat_id, user_id: sessionUserId });
    }


    // console.log(`✅ Switched to ${chat_type} chat (ID: ${chat_id})`);
    loadChat(chat_id, chat_type);
}


// -------------------------- Function to join the chat room --------------------------
// This function is called when the user clicks on a chat item in the sidebar
function joinChatRoom(chatType, chatId) {
    window.activeChatType = chatType;
    window.activeChatId = chatId;

    // 🔹 Make sure the user joins the correct room
    if (chatType === "group") {
        socket.emit("join_group", { group_id: chatId });
        console.log(`📡 Joining group: ${chatId}`);
    } else if (chatType === "private") {
        socket.emit("join_private_chat", { chat_id: chatId });
        console.log(`📡 Joining private chat: ${chatId}`);
    }

    // console.log(`✅ Joined ${chatType} room:`, chatId);
}

// ===================================== SWITCH FUNCTION ENDS HERE =============================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ==================================== HANDLE CHAT CLICK FUNCTION STARTS HERE =================================

function handleChatClick(event) {
    // Prevent default anchor behavior
    event.preventDefault();

    // Find the closest chat list item
    const chatItemList = event.target.closest(".chat-item-list");
    if (!chatItemList) return;

    // Get the chat item and its data attributes
    const chatItem = chatItemList.querySelector(".chat-item");
    if (!chatItem) {
        console.error("Chat item element not found!");
        return;
    }

    const chatId = chatItem.dataset.chatId?.trim();
    const chatType = chatItem.dataset.chatType?.trim();

    if (!chatId || !chatType) {
        console.error("Missing chat ID or type!");
        return;
    }

    // 1. FIRST REMOVE ACTIVE CLASS FROM ALL CHATS
    document.querySelectorAll(".chat-item-list").forEach(item => {
        item.classList.remove("active-chat", "active"); // Remove both classes for safety
    });

    // 2. THEN ADD ACTIVE CLASS ONLY TO THE CLICKED CHAT
    chatItemList.classList.add("active"); // Using just one active class

    // 3. UPDATE CHAT HEADER
    updateChatHeader(
        chatItemList.querySelector(".content-message-name")?.textContent.trim(),
        chatItemList.querySelector(".content-message-image")?.src
    );

    // 4. HANDLE UNREAD MESSAGES
    const unreadBadge = chatItemList.querySelector(".content-message-unread");
    if (unreadBadge) {
        unreadBadge.textContent = "";
        unreadBadge.style.display = "none";
    }

    // 5. MARK MESSAGES AS READ VIA SOCKET
    socket.emit("mark_messages_as_read", {
        chat_id: chatId,
        chat_type: chatType,
        user_id: sessionStorage.getItem("user_id")
    });

    // 6. STORE ACTIVE CHAT IN SESSION STORAGE
    sessionStorage.setItem("active_chat_id", chatId);
    sessionStorage.setItem("active_chat_type", chatType);

    // 7. FINALLY SWITCH TO THE SELECTED CHAT
    switchChat(chatId, chatType);
}

// Attach event listener correctly
document.querySelectorAll(".chat-item").forEach(item => {
    item.addEventListener("click", handleChatClick);
});



socket.on("messages_marked_as_read", function (data) {
    console.log(`✅ ${data.updated_count} messages marked as read for ${data.chat_id}`);

    const chatItem = document.querySelector(`.chat-item[data-chat-id="${data.chat_id}"]`);
    if (chatItem) {
        let unreadBadge = chatItem.querySelector(".content-message-unread");
        if (unreadBadge) {
            unreadBadge.textContent = ""; // Clear unread count
            unreadBadge.style.display = "none"; // Hide unread badge
        }
    }
});

// =========================================== HANDLE CHAT CLICK FUNCTION ENDS HERE ========================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ========================================== UPDATE CHAT HEADER AND IMAGE FUNCTION STARTS HERE ============================

function updateChatHeader(chatName, chatImage) {
    let chatHeader = document.getElementById("chatHeader");
    let chatImg = document.getElementById("chatHeaderImg");

    if (chatHeader) {
        chatHeader.textContent = chatName || "Chat";
    }

    if (chatImg) {
        if (chatImage) {
            chatImg.src = chatImage;
            chatImg.style.display = "block"; // Ensure image is visible
        } else {
            chatImg.src = "/static/images/default-profile.png"; // Fallback avatar
            chatImg.style.display = "block"; // Ensure default image shows
        }
    } else {
        console.error("❌ Chat header image element not found!");
    }

    // Debugging: Ensure no duplicate images
    const header = document.querySelector(".chat-header");
    if (header) {
        const images = header.querySelectorAll("img");
        if (images.length > 1) {
            console.warn("⚠️ Multiple images detected in header! Removing extras...");
            images.forEach((img, index) => {
                if (index > 0) img.remove(); // Keep only the first image
            });
        }
    }
}

// -========================================== UPDATE CHAT HEADER AND IMAGE FUNCTION ENDS HERE ===============================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ===========================================  TIMESTAMP FORMAT FUNCTION ====================================================

function formatTimestamp(timestamp) {
    if (!timestamp) return "Just now";

    const date = new Date(timestamp);

    if (isNaN(date.getTime())) {
        console.error("❌ Invalid timestamp:", timestamp);
        return "Just now";
    }

    return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true
    });
}

// =========================================== TIMESTAMP FORMAT FUNCTION ENDS HERE =========================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// =========================================== LOAD CHAT FUNCTION STARTS HERE ==============================================

function loadChat(chatId, chatType) {
    chatId = chatId || sessionStorage.getItem("active_chat_id");
    chatType = chatType || sessionStorage.getItem("active_chat_type");

    if (!chatId || !chatType) {
        console.error("loadChat: Missing chat ID or type!", { chatId, chatType });
        return;
    }

    console.log("📥 Loading chat:", chatId, chatType);

    if (chatType === "group") {
        socket.emit("join_group", { group_id: chatId });
        console.log(`📡 Joining group: ${chatId}`);
    } else if (chatType === "private") {
        socket.emit("join_private_chat", { chat_id: chatId });
        console.log(`📡 Joining private chat: ${chatId}`);
    }

    let chatbox = document.getElementById("conversation-main");
    if (!chatbox) {
        console.error("Chatbox element not found!");
        return;
    }

    chatbox.innerHTML = "<p>Loading messages...</p>";

    fetch(`/get_messages?chat_id=${chatId}&chat_type=${chatType}`)
        .then(response => response.json())
        .then(data => {
            chatbox.innerHTML = "";

            if (!Array.isArray(data.messages)) {
                console.error("Invalid messages format:", data.messages);
                chatbox.innerHTML = "<p>Error loading messages.</p>";
                return;
            }

            if (data.messages.length === 0) {
                chatbox.innerHTML = "<p>No messages yet.</p>";
                return;
            }

            let lastDate = null;

            data.messages.forEach(message => {
                let messageDate = new Date(message.timestamp).toDateString(); // e.g., "Wed Mar 20 2025"

                if (lastDate !== messageDate) {
                    insertDateSeparator(messageDate); // 🔹 Insert date separator
                    lastDate = messageDate;
                }

                displayMessage(message, chatType);
            });

            chatbox.scrollTop = chatbox.scrollHeight;

        })

        .catch(error => {
            console.error("Error loading chat messages:", error);
            chatbox.innerHTML = "<p>Error loading messages.</p>";
        });
}


// ====================================== LOAD CHAT FUNCTION ENDS HERE ===============================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ======================================= DISPLAY MESSAGE FUNCTION STARTS HERE ======================================

async function displayMessage(data, chatType) {
    let messagesContainer = document.getElementById("conversation-main");
    if (!messagesContainer) {
        console.error("❌ Chatbox not found!");
        return;
    }

    let sessionUserId = sessionStorage.getItem("user_id");
    let isOutgoing = String(data.user_id) === String(sessionUserId);

    let messageWrapper = document.createElement("div");
    messageWrapper.classList.add("message-wrapper");
    messageWrapper.classList.add(isOutgoing ? "outgoing" : "incoming");
    messageWrapper.dataset.messageId = data.id;

    let senderName = (chatType === "group" && data.sender) ? `<strong>${data.sender}:</strong> ` : "";
    let messageText = data.message_type === "text" ? data.message : "";

    let fileUrl = data.file_url || data.message;
    let filePreview = "";

    if (data.message_type === "image" || data.message_type === "file") {
        if (fileUrl) {
            let fullUrl = fileUrl.startsWith("http") ? fileUrl : window.location.origin + fileUrl;
            filePreview = generateFilePreview(fullUrl, data.message_type);
        } else {
            console.warn("⚠️ No file URL found for preview!");
        }
    }

    if (!messageText && !filePreview) {
        console.warn("⚠️ Empty message and no file preview! Skipping message display.");
        return;
    }

    // Determine tick icon
    let tickIcon = "";
    if (isOutgoing) {
        const readBy = data.read_by || [];
        if (readBy.includes(sessionUserId)) {
            tickIcon = '<i class="ri-check-double-line" style="color: red;"></i>';
        } else if (data.status === "delivered") {
            tickIcon = '<i class="ri-check-double-line"></i>';
        } else {
            tickIcon = '<i class="ri-check-line"></i>';
        }
    }

    messageWrapper.innerHTML = `
        <div class="conversation-item ${isOutgoing ? 'outgoing' : 'incoming'}">
            <!-- Dropdown for outgoing messages (left side) -->
            ${isOutgoing ? `
                <div class="conversation-item-dropdown">
                    <button type="button" class="conversation-item-dropdown-toggle">
                        <i class="ri-more-2-line"></i>
                    </button>
                    <ul class="conversation-item-dropdown-list">
                        <li><a href="#" class="dropdown-item reply-message" data-message-id="${data.id}">
                            <i class="ri-reply-line"></i> Reply
                        </a></li>
                        <li><a href="#" class="dropdown-item copy-message" data-message-id="${data.id}">
                            <i class="ri-file-copy-line"></i> Copy
                        </a></li>
                        <li><a href="#" class="dropdown-item forward-message" data-message-id="${data.id}">
                            <i class="ri-share-forward-line"></i> Forward
                        </a></li>
                        <li><a href="#" class="dropdown-item star-message" data-message-id="${data.id}">
                            <i class="ri-star-line"></i> Star
                        </a></li>
                        <li><a href="#" class="dropdown-item delete-message" data-message-id="${data.id}">
                            <i class="ri-delete-bin-line"></i> Delete
                        </a></li>
                        <li><a href="#" class="dropdown-item select-message" data-message-id="${data.id}">
                            <i class="ri-checkbox-line"></i> Select
                        </a></li>
                        <li><a href="#" class="dropdown-item share-message" data-message-id="${data.id}">
                            <i class="ri-share-line"></i> Share
                        </a></li>
                    </ul>
                </div>
            ` : ''}

            <!-- Avatar for incoming messages -->
            ${!isOutgoing ? `
                <div class="conversation-item-side">
                    <img class="conversation-item-image" src="/profile_picture/${data.user_id}" alt="">
                </div>
            ` : ''}

            <!-- Message content -->
            <div class="conversation-item-content">
                <div class="conversation-item-wrapper">
                    <div class="conversation-item-box ${isOutgoing ? 'outgoing-bubble' : 'incoming-bubble'}">
                        <div class="conversation-item-text">
                            <p class="message-text">${senderName}${messageText}</p>
                            ${filePreview}
                            <div class="timestamp conversation-item-time">
                                ${formatTimestamp(data.timestamp)}
                                ${tickIcon}    
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Avatar for outgoing messages -->
            ${isOutgoing ? `
                <div class="conversation-item-side">
                    <img class="conversation-item-image" src="/profile_picture/${sessionUserId}" alt="">
                </div>
            ` : ''}

            <!-- Dropdown for incoming messages (right side) -->
            ${!isOutgoing ? `
                <div class="conversation-item-dropdown">
                    <button type="button" class="conversation-item-dropdown-toggle">
                        <i class="ri-more-2-line"></i>
                    </button>
                    <ul class="conversation-item-dropdown-list">
                        <li><a href="#" class="dropdown-item reply-message" data-message-id="${data.id}">
                            <i class="ri-reply-line"></i> Reply
                        </a></li>
                        <li><a href="#" class="dropdown-item copy-message" data-message-id="${data.id}">
                            <i class="ri-file-copy-line"></i> Copy
                        </a></li>
                        <li><a href="#" class="dropdown-item forward-message" data-message-id="${data.id}">
                            <i class="ri-share-forward-line"></i> Forward
                        </a></li>
                        <li><a href="#" class="dropdown-item star-message" data-message-id="${data.id}">
                            <i class="ri-star-line"></i> Star
                        </a></li>
                        <li><a href="#" class="dropdown-item delete-message" data-message-id="${data.id}">
                            <i class="ri-delete-bin-line"></i> Delete
                        </a></li>
                        <li><a href="#" class="dropdown-item select-message" data-message-id="${data.id}">
                            <i class="ri-checkbox-line"></i> Select
                        </a></li>
                        <li><a href="#" class="dropdown-item share-message" data-message-id="${data.id}">
                            <i class="ri-share-line"></i> Share
                        </a></li>
                    </ul>
                </div>
            ` : ''}
        </div>
    `;

    messagesContainer.appendChild(messageWrapper);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ======================================== DISPLAY MESSAGE FUNCTION ENDS HERE ==============================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ==================================================== SEARCH USER FUNCTION STARTS HERE ====================================

function searchUser() {
    let query = document.getElementById("searchInput").value.trim();
    if (query.length < 2) {
        document.getElementById("searchResults").innerHTML = "";
        return;
    }

    fetch(`/search_users?query=${query}`)
        .then(response => response.json())
        .then(data => {
            let searchResults = document.getElementById("searchResults");
            searchResults.innerHTML = "";

            if (data.length === 0) {
                searchResults.innerHTML = "<p>No users found</p>";
                return;
            }

            data.forEach(user => {
                let userItem = document.createElement("div");
                userItem.classList.add("search-item");

                // Use profile picture URL from backend
                let userImage = user.image_url || "/static/images/default-profile.png";

                userItem.innerHTML = `
                    <div class="search-user">
                        <img src="${userImage}" alt="User Avatar" class="user-avatar">
                        <div class="user-details">
                            <p>${user.firstname} ${user.lastname} (${user.staffid})</p>
                        </div>
                    </div>
                `;

                // Handle click event to start private chat
                userItem.onclick = () => {
                    // Pass user.id, fullName, and imageUrl to startPrivateChat
                    startPrivateChat(user.id, `${user.firstname} ${user.lastname}`, user.image_url);
                    searchResults.innerHTML = "";  // Clear search results
                    document.getElementById("searchInput").value = "";  // Clear input field
                };

                searchResults.appendChild(userItem);
            });
        })
        .catch(error => console.error("Error searching users:", error));
}

// ==================================== SEARCH USER FUNCTION ENDS HERE ==============================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ================================== SEND MESSAGE FUNCTION STARTS HERE =============================================

document.addEventListener("DOMContentLoaded", function () {
    const sendButton = document.getElementById("sendButton");
    const messageInput = document.getElementById("messageInput");
    const fileInput = document.getElementById("fileInput");

    // Remove existing event listeners to avoid duplicates
    sendButton.removeEventListener("click", sendMessage);
    messageInput.removeEventListener("keypress", handleEnterKey);

    // Attach event listeners
    sendButton.addEventListener("click", sendMessage);
    messageInput.addEventListener("keypress", handleEnterKey);


    async function sendMessage() {
        const file = fileInput.files[0];
        const message = messageInput.value.trim();

        if (!message && !file) {
            console.error("❌ Please enter a message or select a file.");
            return;
        }

        let messageData = {
            user_id: sessionStorage.getItem("user_id"),
            group_id: window.activeChatType === "group" ? window.activeChatId : null,
            private_chat_id: window.activeChatType === "private" ? window.activeChatId : null,
            message: message || null,
            message_type: file ? (file.name.match(/\.(png|jpg|jpeg|gif)$/i) ? "image" : "file") : "text",
            timestamp: new Date().toISOString()
        };

        if (file) {
            let formData = new FormData();
            formData.append("file", file);

            try {
                let response = await fetch("/upload", {
                    method: "POST",
                    body: formData
                });

                let result = await response.json();
                console.log("📂 File Upload Response:", result);

                if (result.success && result.file_url) {
                    let cleanFileUrl = result.file_url.replace("//uploads", "/uploads");
                    messageData.message = cleanFileUrl;  // Fix: Assign file path to message
                } else {
                    console.error("❌ Error uploading file:", result.error);
                    return;
                }
            } catch (error) {
                console.error("❌ Error uploading file:", error);
                return;
            }
        }

        // displayMessage(messageData);

        socket.emit("send_message", messageData, (ack) => {
            console.log("✅ Message sent successfully:", ack);
        });

        messageInput.value = "";
        fileInput.value = "";
        if (document.getElementById("filePreview")) {
            document.getElementById("filePreview").remove();
        }
    }

    // ----------------------------- Function to handle Enter key press --------------------------------------------

    function handleEnterKey(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault(); // Prevent new line
            sendMessage();
        }
    }
});

// ------------------------------- Handle incoming WebSocket messages ------------------------------------------------

socket.on("receive_message", async (data) => {
    console.log("📩 New message received:", data);

    const isGroup = !!data.group_id;
    const chatId = isGroup ? data.group_id : data.private_chat_id;
    const chatType = isGroup ? "group" : "private";

    // Check if the message belongs to the active chat
    if (
        (window.activeChatType === "group" && chatId == window.activeChatId) ||
        (window.activeChatType === "private" && chatId == window.activeChatId)
    ) {
        console.log("🔎 Active chat:", window.activeChatType, window.activeChatId);
        await displayMessage(data);

        const sessionUserId = sessionStorage.getItem("user_id");

        if (data.user_id !== sessionUserId) {
            socket.emit("message_delivered", {
                message_id: data.id,
                user_id: sessionUserId
            });
        }
    } else {
        console.warn("⚠️ Message received for a different chat. Updating unread count...");
        updateUnreadCount(data);  // Increment unread messages
    }

    // Always move the chat to the top
    moveChatToTop(chatId, chatType);
    updateChatPreview(chatId, chatType, data.message, data.timestamp);

});

// ========================================= SEND MESSAGES FUNCTION ENDS HERE ===========================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ================================= FILE PREVIEW FUNCTION STARTS HERE ==================================================

function generateFilePreview(fileUrl, fileType) {
    if (!fileUrl) {
        console.error("❌ Missing fileUrl!");
        return "";
    }

    // Ensure the fileUrl is correctly formatted
    fileUrl = fileUrl.replace(/\/{2,}/g, "/").replace(":/", "://");

    let fileName = fileUrl.split("/").pop(); // Extract file name from URL
    let previewHtml = ""; // Declare previewHtml

    if (fileType === "image") {
        previewHtml = `
        <div class="chat-file-preview">
            <a href="${fileUrl}" target="_blank">
                <img src="${fileUrl}" class="chat-image-preview" alt="Uploaded Image">
            </a>
            <p class="file-name" style="width: 100px; font-size: 12px; color: white; margin-top: 5px;">📂 ${fileName}</p>
        </div>`;
    } else {
        previewHtml = `
        <div class="chat-file-preview">
            <a href="${fileUrl}" target="_blank" class="chat-file-link" download="${fileName}">📄 Download</a>
            <p class="file-name" style="font-size: 12px; color: white; margin-top: 5px;">📂 ${fileName}</p>
        </div>`;
    }
    console.log("📸 File preview:", previewHtml); // ✅ Corrected log

    return previewHtml; // ✅ Ensure it always returns a valid string
}

// ================================ FILE PREVIEW FUNCTION ENDS HERE =====================================================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// =============================== FUNCTION TO ADD USERS TO CHATLIST FOR PRIVATE CHAT STARTS HERE =======================================

function startPrivateChat(user_id, fullName, imageUrl) {
    // 1. FIRST REMOVE ACTIVE CLASS FROM ALL CHATS
    document.querySelectorAll(".chat-item-list").forEach(item => {
        item.classList.remove("active-chat", "active");
    });

    let chatList = document.querySelector(".content-messages-list");
    let existingChat = chatList.querySelector(`[data-user-id="${user_id}"]`);

    if (!existingChat) {
        // Create new chat item
        let chatItem = document.createElement("li");
        chatItem.setAttribute("data-user-id", user_id);
        chatItem.classList.add("chat-item-list");

        chatItem.innerHTML = `
            <a href="#" class="chat-item" data-chat-type="private">
                <div class="chat-content-list">
                    <img class="content-message-image" src="${imageUrl}" alt="Chat Image" onerror="this.src='/static/images/default-profile.png';">
                    <div class="chat-details content-message-info">
                        <span class="content-message-name">${fullName}</span>
                        <span class="content-message-text">No messages yet</span>
                        <div class="content-message-more">
                            <span class="content-message-time">-</span>
                        </div>
                    </div>
                </div>
            </a>

            <div class="chat-options">
                <button type="button" class="menu-btn" onclick="toggleMenu(this)">
                    <i class="ri-more-2-line"></i>
                </button>
                <ul class="chat-dropdown-menu">
                    <li><a href="#" class="chat-dropdown-item" onclick="deleteChat('${user_id}', this)">
                        <i class="ri-delete-bin-line"></i> Delete
                    </a></li>
                    <hr>
                    <li><a href="#" class="chat-dropdown-item" onclick="archiveChat('${user_id}', this)">
                        <i class="ri-inbox-archive-line"></i> Archive
                    </a></li>
                    <hr>
                    <li><a href="#" class="chat-dropdown-item" onclick="muteChat('${user_id}', this)">
                        <i class="ri-volume-mute-line"></i> Mute chat
                    </a></li>
                    <hr>
                    <li><a href="#" class="chat-dropdown-item" onclick="markChat('${user_id}', this)">
                        <i class="ri-check-double-line"></i> Mark as read
                    </a></li>
                </ul>
            </div>
        `;

        // Add click handler to the new chat item
        chatItem.querySelector(".chat-item").addEventListener("click", handleChatClick);
        chatList.prepend(chatItem);
        existingChat = chatItem;
    }

    // 2. ADD ACTIVE CLASS TO THE NEW/EXISTING CHAT
    existingChat.classList.add("active");

    // 3. UPDATE CHAT HEADER
    updateChatHeader(fullName, imageUrl);

    // 4. SWITCH TO THE CHAT
    switchChat(user_id, "private");

    // 5. FETCH CHAT ID FROM SERVER
    fetch("/start_private_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user_id }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Error starting chat:", data.error);
                return;
            }

            // Update the chat item with the correct chat ID
            const chatItem = existingChat.querySelector(".chat-item");
            if (chatItem) {
                chatItem.dataset.chatId = data.chat_id;
                // Update session storage with the actual chat ID
                sessionStorage.setItem("active_chat_id", data.chat_id);
                sessionStorage.setItem("active_chat_type", "private");
            }
        })
        .catch(error => console.error("Error starting private chat:", error));

    // 6. CLEAN UP SEARCH UI
    document.getElementById("searchResults").innerHTML = "";
    document.getElementById("searchInput").value = "";
}
document.getElementById("attachFileIcon").addEventListener("click", function () {
    document.getElementById("fileInput").click();
});

// Show preview when a file is selected
const fileInput = document.getElementById("fileInput");
fileInput.addEventListener("change", function () {
    let file = fileInput.files[0];
    if (file) {
        let previewContainer = document.getElementById("filePreview");
        if (!previewContainer) {
            previewContainer = document.createElement("div");
            previewContainer.id = "filePreview";
            previewContainer.style.marginBottom = "10px"; // Add spacing
            document.getElementById("chatInput").insertAdjacentElement("beforebegin", previewContainer);
        }

        let fileExt = file.name.split(".").pop().toLowerCase();
        if (["png", "jpg", "jpeg", "gif", "mp4"].includes(fileExt)) {
            // Display an image preview
            let reader = new FileReader();
            reader.onload = function (e) {
                previewContainer.innerHTML = `
                    <div style=" padding: 30px; display: flex; flex-direction: column; align-items: center; 
                    justify-content: center; gap: 3px; background-color: #f9f9f9; border-radius: 5px;">
                        <img  src="${e.target.result}" alt="${file.name}" style="max-width: 200px; border-radius: 5px;">

                        <p style="text-align: center;">${file.name}</p>
                        <button  onclick="removePreview()" style="background: red; color: white; border: none; 
                        padding: 5px; cursor: pointer; align-self: flex-end;">x</button>
                    </div>
                    
                `;
            };
            reader.readAsDataURL(file);
        } else {
            // Display file name only for non-image files
            previewContainer.innerHTML = `
                <div style="display: flex; align-items: center; text-align: center; gap: 3px; 
                background-color: #f9f9f9;">
                    <p>📂 ${file.name}</p>
                    <button onclick="removePreview()" style="background: red; color: white; 
                    border: none; padding: 5px; cursor: pointer;">x</button>
                </div>
            `;
        }
    }
});

// ---------------------------------- Function to remove file preview ---------------------------------------------------------------------------
function removePreview() {
    let previewContainer = document.getElementById("filePreview");
    if (previewContainer) {
        previewContainer.remove();
    }
    fileInput.value = ""; // Reset file input
}

// ========================================= FUNCTION TO ADD USERS TO CHATLIST FOR PRIVATE CHAT ENDS HERE =======================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ========================================= FUNCTION TO MOVE CHAT TO TOP STARTS HERE ===========================================================

// Function to move the chat to the top of the list
function moveChatToTop(chatId, chatType) {
    const chatList = document.querySelector(".content-messages-list");

    const chatItem = document.querySelector(
        `.chat-item-list .chat-item[data-chat-id="${chatId}"][data-chat-type="${chatType}"]`
    )?.closest(".chat-item-list");

    if (chatItem && chatList) {
        chatList.prepend(chatItem);
        console.log(`⬆️ Moved ${chatType} chat (ID: ${chatId}) to top`);
    } else {
        console.warn(`⚠️ Could not find chat with ID: ${chatId} and type: ${chatType} to move.`);
    }
}

// ----------------------------------------- UPDATE CHAT PREVIEW FUNCTION STARTS HERE -----------------------------------------------
// Function to update chat preview with the latest message and timestamp

function updateChatPreview(chatId, chatType, message, timestamp) {
    const chatItem = document.querySelector(
        `.chat-item-list .chat-item[data-chat-id="${chatId}"][data-chat-type="${chatType}"]`
    )?.closest(".chat-item-list");

    if (!chatItem) {
        console.warn("⚠️ Could not find chat to update preview.");
        return;
    }

    const previewTextEl = chatItem.querySelector(".content-message-text");
    if (previewTextEl) {
        previewTextEl.textContent = message;
    }

    const timeEl = chatItem.querySelector(".content-message-time");
    if (timeEl) {
        timeEl.textContent = formatTimestamp(timestamp);
    }
}

// ----------------------------------------- UPDATE CHAT PREVIEW FUNCTION ENDS HERE --------------------------------------------------

// ========================================= FUNCTION TO MOVE CHAT TO TOP ENDS HERE ==================================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ======================================= DATE CHAT GROUPING IN THE CHAT AREA STARTS HERE ===========================================
// This function shows Date time separations between chats in the chat area
// It will show the date when the message was sent in the chat area

function formatDate(dateString) {
    let date = new Date(dateString);
    let options = { weekday: "long", year: "numeric", month: "long", day: "numeric" };
    return date.toLocaleDateString(undefined, options); // Example: "Wednesday, March 20, 2025"
}

function insertDateSeparator(dateString) {
    let messagesContainer = document.getElementById("conversation-main");

    let dateSeparator = document.createElement("div");
    dateSeparator.className = "chat-date-separator";
    dateSeparator.textContent = formatDate(dateString);

    messagesContainer.appendChild(dateSeparator);
}

// ======================================= DATE CHAT GROUPING IN THE CHAT AREA ENDS HERE ==============================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ========================================= FUNCTION TO UPDATE UNREAD COUNT STARTS HERE ==============================================
// Function to update unread count and move chat to the top
function updateUnreadCount(data) {
    const chatId = data.group_id || data.private_chat_id;
    const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);

    if (chatElement) {
        let unreadBadge = chatElement.querySelector(".unread-badge");
        let unreadCount = parseInt(unreadBadge.innerText) || 0;
        unreadCount += 1; // Increment unread messages
        unreadBadge.innerText = unreadCount;
        unreadBadge.style.display = "inline-block";

        // Move chat to the top of the chat list
        let chatListContainer = document.querySelector(".content-messages-list");
        chatListContainer.prepend(chatElement);
    }
}

// ========================================= FUNCTION TO UPDATE UNREAD COUNT ENDS HERE ===============================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ======================================== FUNCTION TO UPDATE MESSAGE STATUS STARTS HERE ===============================================

socket.on("message_status_update", (data) => {
    console.log("📬 Status update received:", data); // 🔍 Log the incoming data
    const messageId = data.message_id;
    const status = data.status;

    const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!messageEl) return;

    const timestampEl = messageEl.querySelector(".timestamp");
    if (!timestampEl) return;

    // Remove previous tick
    const existingTick = timestampEl.querySelector(".tick");
    if (existingTick) existingTick.remove();

    let tickHTML = "";

    if (status === "sent") {
        tickHTML = '<span class="tick"><i class="ri-check-line"></i></span>';
    } else if (status === "delivered") {
        tickHTML = '<span class="tick"><i class="ri-check-double-line"></i></span>';
    } else if (status === "read") {
        tickHTML = '<span class="tick"><i class="ri-check-double-line" style="color: red;"></i></span>';
    } else {
        console.warn("⚠️ Unknown status received:", status);
    }

    // Append the tick
    timestampEl.insertAdjacentHTML("beforeend", tickHTML);
});

// ======================================== FUNCTION TO UPDATE MESSAGES STATUS ENDS HERE ===============================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ================================== FUNCTION TO DELETE CHAT FROM CHAT LISTS STRATS HERE ==============================================

function deleteChat(chatId, button) {
    let chatItem = button.closest(".chat-item-list"); // Find the closest chat list item

    if (chatItem) {
        chatItem.remove(); // Remove from UI
    } else {
        console.error("Chat element not found in the DOM.");
    }

    // Send request to Flask to mark chat as deleted
    fetch(`/delete_chat/${chatId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert("Error: " + data.error);
            }
        })
        .catch(error => console.error("Error deleting chat:", error));
}
// =================================== FUNCTION TO DELETE CHAT FROM CHAT LISTS ENDS HERE ===============================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ========================= FUNCTION FOR TOGGLE FUNCTIONALITIES FOR CHAT LIST ITEMS STARTS HERE =======================================

// Toggle dropdown menu visibility
function toggleMenu(button) {
    let chatOptions = button.closest(".chat-options");

    // Close any open dropdowns before opening a new one
    document.querySelectorAll(".chat-options").forEach(option => {
        if (option !== chatOptions) {
            option.classList.remove("active");
        }
    });

    // Toggle the current dropdown
    chatOptions.classList.toggle("active");
}

// Close dropdown when clicking outside
document.addEventListener("click", function (event) {
    document.querySelectorAll(".chat-options").forEach(dropdown => {
        if (!dropdown.contains(event.target) && !event.target.closest(".menu-btn")) {
            dropdown.classList.remove("active");
        }
    });
});



// ========================= FUNCTION FOR TOGGLE FUNCTIONALITIES FOR CHAT LIST ITEMS ENDS HERE =======================================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// ======================== FUNCTION TO TOGGLE CHAT ARE DROPDOWN FOR EACH CHAT MESSAGES IN THE CHAT AREA =============================

document.addEventListener('DOMContentLoaded', function () {
    // Handle dropdown toggle
    document.addEventListener('click', function (e) {
        // Toggle dropdown
        if (e.target.closest('.conversation-item-dropdown-toggle')) {
            e.preventDefault();
            const dropdown = e.target.closest('.conversation-item-dropdown');
            document.querySelectorAll('.conversation-item-dropdown').forEach(d => {
                if (d !== dropdown) d.classList.remove('active');
            });
            dropdown.classList.toggle('active');
        }

        // Close dropdowns when clicking outside
        if (!e.target.closest('.conversation-item-dropdown')) {
            document.querySelectorAll('.conversation-item-dropdown').forEach(d => {
                d.classList.remove('active');
            });
        }

        // Handle forward action
        if (e.target.closest('.forward-message')) {
            e.preventDefault();
            const messageId = e.target.closest('.forward-message').dataset.messageId;
            forwardMessage(messageId);
        }

        // Handle delete action
        if (e.target.closest('.delete-message')) {
            e.preventDefault();
            const messageId = e.target.closest('.delete-message').dataset.messageId;
            deleteMessage(messageId);
        }
    });
});

// Message action functions
function forwardMessage(messageId) {
    const messageWrapper = document.querySelector(`.message-wrapper[data-message-id="${messageId}"]`);
    const messageContent = messageWrapper.querySelector('.message-text').textContent;
    console.log('Forwarding message:', messageId, messageContent);
    // Implement your forward logic here
    alert(`Forwarding message ${messageId}`);
}

function deleteMessage(messageId) {
    if (confirm('Are you sure you want to delete this message?')) {
        const messageWrapper = document.querySelector(`.message-wrapper[data-message-id="${messageId}"]`);
        if (messageWrapper) {
            messageWrapper.remove();
            // Add your API call to delete from server here
            console.log('Deleted message:', messageId);
        }
    }
}

// ======================== FUNCTION TO TOGGLE CHAT ARE DROPDOWN FOR EACH CHAT MESSAGES IN THE CHAT AREA =============================
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx