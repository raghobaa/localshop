import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

async function setupSeller() {
    const uri = process.env.MONGO_URI;
    const client = new MongoClient(uri);

    try {
        await client.connect();
        console.log("✅ Connected to MongoDB\n");

        const db = client.db(process.env.MONGO_DB);
        const collection = db.collection("seller");

        // Check if seller exists
        const existing = await collection.findOne({ username: "aa" });

        if (existing) {
            console.log("✅ Seller 'aa' already exists!");
            console.log(JSON.stringify(existing, null, 2));
        } else {
            // Create the seller
            const seller = {
                username: "aa",
                email: "raj@gmail.com",
                password: "111111",
                location: "Bengaluru"
            };

            const result = await collection.insertOne(seller);
            console.log("✅ Seller created!");
            console.log("Inserted ID:", result.insertedId);
            console.log("\nSeller details:");
            console.log(JSON.stringify(seller, null, 2));
        }

        console.log("\n📊 Current sellers in database:");
        const allSellers = await collection.find({}).toArray();
        console.log(`Total: ${allSellers.length}`);
        allSellers.forEach((seller, idx) => {
            console.log(`\n${idx + 1}. Username: ${seller.username}`);
            console.log(`   Email: ${seller.email}`);
            console.log(`   Location: ${seller.location}`);
        });

    } catch (err) {
        console.error("❌ Error:", err);
    } finally {
        await client.close();
    }
}

setupSeller();
