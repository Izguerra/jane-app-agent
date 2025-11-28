const net = require('net');

const client = new net.Socket();

client.connect(54322, '127.0.0.1', function() {
	console.log('Connected to 127.0.0.1:54322');
	client.destroy();
});

client.on('error', function(err) {
	console.log('Error connecting to 127.0.0.1:54322: ' + err.message);
});

const client2 = new net.Socket();
client2.connect(54322, 'localhost', function() {
    console.log('Connected to localhost:54322');
    client2.destroy();
});

client2.on('error', function(err) {
    console.log('Error connecting to localhost:54322: ' + err.message);
});

