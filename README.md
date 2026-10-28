# localshop
cd mongo-mcp/streamlit-ui
source .venv/bin/activate
streamlit run recomendations.py --server.port 8509
```
---
## API & MCP Tool Reference
### Backend Endpoints (`http://localhost:5000`)
- `POST /api/seller/register`: Register new seller with business category and location.
- `POST /api/seller/login`: Authenticate seller and receive JWT.
- `POST /api/consumer/register`: Register new consumer.
- `POST /api/consumer/login`: Authenticate consumer and receive JWT.
- `GET /api/flea-markets`: Query flea markets with filters (`event_type`, `event_city`, `event_location`, `stall_availability`, `page`, `limit`).
- `GET /api/influencer/:category`: Fetch influencers matched to a specific store category.
### MCP Tools (`http://localhost:3000/tools/<toolName>`)
- `addProduct`: Add a new product to a seller's catalog (`{ username, product: { productName, price, stock, category } }`).
- `getInventory`: Fetch all inventory items belonging to a seller (`{ username }`).
- `updateProduct`: Modify product fields by `productId` (`{ productId, updates }`).
- `deleteProduct`: Delete a product by `productId` (`{ productId }`).
- `recordPurchase`: Log consumer purchase and decrement inventory stock (`{ username, productId, productName, category, seller, price }`).
- `getPurchaseHistory`: Retrieve past purchases for a consumer.
- `getRecommendations`: Compute personalized product recommendations for a user.
- `queryDocuments`: Direct document query tool with custom filters.
---
## Troubleshooting
- **Microphone / Voice input does not record:**
  Ensure your terminal and browser have microphone access permissions enabled in your operating system settings. On macOS, go to **System Settings > Privacy & Security > Microphone**.
- **PyAudio installation errors:**
  Ensure PortAudio is installed first (`brew install portaudio` on macOS) before installing `pyaudio`.
- **Streamlit module not found:**
  Ensure the virtual environment is activated (`source .venv/bin/activate`) or set `PYTHON_BIN` in `run-all.sh` to your active Python executable.
- **Port already in use:**
  If a port (e.g. `5000` or `3000`) is occupied, identify and kill the process:
  ```bash
  lsof -ti:5000 | xargs kill -9
  ```
---
## License
This project is licensed under the ISC License.
