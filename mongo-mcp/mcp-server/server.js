import express from "express";
import dotenv from "dotenv";
import { MongoClient } from "mongodb";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

dotenv.config();

const app = express();
app.use(express.json());

const client = new MongoClient(process.env.MONGO_URI);
await client.connect();
const db = client.db(process.env.MONGO_DB);

// ----------------------------
// MCP Server (for AI integration)
// ----------------------------
const mcp = new McpServer({
    name: "mongo-mcp-server",
    version: "1.0.0",
});

// Helper to validate collection
const validateCollection = (collection) => {
    if (!collection || typeof collection !== 'string' || collection.trim() === '') {
        throw new Error("Collection name is required and cannot be empty.");
    }
    return collection.trim();
};

// Query
mcp.tool("queryDocuments", async ({ collection, filter = {} }) => {
    const colName = validateCollection(collection);
    return await db.collection(colName).find(filter).toArray();
});

// Insert
mcp.tool("insertDocument", async ({ collection, document }) => {
    const colName = validateCollection(collection);
    const result = await db.collection(colName).insertOne(document);
    return { insertedId: result.insertedId };
});

// Update
mcp.tool("updateDocument", async ({ collection, filter, update }) => {
    const colName = validateCollection(collection);
    const result = await db.collection(colName).updateMany(filter, update);
    return { matched: result.matchedCount, modified: result.modifiedCount };
});

// Delete
mcp.tool("deleteDocument", async ({ collection, filter }) => {
    const colName = validateCollection(collection);
    const result = await db.collection(colName).deleteMany(filter);
    return { deleted: result.deletedCount };
});

// Add Product to Inventory
mcp.tool("addProduct", async ({ username, product }) => {
    const collection = db.collection("inventory");

    // Add username to product
    const productWithUser = {
        ...product,
        username: username,
        createdAt: new Date()
    };

    const result = await collection.insertOne(productWithUser);
    return { insertedId: result.insertedId, success: true };
});

// Get Inventory by Username
mcp.tool("getInventory", async ({ username }) => {
    const collection = db.collection("inventory");
    const products = await collection.find({ username: username }).toArray();
    return products;
});

// Update Product in Inventory
mcp.tool("updateProduct", async ({ productId, updates }) => {
    const collection = db.collection("inventory");
    const { ObjectId } = await import('mongodb');

    const result = await collection.updateOne(
        { _id: new ObjectId(productId) },
        { $set: { ...updates, updatedAt: new Date() } }
    );

    return {
        matched: result.matchedCount,
        modified: result.modifiedCount,
        success: result.modifiedCount > 0
    };
});

// Delete Product from Inventory
mcp.tool("deleteProduct", async ({ productId }) => {
    const collection = db.collection("inventory");
    const { ObjectId } = await import('mongodb');

    const result = await collection.deleteOne({ _id: new ObjectId(productId) });
    return {
        deleted: result.deletedCount,
        success: result.deletedCount > 0
    };
});

// Get All Sellers
mcp.tool("getAllSellers", async () => {
    const collection = db.collection("seller");
    const sellers = await collection.find({}).toArray();
    return sellers;
});

// ----------------------------
// New Tools for Recommendations
// ----------------------------

// Get Purchase History
mcp.tool("getPurchaseHistory", async ({ username, limit = 50 }) => {
    const collection = db.collection("purchases");
    const history = await collection
        .find({ username: username })
        .sort({ purchaseDate: -1 })
        .limit(limit)
        .toArray();
    return history;
});

// Record Purchase
mcp.tool("recordPurchase", async ({ username, productId, productName, category, sellerType, seller, price }) => {
    const collection = db.collection("purchases");
    const purchase = {
        username,
        productId,
        productName,
        category,
        sellerType,
        seller,
        price: parseFloat(price),
        purchaseDate: new Date()
    };

    const result = await collection.insertOne(purchase);

    // Also update stock in inventory
    if (productId) {
        try {
            const { ObjectId } = await import('mongodb');
            await db.collection("inventory").updateOne(
                { _id: new ObjectId(productId) },
                { $inc: { stock: -1 } }
            );
        } catch (e) {
            console.error("Failed to update stock:", e);
        }
    }

    return { insertedId: result.insertedId, success: true };
});

