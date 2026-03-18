import { useState } from "react";

export default function DecoyTask({ item, onSubmit }) {
  const [assessment, setAssessment] = useState("");
  const [contradictions, setContradictions] = useState("");
  const [confidence, setConfidence] = useState(50);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      itemId: item.id,
      trialType: item.trialType,
      domain: item.domain,
      assessment,
      contradictions: contradictions.split("\n").filter(Boolean),
      confidence: confidence / 100,
      timestamp: Date.now(),
    });
    setAssessment("");
    setContradictions("");
    setConfidence(50);
  };

  return (
    <form onSubmit={handleSubmit} className="task-form">
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
        <label>Your Assessment / Recommendation:</label>
        <textarea
          value={assessment}
          onChange={(e) => setAssessment(e.target.value)}
          rows={4}
          placeholder="Write your diagnosis, recommendation, or investment assessment..."
          required
        />
      </div>

      <div className="input-group">
        <label>Contradictory Evidence Found (one per line, if any):</label>
        <textarea
          value={contradictions}
          onChange={(e) => setContradictions(e.target.value)}
          rows={3}
          placeholder="List any details that conflict with the obvious impression...&#10;(Leave blank if none found)"
        />
      </div>

      <div className="input-group">
        <label>Confidence: {confidence}%</label>
        <input
          type="range"
          min="0"
          max="100"
          value={confidence}
          onChange={(e) => setConfidence(Number(e.target.value))}
          className="slider"
        />
        <div className="slider-labels">
          <span>0% — No idea</span>
          <span>100% — Certain</span>
        </div>
      </div>

      <button type="submit" className="submit-btn">Submit Answer</button>
    </form>
  );
}
