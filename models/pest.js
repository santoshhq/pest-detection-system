const mongoose = require("mongoose");

const PestSchema = new mongoose.Schema({
  common_name: { type: String, required: true, index: true }, // e.g. "aphids"
  scientific_name: { type: String },
  description: { type: String },
  image_url: { type: String },
  owner: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model("Pest", PestSchema);
