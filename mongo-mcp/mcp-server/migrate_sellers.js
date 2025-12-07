import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

// Configuration
const LOCAL_URI = "mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.5.8";
const ATLAS_URI = process.env.MONGO_URI;
const DB_NAME = process.env.MONGO_DB || "mydatabase"; // Using the DB configured in .env

async function migrateSellers() {
    const localClient = new MongoClient(LOCAL_URI);
    const atlasClient = new MongoClient(ATLAS_URI);

    try {
        console.log("🔄 Connecting to databases...");
        await localClient.connect();
        await atlasClient.connect();
        console.log("✅ Connected to both databases");

        const localDb = localClient.db("mydatabase"); // Source is always local 'mydatabase'
        const atlasDb = atlasClient.db(DB_NAME);

        // 1. Get Sellers from Local
        const localCollection = localDb.collection("seller");
        const documents = await localCollection.find({}).toArray();

        if (documents.length === 0) {
            console.log("⚠️ No sellers found locally.");
            return;
        }

        console.log(`\n📦 Found ${documents.length} sellers locally.`);

        // 2. Insert into Atlas
        const atlasCollection = atlasDb.collection("seller");

        // Check if sellers already exist to avoid duplicates
        for (const doc of documents) {
            const exists = await atlasCollection.findOne({ username: doc.username });
            if (!exists) {
                await atlasCollection.insertOne(doc);
                console.log(`✅ Migrated seller: ${doc.username}`);
            } else {
                console.log(`⚠️ Seller '${doc.username}' already exists in Atlas. Skipping.`);
            }
        }

        console.log("\n🚀 Seller migration complete!");

    } catch (err) {
        console.error("❌ Migration Error:", err);
    } finally {
        await localClient.close();
        await atlasClient.close();
    }
}

migrateSellers();
