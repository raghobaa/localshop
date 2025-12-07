import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

async function addProductsForUser() {
    const uri = process.env.MONGO_URI;
    const client = new MongoClient(uri);

    try {
        await client.connect();
        console.log("✅ Connected to MongoDB");

        const db = client.db(process.env.MONGO_DB);
        const collection = db.collection("inventory");

        const username = "aa";

        const products = [
            {
                username: username,
                productName: "Fresh Milk",
                price: 60,
                stock: 50,
                category: "Dairy",
                expiryDate: "30-11-2025",
                createdAt: new Date()
            },
            {
                username: username,
                productName: "Farm Eggs (12 pack)",
                price: 120,
                stock: 100,
                category: "Dairy",
                expiryDate: "15-12-2025",
                createdAt: new Date()
            },
            {
                username: username,
                productName: "Whole Wheat Bread",
                price: 45,
                stock: 30,
                category: "Snacks",
                expiryDate: "05-12-2025",
                createdAt: new Date()
            },
            {
                username: username,
                productName: "Organic Apples",
                price: 180,
                stock: 75,
                category: "Fruits",
                expiryDate: "20-12-2025",
                createdAt: new Date()
            },
            {
                username: username,
                productName: "Potato Chips",
                price: 20,
                stock: 200,
                category: "Snacks",
                expiryDate: "01-06-2026",
                createdAt: new Date()
            }
        ];

        const result = await collection.insertMany(products);
        console.log(`✅ Successfully added ${result.insertedCount} products for user '${username}'!`);

        console.log("\n📦 Added Products:");
        products.forEach(p => {
            console.log(`- ${p.productName} (₹${p.price}) [${p.category}]`);
        });

    } catch (err) {
        console.error("❌ Error:", err);
    } finally {
        await client.close();
    }
}

addProductsForUser();
