"use client";

import { useState, useEffect } from "react";
import { Trophy, TrendingUp, Users, Zap, Star } from "lucide-react";



const DEMO_LINEUP = {
  GK: [{ name: "S. Gonda", nationality: "JPN", points: 8 }],
  DEF: [
    { name: "Y. Sabaly", nationality: "SEN", points: 8 },
    { name: "Pedro Miguel", nationality: "QAT", points: 6 },
    { name: "Boualem Khoukhi", nationality: "QAT", points: 6 },
    { name: "S. Vitória", nationality: "CAN", points: 5 },
  ],
  MID: [
    { name: "S. Amallah", nationality: "MAR", points: 10 },
    { name: "R. Cheshmi", nationality: "IRN", points: 7 },
    { name: "Mohammed Muntari", nationality: "QAT", points: 6 },
  ],
  FWD: [
    { name: "C. Goodwin", nationality: "AUS", points: 10 },
    { name: "Mohammed Muntari", nationality: "QAT", points: 7 },
    { name: "M. Estrada", nationality: "ECU", points: 6 },
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

const nationalityToCode: Record<string, string> = {
  "JPN": "jp", "SEN": "sn", "QAT": "qa", "CAN": "ca",
  "MAR": "ma", "IRN": "ir", "AUS": "au", "ECU": "ec",
  "FRA": "fr", "ARG": "ar", "ENG": "gb-eng", "GER": "de",
  "BRA": "br", "ESP": "es", "POR": "pt", "NED": "nl",
  "BEL": "be", "CRO": "hr", "URU": "uy", "SUI": "ch",
  "DEN": "dk", "KOR": "kr", "USA": "us", "MEX": "mx",
  "POL": "pl", "SRB": "rs", "CMR": "cm", "GHA": "gh",
  "TUN": "tn", "KSA": "sa", "CRC": "cr", "WAL": "gb-wls",
  "Japan": "jp", "Senegal": "sn", "Qatar": "qa", "Canada": "ca",
  "Morocco": "ma", "Iran": "ir", "Australia": "au", "Ecuador": "ec",
  "France": "fr", "Argentina": "ar", "England": "gb-eng", "Germany": "de",
  "Brazil": "br", "Spain": "es", "Portugal": "pt", "Netherlands": "nl",
};

function PlayerCard({ player, position}: {
  player: { name: string; nationality: string; points: number; photo?: string };
  position: string;
}) {
  const countryCode = nationalityToCode[player.nationality] || "un";
  const [tooltip, setTooltip] = useState<{ x: number; y: number } | null>(null);

  return (
    <div
      className="player-card"
      style={{ position: "relative" }}
      onMouseEnter={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        setTooltip({ x: rect.left + rect.width / 2, y: rect.top });
      }}
      onMouseLeave={() => setTooltip(null)}
    >
      <div className="card-inner" style={{ borderColor: positionColors[position] }}>
        <div className="card-top" style={{ backgroundColor: positionColors[position] }} />
        <span className="card-position" style={{ color: positionColors[position] }}>
          {position}
        </span>
        <div className="card-avatar" style={{ backgroundColor: positionColors[position] }}>
          <img
            src={`https://flagcdn.com/w40/${countryCode}.png`}
            alt={player.nationality}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            onError={(e) => { e.currentTarget.style.display = "none"; }}
          />
        </div>
        <span className="card-name">{player.name.split(" ").pop()}</span>
        <span className="card-pts">{player.points} pts</span>
      </div>

      {tooltip && (
        <div
          style={{
            position: "fixed",
            left: `${tooltip.x}px`,
            top: `${tooltip.y - 8}px`,
            transform: "translate(-50%, -100%)",
            zIndex: 9999,
            backgroundColor: "var(--card-bg)",
            border: `2px solid ${positionColors[position]}`,
            borderRadius: "12px",
            padding: "12px",
            width: "140px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.3)",
            pointerEvents: "none",
          }}
        >
          <div style={{
            height: "4px",
            borderRadius: "10px 10px 0 0",
            backgroundColor: positionColors[position],
            margin: "-12px -12px 8px -12px",
          }} />
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
            <img
              src={`https://flagcdn.com/w40/${countryCode}.png`}
              alt={player.nationality}
              style={{ width: "28px", height: "18px", objectFit: "cover", borderRadius: "2px" }}
            />
            <span style={{
              fontFamily: "Bebas Neue, sans-serif",
              fontSize: "0.65rem",
              color: positionColors[position],
              letterSpacing: "0.08em"
            }}>
              {position}
            </span>
          </div>
          <p style={{
            fontFamily: "Bebas Neue, sans-serif",
            fontSize: "1rem",
            letterSpacing: "0.05em",
            marginBottom: "4px",
            lineHeight: 1.2
          }}>
            {player.name}
          </p>
          <p style={{
            fontSize: "0.7rem",
            color: "var(--ink-muted)",
            fontFamily: "DM Sans, sans-serif",
            marginBottom: "8px"
          }}>
            {player.nationality}
          </p>
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "6px 8px",
            borderRadius: "6px",
            backgroundColor: positionColors[position],
          }}>
            <span style={{ color: "rgba(255,255,255,0.8)", fontSize: "0.65rem", fontFamily: "DM Sans, sans-serif" }}>
              Fantasy pts
            </span>
            <span style={{
              color: "white",
              fontFamily: "Bebas Neue, sans-serif",
              fontSize: "1.1rem"
            }}>
              {player.points}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function PitchView({ playersMap }: { playersMap: Record<string, string> }) {
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
          <PlayerCard key={i} player={{ ...p, photo: playersMap[p.name] }} position="FWD"/>
        ))}
      </div>
      <div className="pitch-row">
        {DEMO_LINEUP.MID.map((p, i) => (
          <PlayerCard key={i} player={{ ...p, photo: playersMap[p.name] }} position="MID"/>
        ))}
      </div>
      <div className="pitch-row">
        {DEMO_LINEUP.DEF.map((p, i) => (
          <PlayerCard key={i} player={{ ...p, photo: playersMap[p.name] }} position="DEF"/>
        ))}
      </div>
      <div className="pitch-row">
       {DEMO_LINEUP.GK.map((p, i) => (
          <PlayerCard key={i} player={{ ...p, photo: playersMap[p.name] }} position="GK"/>
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

    try {
      const response = await fetch("https://worldcup-fantasy-agent-production.up.railway.app/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, user_id: "default_user" }),
      });
      const data = await response.json();
      setMessages((prev) => [...prev, { role: "agent", text: data.response }]);
    } catch {
      setMessages((prev) => [...prev, {
        role: "agent",
        text: "Connection error. The coach is taking too long to respond. Please try again.",
      }]);
    } finally {
      setLoading(false);
    }
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
            <div className="bubble muted">Analyzing... (this may take 30-60 seconds)</div>
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
  const [topPerformers, setTopPerformers] = useState(TOP_PERFORMERS);
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("https://worldcup-fantasy-agent-production.up.railway.app/top-performers");
        const data = await response.json();
        if (data.stats && data.stats.length > 0) {
          const mapped = data.stats.slice(0, 5).map((p: any) => ({
            name: p.player_name,
            team: `${p.total_goals}G · ${p.total_assists}A · ${p.matches_played} games`,
            points: p.total_points,
            goals: p.total_goals,
            assists: p.total_assists,
          }));
          setTopPerformers(mapped);
        }
      } catch {
        console.log("Using demo data");
      } finally {
        setLoadingData(false);
      }
    };
    fetchData();
  }, []);

  const [lineup, setLineup] = useState<any>(null);

  useEffect(() => {
    const fetchLineup = async () => {
      try {
        const response = await fetch("https://worldcup-fantasy-agent-production.up.railway.app/lineup/luan?matchday=1");
        const data = await response.json();
        if (data.lineup) {
          setLineup(data.lineup);
        }
      } catch {
        console.log("Using demo lineup");
      }
    };
    fetchLineup();
  }, []);

  const [playersMap, setPlayersMap] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const response = await fetch("https://worldcup-fantasy-agent-production.up.railway.app/players");
        const data = await response.json();
        if (data.players) {
          const map: Record<string, string> = {};
          data.players.forEach((p: any) => {
            map[p.name] = p.photo;
          });
          setPlayersMap(map);
        }
      } catch {
        console.log("Could not load player photos");
      }
    };
    fetchPlayers();
  }, []);

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
              <PitchView playersMap={playersMap} />
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
            {loadingData ? (
              <div style={{ color: "var(--ink-muted)", fontFamily: "DM Sans, sans-serif" }}>
                Loading player data...
              </div>
            ) : (
              <div className="performers-grid">
              {topPerformers.map((player, i) => (
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
            )}
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