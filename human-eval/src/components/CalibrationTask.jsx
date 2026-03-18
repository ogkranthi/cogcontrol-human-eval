import { useState } from "react";

const SEVERITY_OPTIONS = ["none", "minor", "moderate", "major", "contraindicated"];
const MATERIALITY_OPTIONS = ["materialized", "did_not_materialize"];

export default function CalibrationTask({ item, onSubmit }) {
  const [answer, setAnswer] = useState("");
  const [confidence, setConfidence] = useState(50);
  const [wager, setWager] = useState(50);

  const options = item.subtype === "Drug Interaction" ? SEVERITY_OPTIONS : MATERIALITY_OPTIONS;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      itemId: item.id,
      domain: item.domain,
      difficulty: item.difficulty,
      answer,
      confidence: confidence / 100,
      wager,
      timestamp: Date.now(),
    });
    setAnswer("");
    setConfidence(50);
    setWager(50);
  };

  return (
    <form onSubmit={handleSubmit} className="task-form">
      <div className="case-box">
        <div className="case-meta">
          <span className={`domain-tag ${item.domain}`}>{item.domain}</span>
          <span className="diff-tag">Difficulty: {"*".repeat(item.difficulty)}</span>
          <span className="subtype-tag">{item.subtype}</span>
        </div>
        <pre className="case-text">{item.prompt}</pre>
      </div>

      <div className="question-box">
        <strong>Question:</strong> {item.question}
      </div>

      <div className="input-group">
        <label>Your Answer:</label>
        <div className="option-grid">
          {options.map((opt) => (
            <button
              key={opt}
              type="button"
              className={`option-btn ${answer === opt ? "selected" : ""}`}
              onClick={() => setAnswer(opt)}
            >
              {opt.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      <div className="input-group">
        <label>Confidence: {confidence}%</label>
        <input
          type="range" min="0" max="100"
          value={confidence}
          onChange={(e) => setConfidence(Number(e.target.value))}
          className="slider"
        />
        <div className="slider-labels">
          <span>0% — Guessing</span>
          <span>100% — Certain</span>
        </div>
      </div>

      <div className="input-group">
        <label>
          Wager: {wager} points
          <span className="wager-info">
            {" "}(Correct: +{wager} | Wrong: -{wager * 2})
          </span>
        </label>
        <input
          type="range" min="0" max="100"
          value={wager}
          onChange={(e) => setWager(Number(e.target.value))}
          className="slider wager-slider"
        />
        <div className="slider-labels">
          <span>0 — Not betting</span>
          <span>100 — All in</span>
        </div>
      </div>

      <button type="submit" className="submit-btn" disabled={!answer}>
        Submit Answer
      </button>
    </form>
  );
}
