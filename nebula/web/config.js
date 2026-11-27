// Where the game server is. Local pages (localhost, 127.0.0.1) use their own server.
// The deployed website calls the hosted backend.
window.NEBULA_API = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname) ? "" : "https://asteroids.ethiodeploy.app";
