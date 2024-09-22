import React, { useState, useEffect } from "react";
import axios from "axios";
import io from "socket.io-client";
import "./App.css";

function App() {
  const [isStarted, setIsStarted] = useState(false);
  const [topics, setTopics] = useState([]);
  const [currentTopic, setCurrentTopic] = useState("");
  const [file, setFile] = useState(null);
  const [socket, setSocket] = useState(null);
  const [question, setQuestion] = useState("");
  const [userInput, setUserInput] = useState("");
  const [feedback, setFeedback] = useState("");
  const [isChoiceRequired, setIsChoiceRequired] = useState(false);
  const [hint, setHint] = useState("");
  const [correctAnswer, setCorrectAnswer] = useState("");

  useEffect(() => {
    const newSocket = io("http://localhost:5000");
    setSocket(newSocket);

    newSocket.on("question", (data) => {
      setQuestion(data);
      setFeedback("");
      setHint("");
      setCorrectAnswer("");
      setIsChoiceRequired(false);
    });

    // Handle successful connection
    newSocket.on("connect", () => {
      console.log("Connected to server with Socket ID:", newSocket.id);
    });

    // Handle disconnection
    newSocket.on("disconnect", () => {
      console.log("Disconnected from server");
    });

    newSocket.on("feedback", (data) => {
      setFeedback(data);
    });

    newSocket.on("choice", (data) => {
      setIsChoiceRequired(true);
    });

    newSocket.on("hint", (data) => {
      setHint(data);
    });

    newSocket.on("correct_answer", (data) => {
      setCorrectAnswer(data);
    });

    newSocket.on("topic_finished", (data) => {
      console.log(data);
      // You can add some UI feedback here when a topic is finished
    });

    return () => newSocket.disconnect();
  }, []);

  const handleStart = () => {
    setIsStarted(true);
  };

  const handleTopicInputChange = (e) => {
    setCurrentTopic(e.target.value);
  };

  const handleTopicKeyDown = (e) => {
    if (e.key === "Enter" && currentTopic.trim() !== "") {
      e.preventDefault();
      setTopics([...topics, currentTopic.trim()]);
      setCurrentTopic("");
    }
  };

  const handleRemoveTopic = (indexToRemove) => {
    setTopics(topics.filter((_, index) => index !== indexToRemove));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("topics", topics.join(","));
    if (file) {
      formData.append("pdf", file);
    }
    try {
      await axios.post(
        "http://localhost:5000/submitPDF",
        { filename: file ? file.name : null, topics: topics.join(",") },
        { headers: { "Content-Type": "application/json" } }
      );
      alert("Learning session started!");
    } catch (error) {
      console.error("Error starting learning session:", error);
      alert("Error starting learning session");
    }
  };

  const handleUserInput = (e) => {
    e.preventDefault();
    socket.emit("user_input", userInput, (response) => {
      console.log("Server acknowledged:", response);
    });
    setUserInput("");
  };

  if (!isStarted) {
    return (
      <div className="app-container-landing">
        <div className="content">
          <h1>
            Elevate Your
            <br />
            Learning with AI
          </h1>
          <p>
            Transform your study notes into an interactive,
            <br />
            personalized learning experience. Upload your PDFs, set
            <br />
            your goals, and let our AI guide you to mastery.
          </p>
          <button className="start-button" onClick={handleStart}>
            Start Learning
          </button>
        </div>
      </div>
    );
  }

  if (question) {
    return (
      <div className="app-container-learning">
        <h2>{question}</h2>
        {feedback && <p className="feedback">{feedback}</p>}
        {hint && <p className="hint">Hint: {hint}</p>}
        {correctAnswer && (
          <p className="correct-answer">Correct answer: {correctAnswer}</p>
        )}
        <form onSubmit={handleUserInput}>
          <input
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Your answer"
          />
          <button type="submit">Submit</button>
        </form>
        {isChoiceRequired && (
          <div>
            <button
              onClick={() =>
                socket.emit("user_input", "1", (response) => {
                  console.log("Server acknowledged:", response);
                })
              }
            >
              Re-answer with hint
            </button>
            <button
              onClick={() =>
                socket.emit("user_input", "2", (response) => {
                  console.log("Server acknowledged:", response);
                })
              }
            >
              See the correct answer
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="app-container-setup">
      <div className="split-layout">
        <div className="left-side">
          <h1>
            Set Up Your
            <br />
            Learning Session
          </h1>
        </div>
        <div className="right-side">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="topics">Topics:</label>
              <div className="topics-input-container">
                {topics.map((topic, index) => (
                  <span key={index} className="topic-tag">
                    {topic}
                    <button
                      type="button"
                      onClick={() => handleRemoveTopic(index)}
                    >
                      &times;
                    </button>
                  </span>
                ))}
                <input
                  type="text"
                  id="topics"
                  value={currentTopic}
                  onChange={handleTopicInputChange}
                  onKeyDown={handleTopicKeyDown}
                  placeholder="Type a topic and press Enter"
                />
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="pdf">Upload PDF (optional):</label>
              <input
                type="file"
                id="pdf"
                onChange={(e) => setFile(e.target.files[0])}
              />
            </div>
            <button className="start-button" type="submit">
              Start Session
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
