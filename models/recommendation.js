const mongoose = require("mongoose");

const RecommendationSchema = new mongoose.Schema({
  pest_id: { type: mongoose.Schema.Types.ObjectId, ref: "Pest", required: true },
  type: { type: String, enum: ["IPM", "Chemical", "Prevention"], required: true },
  details: { type: String, required: true },
  owner: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model("Recommendation", RecommendationSchema);
