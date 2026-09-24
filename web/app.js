const params = new URLSearchParams(window.location.search);
const roomId = params.get("room") || "";
const token = params.get("token") || "";

const joinPanel = document.getElementById("joinPanel");
const roomPanel = document.getElementById("roomPanel");
const inviteStatus = document.getElementById("inviteStatus");
const displayName = document.getElementById("displayName");
const joinButton = document.getElementById("joinButton");
const joinError = document.getElementById("joinError");
const roomTitle = document.getElementById("roomTitle");
const connectionStatus = document.getElementById("connectionStatus");
const participantList = document.getElementById("participantList");
const muteButton = document.getElementById("muteButton");
const speakerButton = document.getElementById("speakerButton");
const leaveButton = document.getElementById("leaveButton");
const roomError = document.getElementById("roomError");
const remoteAudio = document.getElementById("remoteAudio");

let localStream = null;
let socket = null;
let clientId = null;
let iceServers = [];
let muted = false;
let remoteMuted = false;
let reconnectAttempts = 0;
let intentionallyLeft = false;
const peers = new Map();
const participants = new Map();

function setError(text) {
  joinError.textContent = text || "";
  roomError.textContent = text || "";
}

function setConnection(text) {
  connectionStatus.textContent = text;
}

async function validateInvite() {
  if (!roomId) {
    inviteStatus.textContent = "Invalid or expired invitation";
    joinButton.disabled = true;
    return;
  }
  try {
    const response = await fetch(`/api/validate-invite?room=${encodeURIComponent(roomId)}&token=${encodeURIComponent(token)}`);
    if (!response.ok) throw new Error("Invalid or expired invitation");
    inviteStatus.textContent = `Room ${roomId}`;
  } catch (error) {
    inviteStatus.textContent = error.message;
    joinButton.disabled = true;
  }
}

async function loadWebRtcConfig() {
  const response = await fetch("/api/webrtc-config");
  const data = await response.json();
  iceServers = data.iceServers || [];
}

async function joinRoom() {
  setError("");
  if (!window.RTCPeerConnection || !navigator.mediaDevices?.getUserMedia) {
    setError("WebRTC or microphone access is not supported in this browser.");
    return;
  }
  const name = (displayName.value || "Guest").trim().slice(0, 40);
  try {
    await loadWebRtcConfig();
    localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  } catch (error) {
    setError("Microphone permission was denied or no microphone was found.");
    return;
  }
  participants.set("local", { name, speaking: false });
  roomTitle.textContent = `Room ${roomId}`;
  joinPanel.classList.add("hidden");
  roomPanel.classList.remove("hidden");
  renderParticipants();
  intentionallyLeft = false;
  connectSocket(name);
}

function connectSocket(name) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${protocol}//${window.location.host}/ws?room=${encodeURIComponent(roomId)}&token=${encodeURIComponent(token)}&name=${encodeURIComponent(name)}`;
  socket = new WebSocket(url);
  setConnection("Connecting");

  socket.addEventListener("open", () => {
    reconnectAttempts = 0;
    setConnection("Connected");
  });

  socket.addEventListener("message", async (event) => {
    const message = JSON.parse(event.data);
    await handleSignal(message);
  });

  socket.addEventListener("close", () => {
    setConnection("Disconnected");
    if (!intentionallyLeft) scheduleReconnect(name);
  });
}

function scheduleReconnect(name) {
  reconnectAttempts += 1;
  const delays = [1000, 2000, 5000, 10000];
  const delay = delays[Math.min(reconnectAttempts - 1, delays.length - 1)];
  setConnection("Reconnecting");
  setTimeout(() => {
    if (!intentionallyLeft) connectSocket(name);
  }, delay);
}

