const socket = io();
let username = '';
let avatar = '';
let currentRoom = 'General';

function connectToRoom() {
  username = document.getElementById('username').value.trim();
  avatar = document.getElementById('avatar').value;
  if (!username) return alert("Enter a username");

  document.getElementById('currentRoom').innerText = `Room: ${currentRoom}`;
  socket.emit('join', { room: currentRoom, username, avatar });
  loadChatHistory(currentRoom);
}

function switchRoom(room) {
  currentRoom = room;
  document.getElementById('currentRoom').innerText = `Room: ${currentRoom}`;
  socket.emit('join', { room, username, avatar });
  loadChatHistory(room);
}

function sendMessage() {
  const text = document.getElementById('message').value;
  if (!text) return;

  socket.emit('message', { room: currentRoom, username, avatar, text });
  document.getElementById('message').value = '';
}

function uploadFile() {
  const fileInput = document.getElementById('fileInput');
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("username", username);
  formData.append("avatar", avatar);
  formData.append("room", currentRoom);

  fetch("/upload", { method: "POST", body: formData });
  fileInput.value = '';
}

socket.on("message", data => {
  if (data.room === currentRoom) appendMessage(data);
});

socket.on("file_shared", data => {
  if (data.room === currentRoom) appendMessage(data, true);
});

function appendMessage(data, isFile = false) {
  const li = document.createElement("li");
  let content = `<div><b>${data.avatar} ${data.username}</b></div>`;
  if (isFile) {
    const ext = data.filename.split('.').pop().toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif'].includes(ext)) {
      content += `<img src="${data.file_url}" width="200">`;
    } else if (['mp4', 'webm'].includes(ext)) {
      content += `<video src="${data.file_url}" controls width="250"></video>`;
    } else if (['mp3', 'wav'].includes(ext)) {
      content += `<audio src="${data.file_url}" controls></audio>`;
    } else {
      content += `<a href="${data.file_url}" download>${data.filename}</a>`;
    }
  } else {
    content += `<p>${data.text}</p>`;
  }
  li.innerHTML = content;
  document.getElementById('messages').appendChild(li);
  scrollToBottom();
}

function loadChatHistory(room) {
  fetch(`/messages/${room}`)
    .then(res => res.json())
    .then(messages => {
      document.getElementById('messages').innerHTML = '';
      messages.forEach(m => {
        appendMessage(m, m.file_url != null);
      });
    });
}

function scrollToBottom() {
  const msgList = document.getElementById('messages');
  msgList.scrollTop = msgList.scrollHeight;
}
