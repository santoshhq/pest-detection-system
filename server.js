const express = require("express");
const cors = require("cors");
const mongoose = require("mongoose");
const authRoute = require("./routes/auth");
const predictRoute = require("./routes/predict");
const pestRoute = require("./routes/pest");

const app = express();
app.use(cors());
app.use(express.json());

// --- MongoDB Atlas Connection ---
// Prefer loading the connection string from an environment variable for security.
// You can set MONGO_URI in a .env file or your environment. A hard-coded fallback is kept
// to avoid breaking existing runs, but it's recommended to remove the fallback in production.
// NOTE: Using the 'admin' database in the connection string can cause "not authorized on admin"
// errors if the Atlas user doesn't have admin DB privileges. Use a dedicated application DB
// (for example: 'pestdb') or set a proper MONGO_URI via environment variables.
const MONGO_URI = process.env.MONGO_URI || "mongodb+srv://pestcontrollsystem:pestcontrollsystem@cluster0.nilkiuy.mongodb.net/pestdb?retryWrites=true&w=majority";

// The MongoDB Node driver v4+ ignores useNewUrlParser/useUnifiedTopology; passing them
// causes deprecation warnings. Call mongoose.connect with the URI only and handle errors.
mongoose.connect(MONGO_URI)
  .then(() => console.log("MongoDB Atlas connected successfully"))
  .catch(err => {
    console.error("❌ MongoDB connection error:", err);
    // Helpful hints for common Atlas connection problems
    const msg = err && err.errorResponse && err.errorResponse.errmsg ? err.errorResponse.errmsg : (err && err.message) || '';
    if (msg.includes('Authentication failed')) {
      console.error("Hint: Authentication failed — check your username/password, and that your Atlas DB user has correct privileges and the target database matches the connection string. Also ensure your IP is allowed in Atlas Network Access.");
    } else if (msg.includes('not authorized on admin')) {
      console.error("Hint: The connection is attempting to use the 'admin' database. Change the MONGO_URI to use a non-admin application database (for example add '/pestdb' at the end of the URI) or grant the user appropriate privileges in Atlas. Prefer setting MONGO_URI as an environment variable on Render rather than hard-coding credentials.");
    }
  });

// --- Routes ---
app.use("/predict", predictRoute);
app.use("/pest", pestRoute);
app.use("/auth", authRoute);
app.listen(5000, () => console.log("🚀 Server running on port 5000"));
