import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

// Configuration
const LOCAL_URI = "mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.5.8";
const ATLAS_URI = process.env.MONGO_URI; // Already updated in .env
const DB_NAME = process.env.MONGO_DB || "mydatabase";

async function migrateInventory() {
    const localClient = new MongoClient(LOCAL_URI);
    const atlasClient = new MongoClient(ATLAS_URI);

    try {
        console.log("🔄 Connecting to databases...");
        await localClient.connect();
        console.log("✅ Connected to Local MongoDB");

        await atlasClient.connect();
        console.log("✅ Connected to Atlas MongoDB");

        const localDb = localClient.db(DB_NAME);
        const atlasDb = atlasClient.db(DB_NAME);

        // 1. Get data from Local
        const localCollection = localDb.collection("inventory");
        const documents = await localCollection.find({}).toArray();

        if (documents.length === 0) {
            console.log("⚠️ No documents found in local inventory collection.");
            return;
        }

        console.log(`\n📦 Found ${documents.length} documents in local inventory.`);

        // 2. Insert into Atlas
        const atlasCollection = atlasDb.collection("inventory");

        // Optional: Clear existing Atlas inventory to avoid duplicates?
        // await atlasCollection.deleteMany({}); 
        // console.log("🧹 Cleared existing Atlas inventory");

        const result = await atlasCollection.insertMany(documents);
        console.log(`\n🚀 Successfully migrated ${result.insertedCount} documents to Atlas!`);

        // 3. Verify
        console.log("\n🔍 Verifying Atlas data:");
        const atlasDocs = await atlasCollection.find({}).toArray();
        atlasDocs.forEach(doc => {
            console.log(`- ${doc.productName} (${doc.username})`);
        });

    } catch (err) {
        console.error("❌ Migration Error:", err);
    } finally {
        await localClient.close();
        await atlasClient.close();
    }
}

migrateInventory();
