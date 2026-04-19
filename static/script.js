(function () {
  // Elements
  var userIdInput = document.getElementById("userId");
  var startBtn = document.getElementById("startBtn");
  var statusEl = document.getElementById("status");
  var messagesEl = document.getElementById("messages");
  var composer = document.getElementById("composer");
  var messageInput = document.getElementById("messageInput");
  var sendBtn = document.getElementById("sendBtn");

  var currentUserId = localStorage.getItem("roaming_user_id") || "";

  // isNewConversation flag: true means tell server to create a fresh session
  // If we restored a user id from localStorage we assume it's an ongoing conversation (false).
  // If there's no stored user id, treat next message as new conversation (true).
  var isNewConversation = !currentUserId;

  // Initialize UI with stored user id if present
  if (currentUserId) {
    userIdInput.value = currentUserId;
    statusEl.textContent = "Using ID: " + currentUserId;
  }

  // Helper: append message
  function appendMessage(text, who) {
    var wrap = document.createElement("div");
    wrap.className = "message " + (who === "user" ? "msg-user" : "msg-bot");
    wrap.textContent = text;
    messagesEl.appendChild(wrap);
    // robust scroll to bottom
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  // Helper: display status
  function setStatus(text) {
    statusEl.textContent = text || "";
  }

  // Start / set id
  startBtn.addEventListener("click", function () {
    var val = userIdInput.value.trim();
    if (!val) {
      setStatus("Enter a user id first.");
      return;
    }
    currentUserId = val;
    localStorage.setItem("roaming_user_id", val);
    setStatus("Using ID: " + val);

    // mark that the next message should create a new conversation on the server
    isNewConversation = true;

    // optional: clear chat area for a new session
    messagesEl.innerHTML = "";
    appendMessage("Session started for user: " + val, "bot");

    // ensure send button / input focus ready
    messageInput.focus();
  });

  // Send a message to /conversation
  function sendMessage(text) {
    if (!currentUserId) {
      setStatus("Set a user id first and click Start.");
      return;
    }
    if (!text || !text.trim()) return;

    // UI feedback
    appendMessage(text, "user");
    messageInput.value = "";
    setStatus("Sending...");
    sendBtn.disabled = true;
    startBtn.disabled = true;
    userIdInput.disabled = true;

    // include the is_new_conversation flag in the payload
    fetch("/conversation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: currentUserId,
        user_input: text,
        is_new_conversation: isNewConversation
      })
    })
      .then(function (r) {
        if (!r.ok) throw new Error("Server error: " + r.status);
        return r.json();
      })
      .then(function (data) {
        // Expecting { bot: "...", state?: "..." }
        var botText = data.bot || JSON.stringify(data);
        appendMessage(botText, "bot");
        setStatus("");
        // After a successful send that used the is_new flag,
        // subsequent messages should be treated as part of the existing session.
        isNewConversation = false;
      })
      .catch(function (err) {
        console.error(err);
        appendMessage("Error: " + (err.message || err), "bot");
        setStatus("Request failed");
      })
      .finally(function () {
        sendBtn.disabled = false;
        startBtn.disabled = false;
        userIdInput.disabled = false;
        messageInput.focus();
      });
  }

  // Submit composer form
  composer.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var text = messageInput.value;
    sendMessage(text);
  });

  // allow pressing Enter in message input to send
  messageInput.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      composer.requestSubmit();
    }
  });
})();
