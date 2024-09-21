import React, { useState } from "react";
import axios from "axios";

function App() {
  const [isStarted, setIsStarted] = useState(false);
  const [topics, setTopics] = useState("");
  const [file, setFile] = useState(null);

  const handleStart = () => {
    setIsStarted(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("topics", topics);
    if (file) {
      formData.append("pdf", file);
    }

    try {
      const response = await axios.post(
        "http://localhost:3000/start-learning",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      console.log(response.data);
      alert("Learning session started!");
      setTopics("");
      setFile(null);
      setIsStarted(false);
    } catch (error) {
      console.error("Error starting learning session:", error);
      alert("Error starting learning session");
    }
  };

  if (!isStarted) {
    return (
      <div>
        <h1>Welcome to the Learning App</h1>
        <button onClick={handleStart}>Start Learning</button>
      </div>
    );
  }

  return (
    <div>
      <h1>Set Up Your Learning Session</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="topics">Topics (comma-separated):</label>
          <input
            type="text"
            id="topics"
            value={topics}
            onChange={(e) => setTopics(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="pdf">Upload PDF (optional):</label>
          <input
            type="file"
            id="pdf"
            onChange={(e) => setFile(e.target.files[0])}
          />
        </div>
        <button type="submit">Start Session</button>
      </form>
    </div>
  );
}

export default App;
