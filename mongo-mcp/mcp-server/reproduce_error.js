import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

async function testError() {
    const uri = process.env.MONGO_URI;
    const client = new MongoClient(uri);

    try {
        await client.connect();
        console.log("Connected");

        const db = client.db(process.env.MONGO_DB);

        // Test with empty collection name
        try {
            console.log("Testing empty collection name...");
            const col = db.collection("");
            await col.find({}).toArray();
        } catch (e) {
            console.log("Error with empty collection:", e.message);
        }

        // Test with undefined
        try {
            console.log("Testing undefined collection name...");
            const col = db.collection(undefined);
            await col.find({}).toArray();
        } catch (e) {
            console.log("Error with undefined collection:", e.message);
        }

    } catch (err) {
        console.error("Global error:", err);
    } finally {
        await client.close();
    }
}

testError();
