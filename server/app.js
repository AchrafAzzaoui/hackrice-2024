require("dotenv").config({ path: "../.env" });

const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const multer = require("multer");
const path = require("path");

const upload = multer({ dest: "uploads/" });
const app = express();

app.use(cors());
app.use(express.json());

// Serve static files from the React app build folder
app.use(express.static(path.join(__dirname, "../client/build")));

mongoose
  .connect(process.env.MONGO_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
  })
  .then(() => console.log("Connected to MongoDB"))
  .catch((err) => {
    console.error("MongoDB connection error:", err);
    process.exit(1);
  });

const LearningSession = mongoose.model(
  "LearningSession",
  new mongoose.Schema({
    topics: [String],
    pdfFilename: String,
    createdAt: { type: Date, default: Date.now },
  })
);

app.get("/", (req, res) => {
  res.send("Hello, World!");
});

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

// Catch-all handler to send React app for unrecognized routes
app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "../client/build/index.html"));
});

app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', "*");
  // res.setHeader('Access-Control-Allow-Headers', "*");
});

const PORT = process.env.PORT;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
