import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

async function checkSellers() {
    const uri = process.env.MONGO_URI;
    const dbName = process.env.MONGO_DB; // Should be 'test'

    const client = new MongoClient(uri);

    try {
        await client.connect();
        console.log(`✅ Connected to Atlas DB: '${dbName}'`);

        const db = client.db(dbName);
        const collection = db.collection("seller");

        const sellers = await collection.find({}).toArray();

        console.log(`\n📊 Found ${sellers.length} sellers:`);
        sellers.forEach((s, i) => {
            console.log(`${i + 1}. ${s.username} (${s.storename || 'No Store Name'}) - ${s.email}`);
        });

    } catch (err) {
        console.error("❌ Error:", err);
    } finally {
        await client.close();
    }
}

checkSellers();
