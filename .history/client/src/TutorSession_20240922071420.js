import React, { useState, useEffect } from "react";
import axios from "axios";

const TutorSession = ({ topics, onSessionComplete }) => {
  const [currentTopicIndex, setCurrentTopicIndex] = useState(0);
  const [userExplanation, setUserExplanation] = useState("");
  const [tutorFeedback, setTutorFeedback] = useState("");
  const [isExplanationPhase, setIsExplanationPhase] = useState(true);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [userAnswer, setUserAnswer] = useState("");

  useEffect(() => {
    if (currentTopicIndex >= topics.length) {
      onSessionComplete();
    }
  }, [currentTopicIndex, topics, onSessionComplete]);

  const handleSubmitExplanation = async () => {
    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/submit-explanation",
        {
          topic: topics[currentTopicIndex],
          explanation: userExplanation,
        },
        {
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          },
        }
      );
      setTutorFeedback(response.data.feedback);
      setIsExplanationPhase(false);
      setCurrentQuestion(response.data.question);
    } catch (error) {
      console.error("Error submitting explanation:", error);
    }
  };

  const handleSubmitAnswer = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:5000/submit-answer", {
        topic: topics[currentTopicIndex],
        question: currentQuestion,
        answer: userAnswer,
      });
      setTutorFeedback(response.data.feedback);
      if (response.data.nextQuestion) {
        setCurrentQuestion(response.data.nextQuestion);
        setUserAnswer("");
      } else {
        setCurrentTopicIndex((prevIndex) => prevIndex + 1);
        setIsExplanationPhase(true);
        setUserExplanation("");
        setTutorFeedback("");
      }
    } catch (error) {
      console.error("Error submitting answer:", error);
    }
  };

  if (currentTopicIndex >= topics.length) {
    return <div>Tutorial session complete!</div>;
  }

  return (
    <div className="tutor-session">
      {isExplanationPhase ? (
        <>
          <h2>Explain {topics[currentTopicIndex]} to me.</h2>
          <textarea
            value={userExplanation}
            onChange={(e) => setUserExplanation(e.target.value)}
            placeholder="Type your explanation here..."
          />
          <button onClick={handleSubmitExplanation}>Submit Explanation</button>
        </>
      ) : (
        <>
          <h2>{currentQuestion}</h2>
          <textarea
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value)}
            placeholder="Type your answer here..."
          />
          <button onClick={handleSubmitAnswer}>Submit Answer</button>
        </>
      )}
      {tutorFeedback && (
        <div className="tutor-feedback">
          <h3>Tutor Feedback:</h3>
          <p>{tutorFeedback}</p>
        </div>
      )}
    </div>
  );
};

export default TutorSession;
