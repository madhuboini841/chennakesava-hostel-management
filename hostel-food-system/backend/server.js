const { spawn, spawnSync } = require('child_process');

console.log("Starting Python Flask App via Node Bridge...");

const port = process.env.PORT || 10000;
const host = '0.0.0.0';

// Initialize the database
console.log("Initializing database...");
const initProcess = spawnSync('python3', ['init_db.py'], {
    env: { ...process.env, PYTHONPATH: './pypackages' }
});
console.log(`Init DB Output: ${initProcess.stdout.toString()}`);
if (initProcess.stderr.toString()) {
    console.error(`Init DB Error: ${initProcess.stderr.toString()}`);
}

// Spawn gunicorn to serve the Flask app
const pythonProcess = spawn('python3', ['-m', 'gunicorn', 'app:app', '--bind', `${host}:${port}`], {
    env: { ...process.env, PYTHONPATH: './pypackages' }
});

pythonProcess.stdout.on('data', (data) => {
    process.stdout.write(`Python: ${data}`);
});

pythonProcess.stderr.on('data', (data) => {
    process.stderr.write(`Python Error: ${data}`);
});

pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    process.exit(code);
});
