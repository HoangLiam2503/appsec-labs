// Shared in-memory message store + seed. Reset on restart (fine for a lab).
const messages = [];

function seed() {
  messages.length = 0;
  messages.push({ name: "alice", message: "First! Welcome to the guestbook." });
  messages.push({ name: "bob", message: "Nice board :)" });
}

function add(name, message) {
  messages.push({ name, message });
}

function all() {
  return messages;
}

module.exports = { seed, add, all };
