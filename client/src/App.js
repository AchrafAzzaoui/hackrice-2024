import React, { useState } from "react";
import axios from "axios";
import "./App.css"; // Make sure this import is present


function App() {
  const [isStarted, setIsStarted] = useState(false);
  // const [topics, setTopics] = useState("");
  // new code
  const [topics, setTopics] = useState([]);
  const [currentTopic, setCurrentTopic] = useState("");
    // new code
  const [file, setFile] = useState(null);

  const handleStart = () => {
    setIsStarted(true);
  };

  // new code
  const handleTopicInputChange = (e) => {
    setCurrentTopic(e.target.value);
  };

  const handleTopicKeyDown = (e) => {
    if (e.key === 'Enter' && currentTopic.trim() !== '') {
      e.preventDefault();
      setTopics([...topics, currentTopic.trim()]);
      setCurrentTopic('');
    }
  };

  const handleRemoveTopic = (indexToRemove) => {
    setTopics(topics.filter((_, index) => index !== indexToRemove));
  };
  //new code

  // const handleSubmit = async (e) => {
  //   e.preventDefault();
  //   const formData = new FormData();
  //   formData.append("topics", topics);
  //   if (file) {
  //     formData.append("pdf", file);
  //   }

  //   try {
  //     const response = await axios.post(
  //       "http://localhost:3000/start-learning",
  //       formData,
  //       {
  //         headers: { "Content-Type": "multipart/form-data" },
  //       }
  //     );
  //     console.log(response.data);
  //     alert("Learning session started!");
  //     setTopics("");
  //     setFile(null);
  //     setIsStarted(false);
  //   } catch (error) {
  //     console.error("Error starting learning session:", error);
  //     alert("Error starting learning session");
  //   }
  // };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("topics", topics.join(','));
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
      setTopics([]);
      setFile(null);
      setIsStarted(false);
    } catch (error) {
      console.error("Error starting learning session:", error);
      alert("Error starting learning session");
    }
  };



  if (!isStarted) {
  //   return (
  //     <div className="app-container">
  //       <h1 className="centered-header">Welcome to the Learning App</h1>
  //       <button className="start-button" onClick={handleStart}>Start Learning</button>
  //     </div>
  //   );
  // }
    return (
      <div className="app-container-landing">
        <div className="content">
          <h1>Elevate Your<br />Learning with AI</h1>
          <p>
            Transform your study notes into an interactive,<br />
            personalized learning experience. Upload your PDFs, set<br />
            your goals, and let our AI guide you to mastery.
          </p>
          <button className="start-button" onClick={handleStart}>
            Start Learning
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container-setup">
      <div className="split-layout">
        <div className="left-side">
          <h1>Set Up Your<br />Learning Session</h1>
        </div>
        <div className="right-side">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="topics">Topics:</label>
              <div className="topics-input-container">
                {topics.map((topic, index) => (
                  <span key={index} className="topic-tag">
                    {topic}
                    <button type="button" onClick={() => handleRemoveTopic(index)}>&times;</button>
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
              <input type="file" id="pdf" onChange={(e) => setFile(e.target.files[0])} />
            </div>
            <button type="submit" className="start-button">Start Session</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
