const mongoose = require('mongoose');

const PredictionSchema = new mongoose.Schema({
  owner: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  imageUrl: { type: String },
  class_name: { type: String },
  confidence: { type: Number },
  raw: { type: Object },
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Prediction', PredictionSchema);
