import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

async function verifyData() {
    const uri = process.env.MONGO_URI;
    const client = new MongoClient(uri);

    try {
        await client.connect();
        console.log("✅ Connected to MongoDB\n");

        const db = client.db(process.env.MONGO_DB);
        const collection = db.collection("seller");

        // Count total documents
        const count = await collection.countDocuments();
        console.log(`📊 Total documents in 'seller' collection: ${count}\n`);

        // Get all documents
        const documents = await collection.find({}).toArray();

        console.log("📄 All documents in database:\n");
        documents.forEach((doc, index) => {
            console.log(`Document ${index + 1}:`);
            console.log(JSON.stringify(doc, null, 2));
            console.log("---");
        });

        // Test update
        console.log("\n🧪 Testing update on Apple...");
        const updateResult = await collection.updateOne(
            { product: "Apple" },
            { $set: { price: 999 } }
        );
        console.log(`Matched: ${updateResult.matchedCount}, Modified: ${updateResult.modifiedCount}`);

        // Verify update
        const updatedDoc = await collection.findOne({ product: "Apple" });
        console.log("\n✅ Apple after update:");
        console.log(JSON.stringify(updatedDoc, null, 2));

        // Restore original price
        await collection.updateOne(
            { product: "Apple" },
            { $set: { price: 120 } }
        );
        console.log("\n🔄 Restored Apple to original price (120)");

    } catch (err) {
        console.error("❌ Error:", err);
    } finally {
        await client.close();
    }
}

verifyData();
