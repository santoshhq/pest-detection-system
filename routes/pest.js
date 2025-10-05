const express = require("express");
const router = express.Router();
const Pest = require("../models/pest");
const Recommendation = require("../models/recommendation");
const auth = require("./middleware/auth");

// Create pest
router.post("/", auth, async (req, res) => {
  try {
    const pest = new Pest({ ...req.body, owner: req.user.id });
    await pest.save();
    res.status(201).json(pest);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Get all pests
router.get("/", auth, async (req, res) => {
  try {
    const pests = await Pest.find({ owner: req.user.id }).sort({ common_name: 1 });
    res.json(pests);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get pest by id with recommendations
router.get("/:id", auth, async (req, res) => {
  try {
    const pest = await Pest.findOne({ _id: req.params.id, owner: req.user.id });
    if (!pest) return res.status(404).json({ error: "Pest not found" });

    const recommendations = await Recommendation.find({ pest_id: pest._id, owner: req.user.id });
    res.json({ pest, recommendations });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update pest
router.put("/:id", auth, async (req, res) => {
  try {
    const pest = await Pest.findOneAndUpdate({ _id: req.params.id, owner: req.user.id }, req.body, { new: true });
    res.json(pest);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Delete pest (and its recommendations)
router.delete("/:id", auth, async (req, res) => {
  try {
    await Recommendation.deleteMany({ pest_id: req.params.id, owner: req.user.id });
    await Pest.findOneAndDelete({ _id: req.params.id, owner: req.user.id });
    res.json({ message: "Deleted" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
