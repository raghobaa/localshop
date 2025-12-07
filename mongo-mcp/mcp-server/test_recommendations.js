const BASE_URL = 'http://localhost:3000/tools';
const TEST_USER = 'TestUser_Recs';

async function post(url, body) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
    }
    return res.json();
}

async function test() {
    try {
        console.log("1. Testing recordPurchase...");
        const purchaseRes = await post(`${BASE_URL}/recordPurchase`, {
            username: TEST_USER,
            productName: "Test Product",
            category: "Electronics",
            price: 999,
            seller: "TestSeller"
        });
        console.log("Record Purchase Result:", purchaseRes);

        console.log("\n2. Testing getPurchaseHistory...");
        const historyRes = await post(`${BASE_URL}/getPurchaseHistory`, {
            username: TEST_USER
        });
        console.log("Purchase History (should have at least 1):", historyRes.length);
        if (historyRes.length === 0) throw new Error("History empty!");

        console.log("\n3. Testing getProductsByCategory...");
        // First ensure we have some products
        await post(`${BASE_URL}/addProduct`, {
            username: "Seller1",
            product: {
                productName: "Laptop",
                category: "Electronics",
                price: 50000,
                stock: 10,
                description: "Good laptop"
            }
        });

        const catRes = await post(`${BASE_URL}/getProductsByCategory`, {
            category: "Electronics",
            excludeUsername: TEST_USER
        });
        console.log("Products in Electronics:", catRes.length);

        console.log("\n4. Testing getRecommendations...");
        const recRes = await post(`${BASE_URL}/getRecommendations`, {
            username: TEST_USER
        });
        console.log("Recommendations count:", recRes.length);
        if (recRes.length > 0) {
            console.log("First recommendation:", recRes[0].productName);
        }

        console.log("\n✅ All tests passed!");

    } catch (error) {
        console.error("❌ Test failed:", error.message);
    }
}

test();
