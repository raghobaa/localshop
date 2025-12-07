import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

async function addMissingSellers() {
    const uri = process.env.MONGO_URI;
    const dbName = process.env.MONGO_DB; // 'test'

    const client = new MongoClient(uri);

    try {
        await client.connect();
        console.log(`✅ Connected to Atlas DB: '${dbName}'`);

        const db = client.db(dbName);
        const collection = db.collection("seller");

        // The 4 users provided
        const newSellers = [
            {
                username: "Raj",
                storename: "Raj PetHouse",
                email: "raj@gmail.com",
                password: "12344",
                storetype: "Pet Shops",
                location: "Bengaluru",
                createdAt: new Date()
            },
            {
                username: "kamal",
                storename: "kamal texmart",
                email: "kamal@gmail.com",
                password: "$2b$10$mhUoZjZCP6wX7qRC/u01MO8l8supYumISZw8x4pPvBCPDklg5L7uy",
                storetype: "Clothing Boutiques",
                location: "Bengaluru",
                createdAt: new Date()
            },
            {
                username: "sham",
                storename: "sham grocery",
                email: "sham@gmail.com",
                password: "$2b$10$pPaH1ZcPD.yl.f/6uaM/GOo1sywzAm5BQgCvh/y0T8TXzCJMkFZHe",
                storetype: "Grocery Stores",
                location: "mysore",
                createdAt: new Date()
            },
            {
                username: "mini",
                storename: "mini store",
                email: "mini@gmail.com",
                password: "$2b$10$RcEm73pbxm6AOp5qfDvGBO.wcTeJDiVpaURIyEcrpPyT1zOLok71u",
                storetype: "Convenience Stores",
                location: "Benagluru",
                createdAt: new Date()
            }
        ];

        // Insert only if they don't exist
        for (const seller of newSellers) {
            const exists = await collection.findOne({ username: seller.username });
            if (!exists) {
                await collection.insertOne(seller);
                console.log(`✅ Added seller: ${seller.username}`);
            } else {
                console.log(`⚠️ Seller '${seller.username}' already exists.`);
            }
        }

    } catch (err) {
        console.error("❌ Error:", err);
    } finally {
        await client.close();
    }
}

addMissingSellers();
