import { useState, useEffect, useRef } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Activity,
  Cpu,
  Zap,
  Lock,
  RefreshCw,
  Radio,
  Terminal,
  CheckCircle2,
  XCircle,
  Sun,
  Moon,
  UploadCloud,
  FileText,
  Binary,
  FileCheck,
  AlertCircle,
  Sparkles
} from 'lucide-react';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const API_BASE = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/ws';

interface LogItem {
  id?: number;
  request_id: string;
  timestamp: string;
  client_id: string;
  attack_type: string;
  message: string;
  fidelity: number;
  anomaly_score: number;
  threshold: number;
  verdict: string;
  status_code: string;
  details: string;
}

interface Stats {
  total_requests: number;
  accepted_count: number;
  rejected_count: number;
  accept_rate: number;
  avg_anomaly_score: number;
  avg_fidelity: number;
  attack_breakdown: Record<string, number>;
}

export default function App() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [stats, setStats] = useState<Stats>({
    total_requests: 0,
    accepted_count: 0,
    rejected_count: 0,
    accept_rate: 100,
    avg_anomaly_score: 0,
    avg_fidelity: 1.0,
    attack_breakdown: {}
  });

  const [simulating, setSimulating] = useState(false);
  const [manualMessage, setManualMessage] = useState("Transfer $250,000 to Quantum Reserve");

  // Quantum File Transmission State
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileHash, setFileHash] = useState<string>('');
  const [pauliCorrections, setPauliCorrections] = useState<string[]>([]);
  const [fileTransmitting, setFileTransmitting] = useState<boolean>(false);
  const [fileVerifyResult, setFileVerifyResult] = useState<any | null>(null);

  const generateLegitimatePauliCorrections = (hashHex: string): string[] => {
    const base = [
      ...Array(8).fill('I'),
      ...Array(8).fill('X'),
      ...Array(8).fill('Y'),
      ...Array(8).fill('Z')
    ];
    const seedBits = parseInt(hashHex.slice(0, 8), 16) || 12345;
    const corrections = [...base];
    for (let i = corrections.length - 1; i > 0; i--) {
      const j = Math.abs((seedBits * (i + 1) * 37) % (i + 1));
      [corrections[i], corrections[j]] = [corrections[j], corrections[i]];
    }
    return corrections;
  };

  const computeFileSignature = async (file: File) => {
    try {
      setSelectedFile(file);
      const buffer = await file.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
      setFileHash(hashHex);

      const corrections = generateLegitimatePauliCorrections(hashHex);
      setPauliCorrections(corrections);
      setFileVerifyResult(null);
    } catch (err) {
      console.error('Failed to compute file hash', err);
    }
  };

  const handleTransmitFile = async (mode: 'legit' | 'tamper_payload' | 'tamper_pauli') => {
    if (!selectedFile || !fileHash) return;
    setFileTransmitting(true);
    try {
      let finalCorrections = generateLegitimatePauliCorrections(fileHash);
      const finalHash = fileHash;
      let finalFile: Blob = selectedFile;

      if (mode === 'tamper_payload') {
        const buffer = await selectedFile.arrayBuffer();
        const corrupted = new Uint8Array(buffer.byteLength + 1);
        corrupted.set(new Uint8Array(buffer), 0);
        corrupted[buffer.byteLength] = 0xff;
        finalFile = new Blob([corrupted], { type: selectedFile.type });
      } else if (mode === 'tamper_pauli') {
        finalCorrections = [
          ...Array(20).fill('I'),
          ...Array(6).fill('X'),
          ...Array(4).fill('Y'),
          ...Array(2).fill('Z')
        ];
      }

      const signaturePayload = {
        session_id: 'sess_demo1',
        identity: 'alice',
        nonce: typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `nonce_${Date.now()}_${Math.random()}`,
        timestamp: Date.now() / 1000,
        signature_data: {
          pauli_corrections: finalCorrections,
          message_hash: finalHash
        }
      };

      const formData = new FormData();
      formData.append('file', finalFile, selectedFile.name);
      formData.append('signature_json', JSON.stringify(signaturePayload));

      const res = await fetch(`http://localhost:8000/files/upload-and-verify`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setFileVerifyResult(data);
      fetchStats();
    } catch (err) {
      console.error('File transmission failed', err);
    } finally {
      setFileTransmitting(false);
    }
  };

  // Connect WebSocket & Fetch Initial Data
  useEffect(() => {
    fetchStatsAndHistory();

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      setConnected(true);
      console.log('Connected to QubitX Telemetry WebSocket');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event_type === 'VERIFICATION_COMPLETED') {
        const newLog: LogItem = {
          request_id: data.request_id,
          timestamp: new Date().toLocaleTimeString(),
          client_id: data.client_id,
          attack_type: data.attack_type,
          message: data.message,
          fidelity: data.result.fidelity,
          anomaly_score: data.result.anomaly_score,
          threshold: data.result.threshold,
          verdict: data.result.verdict,
          status_code: data.result.status_code,
          details: data.result.details
        };

        setLogs(prev => [newLog, ...prev.slice(0, 49)]);
        fetchStats();
      } else if (data.event_type === 'CONNECTED') {
        if (Array.isArray(data.recent_history)) setLogs(data.recent_history);
        if (data.stats && typeof data.stats === 'object' && !data.stats.detail) {
          setStats(prev => ({ ...prev, ...data.stats, attack_breakdown: data.stats.attack_breakdown || {} }));
        }
      }
    };

    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    return () => ws.close();
  }, []);

  const fetchStatsAndHistory = async () => {
    try {
      const [statsRes, historyRes] = await Promise.all([
        fetch(`${API_BASE}/stats`),
        fetch(`${API_BASE}/history?limit=50`)
      ]);
      const statsData = await statsRes.json();
      const historyData = await historyRes.json();
      if (statsData && typeof statsData === 'object' && !statsData.detail) {
        setStats(prev => ({ ...prev, ...statsData, attack_breakdown: statsData.attack_breakdown || {} }));
      }
      if (Array.isArray(historyData)) {
        setLogs(historyData);
      }
    } catch (e) {
      console.error('Failed to load initial stats', e);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      const data = await res.json();
      if (data && typeof data === 'object' && !data.detail) {
        setStats(prev => ({ ...prev, ...data, attack_breakdown: data.attack_breakdown || {} }));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const triggerVerification = async (attackType: string) => {
    setSimulating(true);
    try {
      const isAttack = attackType !== 'none';
      const endpoint = isAttack ? `${API_BASE}/attack` : `${API_BASE}/verify`;
      const payload = isAttack
        ? {
          attacker_id: `demo_${attackType}_client`,
          attack_type: attackType,
          message: manualMessage
        }
        : {
          client_id: "demo_legitimate_client",
          message: manualMessage,
          attack_type: "none"
        };

      await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (e) {
      console.error('Trigger verification failed', e);
    } finally {
      setSimulating(false);
    }
  };

  const safeLogs = Array.isArray(logs) ? logs : [];
  const safeBreakdown = stats?.attack_breakdown || {};

  // Chart Data: Anomaly Scores Timeline
  const scoreTimelineData = {
    labels: safeLogs.slice().reverse().map((_, idx) => `Req ${idx + 1}`),
    datasets: [
      {
        label: 'Anomaly Score',
        data: safeLogs.slice().reverse().map(l => l.anomaly_score ?? 0),
        borderColor: '#0095f6',
        backgroundColor: 'rgba(0, 149, 246, 0.08)',
        fill: true,
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: '#0095f6'
      },
      {
        label: 'Safety Threshold (7.815)',
        data: safeLogs.slice().reverse().map(() => 7.815),
        borderColor: '#ed4956',
        borderDash: [4, 4],
        pointRadius: 0,
        borderWidth: 1.5
      }
    ]
  };

  // Chart Data: Attack Types Breakdown
  const attackBreakdownData = {
    labels: ['Legitimate', 'Forgery', 'Replay', 'Impersonation', 'Intercept-Resend'],
    datasets: [
      {
        data: [
          safeBreakdown['none'] || 0,
          safeBreakdown['forgery'] || 0,
          safeBreakdown['replay'] || 0,
          safeBreakdown['impersonation'] || 0,
          safeBreakdown['intercept_resend'] || 0
        ],
        backgroundColor: [
          '#78de45',
          '#ed4956',
          '#ffc107',
          '#a855f7',
          '#0095f6'
        ],
        borderWidth: 0
      }
    ]
  };

  return (
    <div style={{ padding: '32px 40px', maxWidth: '1360px', margin: '0 auto' }}>
      {/* Top Header Navigation */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px', paddingBottom: '20px', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          {/* Futuristic Glowing 3D Quantum Badge */}
          <div style={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <div style={{
              position: 'absolute',
              inset: '-4px',
              borderRadius: '22px',
              background: 'var(--ig-gradient)',
              filter: 'blur(10px)',
              opacity: 0.7
            }}></div>
            <div style={{
              position: 'relative',
              background: 'var(--ig-gradient)',
              padding: '3px',
              borderRadius: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 10px 25px -5px rgba(220, 39, 67, 0.5)'
            }}>
              <div style={{
                background: 'var(--bg-card)',
                padding: '12px',
                borderRadius: '17px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backdropFilter: 'blur(10px)'
              }}>
                <Cpu size={30} color="var(--accent-blue)" style={{ filter: 'drop-shadow(0 0 8px rgba(0, 149, 246, 0.6))' }} />
              </div>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 className="brand-font" style={{
                fontSize: '2.1rem',
                fontWeight: 800,
                letterSpacing: '-0.03em',
                background: 'linear-gradient(135deg, var(--text-primary) 30%, var(--accent-blue) 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                lineHeight: 1.1
              }}>
                QubitX
              </h1>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.7rem',
                fontWeight: 700,
                padding: '4px 12px',
                borderRadius: '100px',
                background: 'linear-gradient(180deg, rgba(0, 149, 246, 0.15) 0%, rgba(0, 149, 246, 0.05) 100%)',
                color: 'var(--accent-blue)',
                border: '1px solid rgba(0, 149, 246, 0.35)',
                boxShadow: '0 4px 12px rgba(0, 149, 246, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
                letterSpacing: '0.05em',
                textTransform: 'uppercase'
              }}>
                <span style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--accent-blue)',
                  boxShadow: '0 0 8px var(--accent-blue)'
                }}></span>
                QDS Engine
              </div>
            </div>
            <p style={{
              fontSize: '0.85rem',
              color: 'var(--text-secondary)',
              marginTop: '4px',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <span>Quantum Teleportation</span>
              <span style={{ opacity: 0.4 }}>•</span>
              <span>Statistical Threat Intelligence</span>
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button onClick={toggleTheme} className="ig-btn-attack" style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }} title="Toggle Light/Dark Theme">
            {theme === 'dark' ? <Sun size={14} color="var(--accent-yellow)" /> : <Moon size={14} color="var(--text-primary)" />}
            <span>{theme === 'dark' ? 'Light' : 'Dark'} Mode</span>
          </button>

          <div className="ig-card" style={{ padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem' }}>
            <Radio size={14} color={connected ? 'var(--accent-green)' : 'var(--accent-red)'} />
            <span style={{ color: connected ? 'var(--text-primary)' : 'var(--accent-red)', fontWeight: 600 }}>
              {connected ? 'Live Feed Connected' : 'Disconnected'}
            </span>
          </div>

          <button onClick={fetchStatsAndHistory} className="ig-btn-attack" style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
      </header>

      {/* Top Metrics Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '28px' }}>
        <div className="ig-card" style={{ padding: '22px 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '12px' }}>
            <span>Total Requests</span>
            <Activity size={18} color="var(--accent-blue)" />
          </div>
          <div className="rich-title" style={{ fontSize: '2.1rem', fontWeight: 800 }}>{stats.total_requests}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px', fontWeight: 500 }}>Teleportation Signatures</div>
        </div>

        <div className="ig-card" style={{ padding: '22px 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '12px' }}>
            <span>Accept Rate</span>
            <ShieldCheck size={18} color="var(--accent-green)" />
          </div>
          <div className="rich-title" style={{ fontSize: '2.1rem', fontWeight: 800, color: 'var(--accent-green)' }}>{stats.accept_rate}%</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px', fontWeight: 500 }}>
            <span>{stats.accepted_count}</span> Approved Signatures
          </div>
        </div>

        <div className="ig-card" style={{ padding: '22px 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '12px' }}>
            <span>Attacks Rejected</span>
            <ShieldAlert size={18} color="var(--accent-red)" />
          </div>
          <div className="rich-title" style={{ fontSize: '2.1rem', fontWeight: 800, color: 'var(--accent-red)' }}>{stats.rejected_count}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px', fontWeight: 500 }}>Security Threat Events</div>
        </div>

        <div className="ig-card" style={{ padding: '22px 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '12px' }}>
            <span>Avg Quantum Fidelity</span>
            <Zap size={18} color="#c084fc" />
          </div>
          <div className="rich-title" style={{ fontSize: '2.1rem', fontWeight: 800, color: '#c084fc' }}>{(stats.avg_fidelity * 100).toFixed(1)}%</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px', fontWeight: 500 }}>Statevector Overlap Score</div>
        </div>
      </div>

      {/* Main Grid Section: Charts & Simulation Controller */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '24px' }}>
        {/* Real-Time Anomaly Score Timeline Chart */}
        <div className="ig-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
            <Activity size={16} color="var(--accent-blue)" /> Anomaly Score vs Threshold
          </h3>
          <div style={{ height: '240px' }}>
            <Line
              data={scoreTimelineData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    labels: {
                      color: '#a8a8a8',
                      font: { family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto', size: 12 }
                    }
                  }
                },
                scales: {
                  y: {
                    min: 0,
                    max: 40,
                    grid: { color: '#262626' },
                    ticks: { color: '#737373' }
                  },
                  x: {
                    grid: { color: '#1a1a1a' },
                    ticks: { color: '#737373' }
                  }
                }
              }}
            />
          </div>
        </div>

        {/* Attack Type Breakdown Chart */}
        <div className="ig-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '16px', alignSelf: 'flex-start', color: 'var(--text-primary)' }}>
            Threat Distribution
          </h3>
          <div style={{ width: '190px', height: '190px' }}>
            <Doughnut data={attackBreakdownData} options={{ maintainAspectRatio: false, plugins: { legend: { display: false } } }} />
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '16px', justifyContent: 'center', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: 8, height: 8, borderRadius: '50%', background: '#78de45' }}></span> Legitimate</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ed4956' }}></span> Forgery</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ffc107' }}></span> Replay</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: 8, height: 8, borderRadius: '50%', background: '#a855f7' }}></span> Impersonation</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: 8, height: 8, borderRadius: '50%', background: '#0095f6' }}></span> Intercept</span>
          </div>
        </div>
      </div>

      {/* Quantum File Transmission & Pauli Verification Widget */}
      <div className="ig-card" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
              <Sparkles size={18} color="var(--accent-blue)" /> Quantum File Transmission & Pauli Verification
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Sign any real file using 32-round Bell-state Pauli measurements ($I, X, Y, Z$) and verify file integrity & non-repudiation in real time.
            </p>
          </div>
          <span className="ig-badge ig-badge-accept">
            <ShieldCheck size={12} /> Multi-Round $\chi^2$ Engine
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
          {/* Left Column: Dropzone & Pauli Sequence */}
          <div>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  computeFileSignature(e.target.files[0]);
                }
              }}
            />

            {!selectedFile ? (
              <div
                className="qds-dropzone"
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    computeFileSignature(e.dataTransfer.files[0]);
                  }
                }}
              >
                <UploadCloud size={32} color="var(--accent-blue)" style={{ margin: '0 auto 10px auto' }} />
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Click or Drag & Drop Any File to Sign
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Supports PDF, TXT, DOCX, PNG, Binary, or any payload
                </div>
              </div>
            ) : (
              <div style={{ background: 'var(--bg-input)', borderRadius: '10px', padding: '16px', border: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileText size={18} color="var(--accent-blue)" />
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{selectedFile.name}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{(selectedFile.size / 1024).toFixed(2)} KB • SHA-256 Calculated</div>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedFile(null);
                      setFileHash('');
                      setPauliCorrections([]);
                      setFileVerifyResult(null);
                    }}
                    style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.78rem' }}
                  >
                    Change File
                  </button>
                </div>

                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px', fontWeight: 600 }}>SHA-256 MESSAGE DIGEST</div>
                  <div style={{ background: 'var(--bg-card)', padding: '6px 10px', borderRadius: '6px', fontSize: '0.72rem', fontFamily: 'monospace', color: '#0095f6', wordBreak: 'break-all', border: '1px solid var(--border-color)' }}>
                    {fileHash}
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                      32-ROUND PAULI SIGNATURE BASIS ($I, X, Y, Z$)
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                      32 Measurement Rounds
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {pauliCorrections.map((p, idx) => (
                      <span key={idx} className={`pauli-pill pauli-${p}`} title={`Round ${idx + 1}: Pauli-${p}`}>
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Transmission Controls & Defender Verdict */}
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
                TRANSMISSION & THREAT SIMULATION
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
                <button
                  onClick={() => handleTransmitFile('legit')}
                  disabled={!selectedFile || fileTransmitting}
                  className="qds-btn-transmit"
                  style={{ opacity: !selectedFile ? 0.5 : 1 }}
                >
                  <FileCheck size={16} /> Transmit Authentic QDS File (Verify)
                </button>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => handleTransmitFile('tamper_payload')}
                    disabled={!selectedFile || fileTransmitting}
                    className="qds-btn-tamper"
                    style={{ flex: 1, opacity: !selectedFile ? 0.5 : 1 }}
                    title="Alters payload content in transit to test SHA-256 digest integrity rejection"
                  >
                    <AlertCircle size={14} /> Tamper File Payload
                  </button>

                  <button
                    onClick={() => handleTransmitFile('tamper_pauli')}
                    disabled={!selectedFile || fileTransmitting}
                    className="qds-btn-tamper"
                    style={{ flex: 1, opacity: !selectedFile ? 0.5 : 1 }}
                    title="Alters Pauli measurement distribution to trigger Chi-Square statistical rejection"
                  >
                    <Binary size={14} /> Inject Pauli Basis Noise
                  </button>
                </div>
              </div>
            </div>

            {/* Defender Verification Report Card */}
            {fileVerifyResult ? (
              <div
                style={{
                  background: fileVerifyResult.verdict === 'ACCEPT' ? 'rgba(120, 222, 69, 0.08)' : 'rgba(237, 73, 86, 0.08)',
                  border: `1px solid ${fileVerifyResult.verdict === 'ACCEPT' ? 'rgba(120, 222, 69, 0.3)' : 'rgba(237, 73, 86, 0.3)'}`,
                  borderRadius: '8px',
                  padding: '14px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '0.88rem', color: fileVerifyResult.verdict === 'ACCEPT' ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                    {fileVerifyResult.verdict === 'ACCEPT' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                    VERDICT: {fileVerifyResult.verdict}
                  </div>
                  <span className={`ig-badge ${fileVerifyResult.verdict === 'ACCEPT' ? 'ig-badge-accept' : 'ig-badge-reject'}`}>
                    {fileVerifyResult.result?.status_code || (fileVerifyResult.verdict === 'ACCEPT' ? '200 OK' : '403 FORBIDDEN')}
                  </span>
                </div>

                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                  <div>Integrity Match: <strong style={{ color: fileVerifyResult.integrity_ok ? 'var(--accent-green)' : 'var(--accent-red)' }}>{fileVerifyResult.integrity_ok ? 'VALID' : 'TAMPERED'}</strong></div>
                  <div>χ² Anomaly Score: <strong style={{ color: 'var(--text-primary)' }}>{fileVerifyResult.result?.anomaly_score?.toFixed(2) ?? 'N/A'} (Thresh: 7.815)</strong></div>
                  <div>Attack Type: <strong style={{ color: 'var(--text-primary)' }}>{fileVerifyResult.attack_type || 'none'}</strong></div>
                  <div>Fidelity: <strong style={{ color: 'var(--text-primary)' }}>{(fileVerifyResult.result?.fidelity * 100).toFixed(0)}%</strong></div>
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '8px', fontStyle: 'italic' }}>
                  {fileVerifyResult.result?.details || 'Transmission processed by Defender.'}
                </div>
              </div>
            ) : (
              <div style={{ background: 'var(--bg-input)', borderRadius: '8px', padding: '14px', border: '1px solid var(--border-color)', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Select a file and click an action above to execute real-time quantum verification.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Attack Simulator Control Panel */}
      <div className="ig-card" style={{ padding: '20px', marginBottom: '24px' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
          <Terminal size={16} color="var(--accent-blue)" /> QDS Simulation Console
        </h3>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="text"
            className="ig-input"
            value={manualMessage}
            onChange={(e) => setManualMessage(e.target.value)}
            placeholder="Enter Message Payload..."
            style={{
              flex: 1,
              minWidth: '260px'
            }}
          />

          <button onClick={() => triggerVerification('none')} disabled={simulating} className="ig-btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle2 size={15} /> Send Legitimate QDS
          </button>

          <button onClick={() => triggerVerification('forgery')} disabled={simulating} className="ig-btn-attack">
            Forge Signature
          </button>

          <button onClick={() => triggerVerification('replay')} disabled={simulating} className="ig-btn-attack">
            Replay Attack
          </button>

          <button onClick={() => triggerVerification('impersonation')} disabled={simulating} className="ig-btn-attack">
            Impersonate Key
          </button>

          <button onClick={() => triggerVerification('intercept_resend')} disabled={simulating} className="ig-btn-attack">
            Intercept-Resend
          </button>
        </div>
      </div>

      {/* Audit History Log Table */}
      <div className="ig-card" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
          <Lock size={16} color="var(--accent-blue)" /> Security Audit Logs
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.04em' }}>
                <th style={{ padding: '10px 12px' }}>TIMESTAMP</th>
                <th style={{ padding: '10px 12px' }}>CLIENT ID</th>
                <th style={{ padding: '10px 12px' }}>ATTACK TYPE</th>
                <th style={{ padding: '10px 12px' }}>FIDELITY</th>
                <th style={{ padding: '10px 12px' }}>ANOMALY SCORE</th>
                <th style={{ padding: '10px 12px' }}>VERDICT</th>
                <th style={{ padding: '10px 12px' }}>DETAILS</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #1a1a1a', transition: 'background-color 0.15s ease' }}>
                  <td style={{ padding: '12px', color: 'var(--text-muted)', fontSize: '0.78rem' }} className="font-mono">{log.timestamp || 'Just now'}</td>
                  <td style={{ padding: '12px', fontWeight: 500, color: 'var(--text-primary)' }}>{log.client_id}</td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '0.72rem',
                      fontWeight: 600,
                      background: log.attack_type === 'none' ? 'rgba(120, 222, 69, 0.1)' : 'rgba(237, 73, 86, 0.1)',
                      color: log.attack_type === 'none' ? 'var(--accent-green)' : 'var(--accent-red)'
                    }}>
                      {log.attack_type.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '12px', color: 'var(--text-secondary)' }} className="font-mono">{(log.fidelity * 100).toFixed(1)}%</td>
                  <td style={{ padding: '12px', fontWeight: 600, color: log.anomaly_score > 12.0 ? 'var(--accent-red)' : 'var(--accent-blue)' }} className="font-mono">
                    {log.anomaly_score}
                  </td>
                  <td style={{ padding: '12px' }}>
                    {log.verdict === 'ACCEPT' ? (
                      <span className="ig-badge ig-badge-accept"><CheckCircle2 size={11} /> ACCEPT</span>
                    ) : (
                      <span className="ig-badge ig-badge-reject"><XCircle size={11} /> REJECT</span>
                    )}
                  </td>
                  <td style={{ padding: '12px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

