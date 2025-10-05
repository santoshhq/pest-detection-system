const express = require("express");
const cors = require("cors");
const mongoose = require("mongoose");

const predictRoute = require("./routes/predict");
const pestRoute = require("./routes/pest");

const app = express();
app.use(cors());
app.use(express.json());

// --- MongoDB Atlas Connection ---
// Prefer loading the connection string from an environment variable for security.
// You can set MONGO_URI in a .env file or your environment. A hard-coded fallback is kept
// to avoid breaking existing runs, but it's recommended to remove the fallback in production.
const MONGO_URI = process.env.MONGO_URI || "mongodb+srv://pestcontrollsystem:OGsl4D8ugkou2tFY@cluster0.nilkiuy.mongodb.net/admin?retryWrites=true&w=majority";

// The MongoDB Node driver v4+ ignores useNewUrlParser/useUnifiedTopology; passing them
// causes deprecation warnings. Call mongoose.connect with the URI only and handle errors.
mongoose.connect(MONGO_URI)
  .then(() => console.log("MongoDB Atlas connected successfully"))
  .catch(err => {
    console.error("❌ MongoDB connection error:", err);
    // If auth failed, provide a helpful hint.
    if (err && err.errorResponse && err.errorResponse.errmsg && err.errorResponse.errmsg.includes('Authentication failed')) {
      console.error("Hint: Authentication failed — check your username/password, the database user privileges, and that your IP is allowed in Atlas Network Access (e.g. 122.171.64.161/32). Also consider storing credentials in environment variables instead of in source code.");
    }
  });

// --- Routes ---
app.use("/predict", predictRoute);
app.use("/pest", pestRoute);

app.listen(5000, () => console.log("🚀 Server running on port 5000"));
