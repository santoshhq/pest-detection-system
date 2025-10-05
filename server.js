const express = require("express");
const cors = require("cors");
const mongoose = require("mongoose");

const predictRoute = require("./routes/predict");
const pestRoute = require("./routes/pest");
const authRoute = require("./routes/auth");

const app = express();
app.use(cors());
app.use(express.json());

// Simple request logger to help debug routing issues
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} => ${req.method} ${req.originalUrl}`);
  next();
});

// Health check
app.get("/", (req, res) => res.send("OK"));

// --- MongoDB Atlas Connection ---
// Prefer loading the connection string from an environment variable for security.
// You can set MONGO_URI in a .env file or your environment. The fallback here uses the
// `darling` database so that a named DB is created instead of `admin` when running locally
// without MONGO_URI set. In production remove the fallback and use environment variables.
const MONGO_URI = process.env.MONGO_URI || "mongodb+srv://pestcontrollsystem:pestcontrollsystem@cluster0.nilkiuy.mongodb.net/darling?retryWrites=true&w=majority";

// The MongoDB Node driver v4+ ignores useNewUrlParser/useUnifiedTopology; passing them
// causes deprecation warnings. Call mongoose.connect with the URI only and handle errors.
mongoose.connect(MONGO_URI)
  .then(async () => {
    console.log("MongoDB Atlas connected successfully");

    // Require models so Mongoose registers them and we can access collection names
    const Pest = require("./models/pest");
    const Recommendation = require("./models/recommendation");

    // Ensure collections exist on startup. Atlas/MongoDB will not create the database or
    // collections until data is written or createCollection is called. This routine tries
    // to create the collections if they're missing, and falls back to inserting a dummy
    // document if createCollection is not permitted.
    async function ensureCollections() {
      const db = mongoose.connection.db;
      try {
        const existing = await db.listCollections().toArray();
        const names = existing.map(c => c.name);

        async function createIfMissing(colName) {
          if (!names.includes(colName)) {
            try {
              await db.createCollection(colName);
              console.log(`Created collection: ${colName}`);
            } catch (err) {
              console.warn(`createCollection failed for ${colName}:`, err.message);
              // fallback: insert a single doc to force collection creation then remove it
              try {
                await db.collection(colName).insertOne({ _createdAt: new Date(), _seed: true });
                await db.collection(colName).deleteMany({ _seed: true });
                console.log(`Created collection by inserting seed doc: ${colName}`);
              } catch (err2) {
                console.error(`Failed to create collection ${colName} by fallback insert:`, err2.message);
              }
            }
          }
        }

        await createIfMissing(Pest.collection.name);
        await createIfMissing(Recommendation.collection.name);

        // Ensure any schema-defined indexes are created
        try {
          await Pest.init();
          await Recommendation.init();
        } catch (idxErr) {
          console.warn('Index initialization warning:', idxErr && idxErr.message ? idxErr.message : idxErr);
        }
      } catch (outerErr) {
        console.error('Error while ensuring collections:', outerErr && outerErr.message ? outerErr.message : outerErr);
      }
    }

    await ensureCollections();
  })
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
app.use("/auth", authRoute);

// On startup, print available routes (helps confirm predict route is mounted)
function listRoutes() {
  const routes = [];
  app._router.stack.forEach(mw => {
    if (mw.route) {
      // routes registered directly on the app
      const methods = Object.keys(mw.route.methods).join(',').toUpperCase();
      routes.push(`${methods} ${mw.route.path}`);
    } else if (mw.name === 'router' && mw.handle && mw.handle.stack) {
      // router middleware
      mw.handle.stack.forEach(r => {
        if (r.route && r.route.path) {
          const methods = Object.keys(r.route.methods).join(',').toUpperCase();
          // prepend the mount path if available
          const mountPath = mw.regexp && mw.regexp.source ? (mw.regexp.source.replace('^\\/','/').replace('\\/?(?=\\/|$)','')) : '';
          routes.push(`${methods} ${mountPath}${r.route.path}`);
        }
      });
    }
  });
  console.log('Mounted routes:\n' + routes.join('\n'));
}

app.listen(5000, () => console.log("🚀 Server running on port 5000"));
