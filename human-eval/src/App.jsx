import { useState, useEffect } from "react";
import { TASKS, TASK_ORDER } from "./data/tasks";
import DecoyTask from "./components/DecoyTask";
import CalibrationTask from "./components/CalibrationTask";
import AbstentionTask from "./components/AbstentionTask";
import Results from "./components/Results";
import "./App.css";

const STORAGE_KEY = "cogcontrol_human_eval";

function App() {
  const [phase, setPhase] = useState("intro"); // intro | task | results
  const [currentTaskIdx, setCurrentTaskIdx] = useState(0);
  const [currentItemIdx, setCurrentItemIdx] = useState(0);
  const [allResults, setAllResults] = useState({ ef1: [], mc1: [], mc2: [] });
  const [startTime, setStartTime] = useState(null);

  // Load saved progress
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const data = JSON.parse(saved);
        setAllResults(data.results || { ef1: [], mc1: [], mc2: [] });
        setCurrentTaskIdx(data.taskIdx || 0);
        setCurrentItemIdx(data.itemIdx || 0);
        if (data.phase === "results") setPhase("results");
      } catch {
        // ignore corrupt data
      }
    }
  }, []);

  // Save progress
  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ results: allResults, taskIdx: currentTaskIdx, itemIdx: currentItemIdx, phase })
    );
  }, [allResults, currentTaskIdx, currentItemIdx, phase]);

  const currentTaskKey = TASK_ORDER[currentTaskIdx];
  const currentTask = TASKS[currentTaskKey];
  const currentItem = currentTask?.items[currentItemIdx];
  const totalItems = TASK_ORDER.reduce((sum, k) => sum + TASKS[k].items.length, 0);
  const completedItems = Object.values(allResults).reduce((sum, arr) => sum + arr.length, 0);

  const handleStart = () => {
    setPhase("task");
    setStartTime(Date.now());
  };

  const handleReset = () => {
    if (window.confirm("Reset all progress? This cannot be undone.")) {
      setAllResults({ ef1: [], mc1: [], mc2: [] });
      setCurrentTaskIdx(0);
      setCurrentItemIdx(0);
      setPhase("intro");
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const handleSubmit = (response) => {
    const taskKey = TASK_ORDER[currentTaskIdx];
    setAllResults((prev) => ({
      ...prev,
      [taskKey]: [...prev[taskKey], response],
    }));

    // Advance to next item or next task
    const task = TASKS[taskKey];
    if (currentItemIdx + 1 < task.items.length) {
      setCurrentItemIdx(currentItemIdx + 1);
    } else if (currentTaskIdx + 1 < TASK_ORDER.length) {
      setCurrentTaskIdx(currentTaskIdx + 1);
      setCurrentItemIdx(0);
    } else {
      setPhase("results");
    }
  };

  // INTRO
  if (phase === "intro") {
    return (
      <div className="app">
        <header className="app-header">
          <h1>CogControl-Stakes</h1>
          <p className="subtitle">Human Baseline Evaluation</p>
        </header>
        <div className="intro-content">
          <p>
            This evaluation collects human baseline data for the{" "}
            <strong>CogControl-Stakes</strong> benchmark — measuring cognitive
            control (executive functions + metacognition) in AI systems.
          </p>

          <div className="task-overview">
            {TASK_ORDER.map((key) => (
              <div key={key} className="task-card">
                <h3>{TASKS[key].name}</h3>
                <p className="paradigm">{TASKS[key].paradigm}</p>
                <p>{TASKS[key].description}</p>
                <span className="item-count">{TASKS[key].items.length} items</span>
              </div>
            ))}
          </div>

          <div className="intro-stats">
            <span>{totalItems} total items</span>
            <span>~2-3 hours</span>
            <span>Progress auto-saved</span>
          </div>

          <button onClick={handleStart} className="start-btn">
            {completedItems > 0 ? `Resume (${completedItems}/${totalItems} done)` : "Begin Evaluation"}
          </button>

          {completedItems > 0 && (
            <button onClick={handleReset} className="reset-btn">
              Reset Progress
            </button>
          )}
        </div>
      </div>
    );
  }

  // RESULTS
  if (phase === "results") {
    return (
      <div className="app">
        <header className="app-header">
          <h1>CogControl-Stakes</h1>
          <p className="subtitle">Human Baseline Results</p>
        </header>
        <Results allResults={allResults} />
        <button onClick={handleReset} className="reset-btn" style={{ marginTop: "2rem" }}>
          Start Over
        </button>
      </div>
    );
  }

  // TASK
  return (
    <div className="app">
      <header className="app-header compact">
        <h1>CogControl-Stakes</h1>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${(completedItems / totalItems) * 100}%` }}
          />
        </div>
        <div className="progress-text">
          {completedItems}/{totalItems} items | {currentTask.name} — Item{" "}
          {currentItemIdx + 1}/{currentTask.items.length}
        </div>
      </header>

      <div className="task-content">
        <div className="task-header">
          <h2>{currentTask.name}</h2>
          <p className="task-desc">{currentTask.description}</p>
        </div>

        {currentTaskKey === "ef1" && (
          <DecoyTask key={currentItem.id} item={currentItem} onSubmit={handleSubmit} />
        )}
        {currentTaskKey === "mc1" && (
          <CalibrationTask key={currentItem.id} item={currentItem} onSubmit={handleSubmit} />
        )}
        {currentTaskKey === "mc2" && (
          <AbstentionTask key={currentItem.id} item={currentItem} onSubmit={handleSubmit} />
        )}
      </div>
    </div>
  );
}

export default App;
