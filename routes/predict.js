// routes/predict.js
const express = require("express");
const router = express.Router();
const { spawn } = require("child_process");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const auth = require("./middleware/auth");
const Prediction = require("../models/prediction");

// Temp storage for uploaded images
const upload = multer({ dest: "uploads/" });

router.post("/", auth, upload.single("image"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No image uploaded" });
  const imagePath = req.file.path;
  // Resolve the Python script path relative to this file so it works regardless of CWD
  const scriptPath = path.resolve(__dirname, "..", "models", "utils", "call_model.py");
  console.log(`Spawning Python: python ${scriptPath} ${imagePath}`);
  const py = spawn("python", [scriptPath, imagePath]);

  let data = "";
  let error = "";

  py.stdout.on("data", chunk => (data += chunk.toString()));
  py.stderr.on("data", chunk => {
    const txt = chunk.toString();
    error += txt;
    // print stderr chunks as they arrive for immediate debugging
    console.error("Python stderr:", txt);
  });

  py.on('error', (err) => {
    // spawn-level errors (e.g., executable not found)
    console.error('Failed to start Python process:', err.message || err);
  });

  py.on("close", async () => {
    console.log('Python process closed with exit code (unknown here)');
    fs.unlinkSync(imagePath); // delete temp file
    if (error) {
      console.error("Python Error:", error);
      return res.status(500).json({ error: "Prediction failed" });
    }
    try {
      const result = JSON.parse(data);
      // Save top1 prediction (result could be array or single obj)
      const top = Array.isArray(result) ? result[0] : result;
      const predDoc = new Prediction({
        owner: req.user.id,
        imageUrl: imagePath,
        class_name: top.class_name,
        confidence: top.confidence,
        raw: result
      });
      await predDoc.save();
      res.json(predDoc);
    } catch (err) {
      res.status(500).json({ error: "Invalid JSON from model" });
    }
  });
});

module.exports = router;
