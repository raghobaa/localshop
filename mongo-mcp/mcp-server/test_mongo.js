import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

async function testConnection() {
    const uri = process.env.MONGO_URI;
    const client = new MongoClient(uri);

    try {
        await client.connect();
        console.log("Connected successfully to server");

        const db = client.db(process.env.MONGO_DB);
        const collection = db.collection("hack");

        // Insert a document
        const insertResult = await collection.insertOne({ name: "Test Hack", created_at: new Date() });
        console.log("Inserted document into 'hack' collection:", insertResult.insertedId);

        // Find the document
        const findResult = await collection.findOne({ _id: insertResult.insertedId });
        console.log("Found document:", findResult);

        console.log("Test successful!");
    } catch (err) {
        console.error("An error occurred:", err);
    } finally {
        await client.close();
    }
}

testConnection();
