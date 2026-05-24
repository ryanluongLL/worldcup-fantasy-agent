"use client";

import { useState } from "react";
import { Trophy, TrendingUp, Users, Zap, Star } from "lucide-react";

const DEMO_LINEUP = {
  GK: [{ name: "Gonda", nationality: "JPN", points: 8 }],
  DEF: [
    { name: "Sabaly", nationality: "SEN", points: 8 },
    { name: "Pedro Miguel", nationality: "QAT", points: 6 },
    { name: "Khoukhi", nationality: "QAT", points: 6 },
    { name: "Vitória", nationality: "CAN", points: 5 },
  ],
  MID: [
    { name: "Amallah", nationality: "MAR", points: 10 },
    { name: "Cheshmi", nationality: "IRN", points: 7 },
    { name: "Mohammed", nationality: "QAT", points: 6 },
  ],
  FWD: [
    { name: "Goodwin", nationality: "AUS", points: 10 },
    { name: "Muntari", nationality: "QAT", points: 7 },
    { name: "Estrada", nationality: "ECU", points: 6 },
  ],
};

const TOP_PERFORMERS = [
  { name: "Kylian Mbappé", team: "France", points: 59, goals: 8, assists: 2 },
  { name: "Lionel Messi", team: "Argentina", points: 57, goals: 7, assists: 3 },
  { name: "Julián Álvarez", team: "Argentina", points: 32, goals: 4, assists: 0 },
  { name: "Olivier Giroud", team: "France", points: 30, goals: 4, assists: 0 },
  { name: "Harry Kane", team: "England", points: 28, goals: 2, assists: 3 },
];

const positionColors: Record<string, string> = {
  GK: "#C9963A",
  DEF: "#1A6B3C",
  MID: "#2D8A52",
  FWD: "#C8402A",
};

function PlayerCard({ player, position }: { player: { name: string; nationality: string; points: number }; position: string }) {
  return (
    <div className="player-card">
      <div
        className="card-inner"
        style={{ borderColor: positionColors[position] }}
      >
        <div className="card-top" style={{ backgroundColor: positionColors[position] }} />
        <span className="card-position" style={{ color: positionColors[position] }}>
          {position}
        </span>
        <div className="card-avatar" style={{ backgroundColor: positionColors[position] }}>
          {player.nationality}
        </div>
        <span className="card-name">{player.name.split(" ").pop()}</span>
        <span className="card-pts">{player.points} pts</span>
      </div>
    </div>
  );
}

function PitchView() {
  return (
    <div className="pitch">
      <div className="pitch-markings">
        <div className="pitch-line center-line" />
        <div className="pitch-circle" />
        <div className="pitch-box top-box" />
        <div className="pitch-box bottom-box" />
      </div>
      <div className="pitch-row">
        {DEMO_LINEUP.FWD.map((p, i) => (
          <PlayerCard key={i} player={p} position="FWD" />
        ))}
      </div>
      <div className="pitch-row">
        {DEMO_LINEUP.MID.map((p, i) => (
          <PlayerCard key={i} player={p} position="MID" />
        ))}
      </div>
      <div className="pitch-row">
        {DEMO_LINEUP.DEF.map((p, i) => (
          <PlayerCard key={i} player={p} position="DEF" />
        ))}
      </div>
      <div className="pitch-row">
        {DEMO_LINEUP.GK.map((p, i) => (
          <PlayerCard key={i} player={p} position="GK" />
        ))}
      </div>
      <div className="formation-badge">4-3-3</div>
    </div>
  );
}

function AgentChat() {
  const [messages, setMessages] = useState([
    { role: "agent", text: "Welcome to Pitchside. I'm your AI football coach. Ask me to recommend a lineup, suggest transfers, compare players, or predict match outcomes." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);
    setTimeout(() => {
      setMessages((prev) => [...prev, {
        role: "agent",
        text: "Analyzing your request using 2022 World Cup data. Backend integration coming soon.",
      }]);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="online-dot" />
        <span className="chat-title">COACH AI</span>
      </div>
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="bubble">{msg.text}</div>
          </div>
        ))}
        {loading && (
          <div className="message agent">
            <div className="bubble muted">Analyzing...</div>
          </div>
        )}
      </div>
      <div className="chat-input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask your coach..."
          className="chat-input"
        />
        <button onClick={sendMessage} className="send-btn">SEND</button>
      </div>
    </div>
  );
}

export default function Home() {
  const [activeTab, setActiveTab] = useState("team");

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-icon">P</div>
          <span className="logo-text">PITCHSIDE</span>
        </div>
        <nav className="nav">
          {[
            { id: "team", label: "My Team", icon: Users },
            { id: "intel", label: "Intelligence", icon: TrendingUp },
            { id: "standings", label: "Standings", icon: Trophy },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`nav-btn ${activeTab === id ? "active" : ""}`}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </nav>
        <div className="badge">WORLD CUP 2026</div>
      </header>

      <div className="hero">
        <div className="hero-content">
          <div className="hero-title">
            <span className="hero-white">YOUR AI</span>
            <span className="hero-gold">COACH</span>
          </div>
          <p className="hero-sub">
            Powered by Gemini AI and real 2022 World Cup data. Get lineup recommendations, transfer suggestions, match predictions, and live 2026 standings.
          </p>
          <div className="hero-stats">
            {[
              { label: "60 Players", icon: Users },
              { label: "3,230 Stats", icon: Zap },
              { label: "15 AI Tools", icon: Star },
            ].map(({ label, icon: Icon }) => (
              <div key={label} className="hero-stat">
                <Icon size={14} color="#C9963A" />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="hero-circle-1" />
        <div className="hero-circle-2" />
      </div>

      <main className="main">
        {activeTab === "team" && (
          <div className="team-grid">
            <div className="pitch-section">
              <div className="section-header">
                <h2 className="section-title">MY SQUAD</h2>
                <span className="section-sub">Matchday 1 · 4-3-3</span>
              </div>
              <PitchView />
            </div>
            <div className="chat-section">
              <h2 className="section-title" style={{ marginBottom: "1rem" }}>COACH AI</h2>
              <AgentChat />
            </div>
          </div>
        )}

        {activeTab === "intel" && (
          <div>
            <h2 className="section-title" style={{ marginBottom: "1.5rem" }}>
              TOP PERFORMERS · 2022 WORLD CUP
            </h2>
            <div className="performers-grid">
              {TOP_PERFORMERS.map((player, i) => (
                <div key={i} className="performer-card">
                  <div className="performer-top">
                    <div>
                      <p className="performer-name">{player.name}</p>
                      <p className="performer-team">{player.team}</p>
                    </div>
                    <div className="points-badge">
                      <span className="points-num">{player.points}</span>
                      <span className="points-label">pts</span>
                    </div>
                  </div>
                  <div className="performer-stats">
                    <div>
                      <p className="stat-num red">{player.goals}</p>
                      <p className="stat-label">Goals</p>
                    </div>
                    <div>
                      <p className="stat-num gold">{player.assists}</p>
                      <p className="stat-label">Assists</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "standings" && (
          <div>
            <div className="standings-header">
              <h2 className="section-title">2026 WORLD CUP</h2>
              <div className="starts-badge">STARTS JUNE 11</div>
            </div>
            <div className="standings-empty">
              <Trophy size={48} color="#C9963A" />
              <p className="empty-title">TOURNAMENT BEGINS JUNE 11</p>
              <p className="empty-sub">
                Live standings, top scorers, and group tables will appear here automatically once the 2026 World Cup kicks off.
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}