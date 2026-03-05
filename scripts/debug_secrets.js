const fs = require('fs');
const path = require('path');

try {
    const envPath = path.resolve(__dirname, '../.env');
    const envContent = fs.readFileSync(envPath, 'utf8');
    const secretLine = envContent.split('\n').find(line => line.startsWith('AUTH_SECRET='));
    const secret = secretLine ? secretLine.split('=')[1].trim() : null;

    console.log(`NODE SECRET: ${secret ? secret.substring(0, 5) + '...' : 'None'}`);
} catch (e) {
    console.error("Error reading .env:", e.message);
}
