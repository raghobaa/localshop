import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

async function insertSeller() {
    const uri = process.env.MONGO_URI;
    const client = new MongoClient(uri);

    try {
        await client.connect();
        console.log("Connected to MongoDB");

        const db = client.db(process.env.MONGO_DB);
        const collection = db.collection("seller");

        const document = {
            seller: "Raghav Store",
            product: "Apple",
            type: "Fruit",
            price: 120,
            no_of_items: 50,
            code: "APL120"
        };

        const result = await collection.insertOne(document);
        console.log("Document inserted successfully!");
        console.log("Inserted ID:", result.insertedId);

        // Verify by finding the document
        const inserted = await collection.findOne({ _id: result.insertedId });
        console.log("\nInserted document:");
        console.log(inserted);

    } catch (err) {
        console.error("Error:", err);
    } finally {
        await client.close();
    }
}

insertSeller();
