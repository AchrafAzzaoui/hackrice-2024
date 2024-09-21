require("dotenv").config();
const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const multer = require("multer");
const upload = multer({ dest: "uploads/" });

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Connect to MongoDB
mongoose
  .connect(process.env.MONGO_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
  })
  .then(() => console.log("Connected to MongoDB"))
  .catch((err) => console.error("MongoDB connection error:", err));

// Learning Session model
const LearningSession = mongoose.model(
  "LearningSession",
  new mongoose.Schema({
    topics: [String],
    pdfFilename: String,
    createdAt: { type: Date, default: Date.now },
  })
);

// Routes

// Original route
app.get("/", (req, res) => {
  res.send("Hello, World!");
});

// Start learning session route
app.post("/start-learning", upload.single("pdf"), async (req, res) => {
  try {
    const { topics } = req.body;
    const pdfFilename = req.file ? req.file.filename : null;

    const session = new LearningSession({
      topics: topics.split(",").map((topic) => topic.trim()),
      pdfFilename,
    });

    await session.save();
    res.json({ message: "Learning session started", sessionId: session._id });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Server start
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
