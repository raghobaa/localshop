import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

// Configuration
const LOCAL_URI = "mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.5.8";
const ATLAS_URI = process.env.MONGO_URI;
const TARGET_DB = "test"; // Explicitly targeting 'test'

async function migrateSellersToTest() {
    const localClient = new MongoClient(LOCAL_URI);
    const atlasClient = new MongoClient(ATLAS_URI);

    try {
        console.log("🔄 Connecting to databases...");
        await localClient.connect();
        await atlasClient.connect();
        console.log("✅ Connected to both databases");

        const localDb = localClient.db("mydatabase");
        const atlasDb = atlasClient.db(TARGET_DB);

        // 1. Get Sellers from Local
        const localCollection = localDb.collection("seller");
        const documents = await localCollection.find({}).toArray();

        if (documents.length === 0) {
            console.log("⚠️ No sellers found locally.");
            return;
        }

        console.log(`\n📦 Found ${documents.length} sellers locally.`);

        // 2. Insert into Atlas 'test' DB
        const atlasCollection = atlasDb.collection("seller");

        for (const doc of documents) {
            const exists = await atlasCollection.findOne({ username: doc.username });
            if (!exists) {
                await atlasCollection.insertOne(doc);
                console.log(`✅ Migrated seller to 'test' DB: ${doc.username}`);
            } else {
                console.log(`⚠️ Seller '${doc.username}' already exists in 'test' DB. Skipping.`);
            }
        }

        console.log("\n🚀 Seller migration to 'test' DB complete!");

    } catch (err) {
        console.error("❌ Migration Error:", err);
    } finally {
        await localClient.close();
        await atlasClient.close();
    }
}

migrateSellersToTest();
