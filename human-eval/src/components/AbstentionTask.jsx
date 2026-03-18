import { useState } from "react";

export default function AbstentionTask({ item, onSubmit }) {
  const [decision, setDecision] = useState("");
  const [answer, setAnswer] = useState("");
  const [confidence, setConfidence] = useState(50);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      itemId: item.id,
      domain: item.domain,
      answerability: item.answerability,
      difficulty: item.difficulty,
      decision,
      answer: decision === "answer" ? answer : null,
      confidence: confidence / 100,
      timestamp: Date.now(),
    });
    setDecision("");
    setAnswer("");
    setConfidence(50);
  };

  return (
    <form onSubmit={handleSubmit} className="task-form">
      <div className="payoff-banner">
        Correct: <span className="gain">+10</span> | Wrong: <span className="loss">-50</span> | Abstain: <span className="neutral">-2</span>
      </div>

      <div className="case-box">
        <div className="case-meta">
          <span className={`domain-tag ${item.domain}`}>{item.domain}</span>
          <span className="diff-tag">Difficulty: {"*".repeat(item.difficulty)}</span>
        </div>
        <pre className="case-text">{item.case}</pre>
      </div>

      <div className="question-box">
        <strong>Question:</strong> {item.question}
      </div>

      <div className="input-group">
        <label>Your Decision:</label>
        <div className="decision-grid">
          <button
            type="button"
            className={`decision-btn answer-btn ${decision === "answer" ? "selected" : ""}`}
            onClick={() => setDecision("answer")}
          >
            ANSWER
            <small>Risk it (+10 / -50)</small>
          </button>
          <button
            type="button"
            className={`decision-btn abstain-btn ${decision === "abstain" ? "selected" : ""}`}
            onClick={() => setDecision("abstain")}
          >
            ABSTAIN
            <small>Defer to specialist (-2)</small>
          </button>
        </div>
      </div>

      {decision === "answer" && (
        <div className="input-group">
          <label>Your Answer:</label>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={3}
            placeholder="Write your answer..."
            required
          />
        </div>
      )}

      {decision && (
        <div className="input-group">
          <label>Confidence: {confidence}%</label>
          <input
            type="range" min="0" max="100"
            value={confidence}
            onChange={(e) => setConfidence(Number(e.target.value))}
            className="slider"
          />
        </div>
      )}

      <button type="submit" className="submit-btn" disabled={!decision || (decision === "answer" && !answer)}>
        Submit Decision
      </button>
    </form>
  );
}
