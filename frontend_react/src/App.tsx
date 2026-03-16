import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Camera, Activity, History, Settings, Play, Square, Video, AlertCircle, Cpu } from 'lucide-react';

// Use relative URL for Vite proxy support
const BACKEND_URL = ''; 

function App() {
  const [activeTab, setActiveTab] = useState('monitor'); // 'monitor', 'events', 'gallery', 'settings'
  const [sourceType, setSourceType] = useState('webcam');
  const [streamUrl, setStreamUrl] = useState('0');
  const [isRunning, setIsRunning] = useState(false);
  const [gallery, setGallery] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Refs for remote streaming
  const videoRef = React.useRef<HTMLVideoElement | null>(null);
  const canvasRef = React.useRef<HTMLCanvasElement>(document.createElement('canvas'));
  const wsRef = React.useRef<WebSocket | null>(null);
  const streamRef = React.useRef<MediaStream | null>(null);
  const captureIntervalRef = React.useRef<any>(null);

  useEffect(() => {
    if (sourceType === 'webcam') setStreamUrl('remote');
    else setStreamUrl(''); // Clear RTSP/HTTP
  }, [sourceType]);

  // Fetch data periodically
  useEffect(() => {
    let interval;
    if (isRunning) {
      interval = setInterval(() => {
        fetchGallery();
        fetchEvents();
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  const fetchGallery = async () => {
    try {
      const resp = await axios.get(`${BACKEND_URL}/api/gallery`);
      setGallery(resp.data);
    } catch (e) { console.error(e); }
  };

  const fetchEvents = async () => {
    try {
      const resp = await axios.get(`${BACKEND_URL}/api/events`);
      setEvents(resp.data);
    } catch (e) { console.error(e); }
  };

  const startStream = async () => {
    setError(null);
    try {
      if (sourceType === 'webcam' && streamUrl === 'remote') {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' }, width: { ideal: 640 }, height: { ideal: 480 } }
        });
        streamRef.current = stream;

        const video = document.createElement('video');
        video.srcObject = stream;
        video.play();
        videoRef.current = video;

        // Connect WebSocket
        const WS_URL = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/api/stream/ws';
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log("WebSocket Connected");
          captureIntervalRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              const canvas = canvasRef.current;
              const ctx = canvas.getContext('2d');
              if (!ctx) return;
              canvas.width = 640;
              canvas.height = 480;
              ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
              canvas.toBlob((blob) => {
                if (blob) ws.send(blob);
              }, 'image/jpeg', 0.6);
            }
          }, 150); // ~7 FPS
        };
      }

      await axios.post(`${BACKEND_URL}/api/stream/start?url=${encodeURIComponent(streamUrl)}`);
      setIsRunning(true);
    } catch (e) {
      setError("Backend Offline or Camera Access Denied. Please run run_native.bat.");
      console.error(e);
      stopStream();
    }
  };

  const stopStream = async () => {
    try {
      // Cleanup local resources
      if (captureIntervalRef.current) clearInterval(captureIntervalRef.current);
      if (wsRef.current) wsRef.current.close();
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());

      await axios.post(`${BACKEND_URL}/api/stream/stop`);
      setIsRunning(false);
    } catch (e) { console.error(e); }
  };

  return (
    <div className="flex flex-col md:flex-row h-screen bg-cyber-900 font-sans selection:bg-neon selection:text-black shadow-inner overflow-hidden">
      {/* Sidebar Navigation - Bottom Nav on Mobile, Side Nav on Desktop */}
      <nav className="w-full md:w-20 border-t md:border-t-0 md:border-r border-white/5 flex flex-row md:flex-col items-center justify-around md:justify-start py-4 md:py-8 gap-4 md:gap-8 bg-cyber-800 shadow-2xl z-20 order-last md:order-first">
        <div className="hidden md:flex w-12 h-12 bg-neon/10 rounded-2xl items-center justify-center border border-neon/30 text-neon shadow-[0_0_15px_rgba(168,85,247,0.2)]">
          <Cpu size={24} />
        </div>
        <div className="flex flex-row md:flex-col gap-2 md:gap-6 w-full md:w-auto justify-around">
          <NavItem active={activeTab === 'monitor'} onClick={() => setActiveTab('monitor')} icon={<Camera size={20} />} label="Live" />
          <NavItem active={activeTab === 'events'} onClick={() => setActiveTab('events')} icon={<Activity size={20} />} label="Events" />
          <NavItem active={activeTab === 'gallery'} onClick={() => setActiveTab('gallery')} icon={<Video size={20} />} label="Gallery" />
          <NavItem active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} icon={<Settings size={20} />} label="System" />
        </div>
      </nav>

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col min-w-0 bg-cyber-900/50 backdrop-blur-sm relative overflow-hidden">
        {/* Decorative Grid */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#00ff9f 1px, transparent 1px)', backgroundSize: '30px 30px' }}></div>

        {/* Top Control Bar */}
        <header className="min-h-20 border-b border-white/5 flex flex-col lg:flex-row items-center p-4 lg:px-8 gap-4 lg:gap-8 justify-between bg-cyber-800/20 backdrop-blur z-10 shrink-0">
          <div className="flex items-center gap-4 w-full lg:w-auto overflow-hidden">
            <h1 className="text-lg lg:text-xl font-black tracking-[0.2em] text-white italic uppercase whitespace-nowrap">
              Vision<span className="text-neon drop-shadow-[0_0_10px_#00ff9f]">X</span>-11
            </h1>
            <div className="h-6 w-[1px] bg-white/10 mx-1"></div>
            <div className="flex items-center gap-2 flex-1">
              <div className="flex bg-black/40 p-1 rounded-lg border border-white/5 shrink-0">
                {['webcam', 'device', 'rtsp', 'http'].map(type => (
                  <button
                    key={type}
                    onClick={() => setSourceType(type)}
                    className={`px-2 lg:px-4 py-1.5 rounded-md text-[8px] lg:text-[10px] font-bold uppercase transition-all ${sourceType === type ? 'bg-neon text-black box-shadow' : 'text-gray-500 hover:text-white'}`}
                  >
                    {type}
                  </button>
                ))}
              </div>
              <input
                className="bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-[10px] lg:text-xs focus:outline-none focus:border-neon/50 w-full max-w-[200px] text-gray-300 font-mono"
                value={streamUrl}
                onChange={(e) => setStreamUrl(e.target.value)}
                placeholder={sourceType === 'rtsp' ? "rtsp://..." : sourceType === 'http' ? "http://..." : "Idx"}
              />
            </div>
          </div>

          <div className="flex items-center gap-4 w-full lg:w-auto justify-between lg:justify-end">
            {error && <div className="text-cyber-red animate-pulse text-[9px] font-bold uppercase flex items-center gap-2 max-w-[150px]"><AlertCircle size={14} /> {error}</div>}
            {!isRunning ? (
              <button onClick={startStream} className="neon-button flex-1 lg:flex-none flex items-center justify-center gap-2 group py-2 lg:py-2">
                <Play size={14} className="group-hover:translate-x-0.5 transition-transform" fill="currentColor" /> <span className="whitespace-nowrap">Start AI</span>
              </button>
            ) : (
              <button onClick={stopStream} className="stop-button flex-1 lg:flex-none flex items-center justify-center gap-2 group py-2 lg:py-2">
                <Square size={14} className="animate-pulse" fill="currentColor" /> <span className="whitespace-nowrap">Stop Stream</span>
              </button>
            )}
          </div>
        </header>

        {/* Dynamic Tab Content */}
        <main className="flex-1 flex flex-col lg:flex-row overflow-hidden p-3 lg:p-6 gap-4 lg:gap-6 relative z-10">
          {activeTab === 'monitor' && (
            <div className="flex-1 flex flex-col gap-4 lg:gap-6 min-w-0 h-full overflow-hidden">
              {/* Monitoring area (Top) */}
              <div className="flex-[3] grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-6 min-h-0">
                <Monitor label="Input Stream" isRunning={isRunning} url={`${BACKEND_URL}/api/stream/raw?t=${Date.now()}`} color="gray" type="raw" />
                <Monitor label="Neural Analysis" isRunning={isRunning} url={`${BACKEND_URL}/api/stream/video?t=${Date.now()}`} color="neon" type="ai" />
              </div>

              {/* Dashboard area (Bottom) - 2:1 Split */}
              <div className="flex-[2] flex flex-col lg:flex-row gap-4 lg:gap-6 min-h-0">
                {/* Event Strip (2/3) */}
                <div className="lg:flex-[2] glass-panel p-4 lg:p-5 flex flex-col min-h-[150px] lg:min-h-0 min-w-0">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-[9px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                      <Activity size={14} className="text-neon" /> RT_BUFFER
                    </h3>
                  </div>
                  <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2 pr-1">
                    {events.slice(0, 10).map((ev, i) => (
                      <EventRow key={i} ev={ev} full={false} />
                    ))}
                    {events.length === 0 && <StandbyText text="Idle..." />}
                  </div>
                </div>

                {/* Identity QuickView (1/3) */}
                <aside className="lg:flex-1 glass-panel flex flex-col min-h-[150px] lg:min-h-0 overflow-hidden shrink-0">
                  <div className="p-4 border-b border-white/5 bg-white/[0.02]">
                    <h2 className="text-[9px] font-black text-white uppercase tracking-widest flex items-center gap-2">
                      <Video size={14} className="text-neon" /> ACTIV_ID
                    </h2>
                  </div>
                  <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-3">
                    {gallery.slice(0, 5).map((p, i) => (
                      <IdentityCard key={i} p={p} full={false} />
                    ))}
                    {gallery.length === 0 && <StandbyText text="Registry Empty" />}
                  </div>
                </aside>
              </div>
            </div>
          )}

          {activeTab === 'events' && (
            <div className="flex-1 glass-panel p-4 lg:p-8 overflow-hidden flex flex-col h-full">
              <h2 className="text-lg lg:text-xl font-bold mb-4 flex items-center gap-3"><Activity className="text-neon" /> Event Log</h2>
              <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3">
                {events.map((ev, i) => <EventRow key={i} ev={ev} full={true} />)}
              </div>
            </div>
          )}

          {activeTab === 'gallery' && (
            <div className="flex-1 glass-panel p-4 lg:p-8 overflow-hidden flex flex-col h-full">
              <h2 className="text-lg lg:text-xl font-bold mb-4 flex items-center gap-3"><Video className="text-neon" /> Subject Records</h2>
              <div className="flex-1 overflow-y-auto custom-scrollbar grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pr-1 text-center">
                {gallery.map((p, i) => <IdentityCard key={i} p={p} full={true} />)}
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="flex-1 glass-panel p-8 flex flex-col items-center justify-center text-center">
              <Settings className="text-neon w-12 h-12 lg:w-16 lg:h-16 mb-4 opacity-20 animate-spin-slow" />
              <h2 className="text-lg lg:text-xl font-bold text-white mb-2 uppercase tracking-tighter">System Config</h2>
              <p className="text-gray-500 text-xs lg:sm max-w-md">Neural parameters optimized for host hardware.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

// Components
const NavItem = ({ active, onClick, icon, label }) => (
  <button
    onClick={onClick}
    className={`group flex flex-col items-center gap-1 transition-all p-3 rounded-xl ${active ? 'bg-neon/10 text-neon shadow-[0_0_15px_rgba(168,85,247,0.05)] border border-neon/20' : 'text-gray-500 hover:text-gray-300'}`}
  >
    {icon}
    <span className="text-[8px] font-black uppercase tracking-tighter opacity-70">{label}</span>
  </button>
);

const Monitor = ({ label, isRunning, url, color, type }) => (
  <div className={`glass-panel overflow-hidden flex flex-col relative group border-${color === 'neon' ? 'neon/20' : 'white/5'}`}>
    <div className={`absolute top-4 left-4 z-10 backdrop-blur px-3 py-1 rounded-full border border-white/10 text-[8px] font-black tracking-widest flex items-center gap-2 uppercase ${color === 'neon' ? 'text-neon bg-neon/5' : 'text-gray-400 bg-black/60'}`}>
      <div className={`w-1 h-1 rounded-full ${isRunning ? (color === 'neon' ? 'bg-neon animate-ping' : 'bg-gray-400') : 'bg-red-900 animate-pulse'}`}></div> {label}
    </div>
    <div className={`flex-1 bg-black overflow-hidden relative ${type === 'raw' ? 'scanline' : ''}`}>
      {isRunning ? (
        <img src={url} className="w-full h-full object-cover" alt={label} />
      ) : (
        <div className="h-full w-full flex items-center justify-center flex-col gap-2">
          <Cpu size={40} className="text-white/[0.02] animate-pulse" />
          <div className="text-[10px] font-black uppercase tracking-[0.4em] text-white/10 italic">Secure Channel Offline</div>
        </div>
      )}
    </div>
  </div>
);

const EventRow = ({ ev, full }) => {
  const isActive = ev.activity === 'Active' || ev.pose === 'Walking';
  const statusColor = isActive ? 'text-[#10b981] border-[#10b981]/20 bg-[#10b981]/5' : 'text-[#f59e0b] border-[#f59e0b]/20 bg-[#f59e0b]/5';
  const dotColor = isActive ? 'bg-[#10b981]' : 'bg-[#f59e0b]';

  return (
    <div className={`flex items-center gap-3 p-2 rounded-lg bg-white/[0.01] border border-white/5 hover:bg-white/[0.03] transition-all group ${full ? 'py-3 px-5' : ''}`}>
      <span className="text-[8px] text-gray-600 font-mono w-12 shrink-0">{ev.time}</span>
      <div className={`h-1 w-1 rounded-full transition-all ${dotColor} shadow-[0_0_5px_currentColor]`}></div>
      
      <div className="flex-1 flex items-center gap-3 min-w-0">
        <span className="text-[9px] font-mono text-neon border border-neon/30 px-1.5 py-0.5 rounded bg-neon/5 shrink-0">
          {ev.hash}
        </span>
        
        <span className="text-[10px] font-bold text-gray-300 uppercase tracking-tight truncate shrink-0">
          {ev.action}
        </span>

        <span className={`text-[8px] font-black px-1.5 py-0.5 rounded border uppercase shrink-0 ${statusColor}`}>
          {ev.pose}
        </span>

        <div className="flex gap-1 overflow-hidden ml-auto">
          {jsonSafeParse(ev.clothes).slice(0, 1).map((c, ci) => (
            <span key={ci} className="text-[8px] text-gray-500 whitespace-nowrap opacity-60 italic">{c}</span>
          ))}
        </div>
      </div>
    </div>
  );
};

const IdentityCard = ({ p, full }) => (
  <div className={`p-3 rounded-2xl bg-cyber-800/40 border border-white/5 hover:border-neon/30 transition-all group relative overflow-hidden ${full ? 'flex flex-col gap-3' : 'flex gap-4'}`}>
    <div className="absolute inset-0 bg-gradient-to-br from-neon/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
    <div className={`shrink-0 bg-black rounded-xl overflow-hidden border border-white/10 shadow-xl group-hover:border-neon/40 transition-all ${full ? 'w-full aspect-square' : 'w-16 h-16'}`}>
      <img src={`data:image/jpeg;base64,${p.photo}`} className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700" alt="Subject" />
    </div>
    <div className="flex-1 min-w-0 flex flex-col justify-between py-1">
      <div>
        <div className="flex items-center justify-between mb-0.5">
          <div className="flex items-center gap-1.5">
            <span className="text-[7px] font-black text-neon uppercase tracking-tighter">IDENT_TOKEN</span>
            <span className={`text-[6px] font-bold px-1 rounded-sm ${p.activity === 'Active' ? 'bg-neon/20 text-neon' : 'bg-gray-800 text-gray-500'}`}>{p.pose}</span>
          </div>
          <span className="text-[7px] text-gray-600 font-mono">{new Date(p.timestamp * 1000).toLocaleTimeString()}</span>
        </div>
        <p className="text-[10px] font-mono text-gray-300 truncate tracking-tight">{p.hash.slice(0, 12)}</p>
      </div>
      <div className="flex flex-wrap gap-1 mt-2">
        {jsonSafeParse(p.clothes).slice(0, 4).map((c, ci) => (
          <span key={ci} className="text-[7px] bg-neon/5 text-neon/70 px-2 py-0.5 rounded border border-neon/10 font-black uppercase tracking-tighter">{c}</span>
        ))}
      </div>
    </div>
  </div>
);

const StandbyText = ({ text }) => (
  <div className="h-full flex flex-col items-center justify-center text-white/[0.05] italic gap-3">
    <div className="w-8 h-[1px] bg-white/[0.05]"></div>
    <span className="text-[10px] uppercase tracking-widest">{text}</span>
    <div className="w-8 h-[1px] bg-white/[0.05]"></div>
  </div>
);

function jsonSafeParse(val) {
  try { return typeof val === 'string' ? JSON.parse(val) : val; }
  catch { return val || []; }
}

export default App;
