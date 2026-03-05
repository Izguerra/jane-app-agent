const Stripe = require('stripe');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// Load .env from root
const envPath = path.resolve(__dirname, '../.env');
const envConfig = dotenv.parse(fs.readFileSync(envPath));

const stripe = new Stripe(envConfig.STRIPE_SECRET_KEY);

async function main() {
    try {
        console.log('Fetching Products and Prices...');
        const products = await stripe.products.list({ active: true, expand: ['data.default_price'] });
        const prices = await stripe.prices.list({ active: true, expand: ['data.product'] });

        console.log('\n--- Products ---');
        products.data.forEach(p => {
            console.log(`Product: ${p.name} (${p.id})`);
        });

        console.log('\n--- Prices ---');
        prices.data.forEach(p => {
            const productName = typeof p.product === 'string' ? p.product : p.product.name;
            const amount = p.unit_amount / 100;
            const currency = p.currency.toUpperCase();
            const interval = p.recurring ? p.recurring.interval : 'one-time';
            console.log(`Price: ${amount} ${currency} / ${interval} - Product: ${productName} - ID: ${p.id}`);
        });

    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

main();