// Get Products By Category
mcp.tool("getProductsByCategory", async ({ category, excludeUsername, limit = 20 }) => {
    const collection = db.collection("inventory");
    const query = { category: category };

    if (excludeUsername) {
        query.username = { $ne: excludeUsername };
    }

    // Only show in-stock items
    query.stock = { $gt: 0 };

    const products = await collection.find(query).limit(limit).toArray();
    return products;
});

// Get Recommendations
mcp.tool("getRecommendations", async ({ username, limit = 10 }) => {
    const inventory = db.collection("inventory");
    const purchases = db.collection("purchases");

    // 1. Get user's recent categories
    const userPurchases = await purchases
        .find({ username: username })
        .sort({ purchaseDate: -1 })
        .limit(20)
        .toArray();

    const preferredCategories = [...new Set(userPurchases.map(p => p.category))];

    let query = { stock: { $gt: 0 } };

    // Don't recommend own products
    if (username) {
        query.username = { $ne: username };
    }

    // If we have history, prioritize those categories
    if (preferredCategories.length > 0) {
        // Simple strategy: 50% from preferred, 50% random/other
        // For now, let's just fetch a mix
        query.category = { $in: preferredCategories };
    }

    let recommendations = await inventory.find(query).limit(limit).toArray();

    // If not enough recommendations, fill with random popular items
    if (recommendations.length < limit) {
        const moreQuery = {
            stock: { $gt: 0 },
            username: { $ne: username },
            _id: { $nin: recommendations.map(r => r._id) }
        };
        const more = await inventory.find(moreQuery).limit(limit - recommendations.length).toArray();
        recommendations = [...recommendations, ...more];
    }

    // Add mock recommendation scores and reasons
    return recommendations.map(rec => ({
        ...rec,
        recommendationScore: 0.8 + (Math.random() * 0.2), // 0.8 - 1.0
        reason: preferredCategories.includes(rec.category) ? "Based on your history" : "Popular item"
    }));
});

mcp.runTool = async (name, args) => {
    const tool = mcp._registeredTools[name];
    if (!tool) throw new Error(`Tool ${name} not found`);
    return await tool.callback(args);
};

console.log("MCP Server Ready");

// ----------------------------
// REST API for Streamlit
// ----------------------------

// Query
app.post("/tools/queryDocuments", async (req, res) => {
    try {
        const result = await mcp.runTool("queryDocuments", req.body);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Insert
app.post("/tools/insertDocument", async (req, res) => {
    try {
        res.json(await mcp.runTool("insertDocument", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Update
app.post("/tools/updateDocument", async (req, res) => {
    try {
        res.json(await mcp.runTool("updateDocument", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Delete
app.post("/tools/deleteDocument", async (req, res) => {
    try {
        res.json(await mcp.runTool("deleteDocument", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Inventory Management Routes

// Add Product to Inventory
app.post("/tools/addProduct", async (req, res) => {
    try {
        res.json(await mcp.runTool("addProduct", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get Inventory by Username
app.post("/tools/getInventory", async (req, res) => {
    try {
        res.json(await mcp.runTool("getInventory", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Update Product
app.post("/tools/updateProduct", async (req, res) => {
    try {
        res.json(await mcp.runTool("updateProduct", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Delete Product
app.post("/tools/deleteProduct", async (req, res) => {
    try {
        res.json(await mcp.runTool("deleteProduct", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get All Sellers
app.post("/tools/getAllSellers", async (req, res) => {
    try {
        res.json(await mcp.runTool("getAllSellers", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// ----------------------------
// New Endpoints for Recommendations
// ----------------------------

app.post("/tools/getPurchaseHistory", async (req, res) => {
    try {
        res.json(await mcp.runTool("getPurchaseHistory", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post("/tools/recordPurchase", async (req, res) => {
    try {
        res.json(await mcp.runTool("recordPurchase", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post("/tools/getProductsByCategory", async (req, res) => {
    try {
        res.json(await mcp.runTool("getProductsByCategory", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post("/tools/getRecommendations", async (req, res) => {
    try {
        res.json(await mcp.runTool("getRecommendations", req.body));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Start express
app.listen(3000, () =>
    console.log("REST API running at http://localhost:3000")
);