async function handleSignal(message) {
  if (message.type === "error") {
    setError(message.message || "Connection error");
    return;
  }
  if (message.type === "joined") {
    clientId = message.clientId;
    for (const peer of message.peers || []) {
      participants.set(peer.clientId, { name: peer.name, speaking: false });
      await createPeer(peer.clientId, true);
    }
    renderParticipants();
    return;
  }
  if (message.type === "peer-joined") {
    participants.set(message.peer.clientId, { name: message.peer.name, speaking: false });
    renderParticipants();
    return;
  }
  if (message.type === "offer") {
    const pc = await createPeer(message.from, false);
    await pc.setRemoteDescription(message.sdp);
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);
    send({ type: "answer", target: message.from, sdp: pc.localDescription });
    return;
  }
  if (message.type === "answer") {
    const pc = peers.get(message.from);
    if (pc) await pc.setRemoteDescription(message.sdp);
    return;
  }
  if (message.type === "ice") {
    const pc = peers.get(message.from);
    if (pc && message.candidate) await pc.addIceCandidate(message.candidate);
    return;
  }
  if (message.type === "peer-left") {
    closePeer(message.clientId);
    participants.delete(message.clientId);
    renderParticipants();
    return;
  }
  if (message.type === "speaking") {
    const participant = participants.get(message.clientId);
    if (participant) participant.speaking = message.speaking;
    renderParticipants();
  }
}

async function createPeer(peerId, initiator) {
  if (peers.has(peerId)) return peers.get(peerId);
  const pc = new RTCPeerConnection({ iceServers });
  peers.set(peerId, pc);
  for (const track of localStream.getAudioTracks()) {
    pc.addTrack(track, localStream);
  }
  pc.addEventListener("icecandidate", (event) => {
    if (event.candidate) send({ type: "ice", target: peerId, candidate: event.candidate });
  });
  pc.addEventListener("track", (event) => attachAudio(peerId, event.streams[0]));
  pc.addEventListener("connectionstatechange", () => {
    if (["failed", "disconnected", "closed"].includes(pc.connectionState)) {
      setConnection(pc.connectionState === "failed" ? "Unable to establish peer connection. This network may require a TURN relay." : "Connected");
    }
  });
  if (initiator) {
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    send({ type: "offer", target: peerId, sdp: pc.localDescription });
  }
  return pc;
}

function attachAudio(peerId, stream) {
  let audio = document.getElementById(`audio-${peerId}`);
  if (!audio) {
    audio = document.createElement("audio");
    audio.id = `audio-${peerId}`;
    audio.autoplay = true;
    audio.playsInline = true;
    remoteAudio.appendChild(audio);
  }
  audio.srcObject = stream;
  audio.muted = remoteMuted;
  audio.play().catch(() => {});
}

function closePeer(peerId) {
  const pc = peers.get(peerId);
  if (pc) pc.close();
  peers.delete(peerId);
  document.getElementById(`audio-${peerId}`)?.remove();
}

function send(message) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(message));
  }
}

function renderParticipants() {
  participantList.innerHTML = "";
  for (const [id, participant] of participants.entries()) {
    const li = document.createElement("li");
    if (participant.speaking) li.classList.add("speaking");
    li.textContent = id === "local" ? `${participant.name} (you)` : participant.name;
    participantList.appendChild(li);
  }
}

muteButton.addEventListener("click", () => {
  muted = !muted;
  for (const track of localStream?.getAudioTracks() || []) {
    track.enabled = !muted;
  }
  muteButton.textContent = muted ? "MUTED" : "MIC ON";
  muteButton.classList.toggle("muted", muted);
});

speakerButton.addEventListener("click", () => {
  remoteMuted = !remoteMuted;
  for (const audio of remoteAudio.querySelectorAll("audio")) {
    audio.muted = remoteMuted;
  }
  speakerButton.textContent = remoteMuted ? "REMOTE AUDIO MUTED" : "REMOTE AUDIO ON";
});

leaveButton.addEventListener("click", () => {
  intentionallyLeft = true;
  send({ type: "leave" });
  socket?.close();
  for (const peerId of peers.keys()) closePeer(peerId);
  for (const track of localStream?.getTracks() || []) track.stop();
  window.location.reload();
});

joinButton.addEventListener("click", joinRoom);
displayName.addEventListener("keydown", (event) => {
  if (event.key === "Enter") joinRoom();
});

validateInvite();

