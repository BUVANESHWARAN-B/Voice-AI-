"use client";

import { useState, useCallback } from "react";
import { 
  LiveKitRoom, 
  RoomAudioRenderer, 
  useRoomContext,
  useDataChannel,
  useLocalParticipant
} from "@livekit/components-react";
import { Mic, PhoneOff, Activity, Loader2 } from "lucide-react";
import SimliAvatar from "../components/SimliAvatar";
import CallSummary from "../components/CallSummary";
import Image from "next/image";

export default function Home() {
  const [token, setToken] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [toolIndicator, setToolIndicator] = useState("");
  const [callSummary, setCallSummary] = useState<any>(null);

  const startCall = async () => {
    try {
      setConnecting(true);
      const uniqueRoomName = `mavi-lobby-${Math.floor(Math.random() * 10000)}`;
      
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/get-token?room_name=${uniqueRoomName}&participant_name=user`);
      const data = await res.json();
      setToken(data.token);
      setConnected(true);
    } catch (e) {
      console.error("Failed to connect", e);
    } finally {
      setConnecting(false);
    }
  };

  const endCall = async () => {
    setConnected(false);
    setToken("");
    setToolIndicator("");
    
    // Fetch dynamic summary from backend
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/summary`);
      if (response.ok) {
        const data = await response.json();
        setCallSummary(data);
      } else {
        setCallSummary({ summary_text: "Call ended.", appointments: [] });
      }
    } catch (e) {
      console.error("Failed to fetch summary", e);
      setCallSummary({ summary_text: "Call ended.", appointments: [] });
    }
  };

  return (
    <main className="min-h-screen bg-black text-white p-8 flex flex-col items-center">
      <div className="max-w-4xl w-full flex flex-col items-center text-center mb-12">
        <Image src="/logo.png" alt="MAVI Logo" width={80} height={80} className="mb-6 rounded-2xl shadow-lg" />
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-4">
          MAVI - Agentic HealthCare
        </h1>
        <p className="text-gray-400 text-lg">Your intelligent healthcare front desk. Talk naturally to book appointments.</p>
      </div>

      {!connected && !callSummary && (
        <button 
          onClick={startCall}
          disabled={connecting}
          className="group relative inline-flex items-center justify-center gap-2 px-8 py-4 font-semibold text-white transition-all duration-200 bg-blue-600 border border-transparent rounded-full hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {connecting ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Mic className="w-5 h-5 group-hover:scale-110 transition-transform" />
          )}
          {connecting ? "Connecting..." : "Start Call"}
        </button>
      )}

      {connected && (
        <LiveKitRoom
          video={false}
          audio={true}
          token={token}
          serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
          data-lk-theme="default"
          className="w-full max-w-2xl flex flex-col items-center gap-8"
          onDisconnected={endCall}
        >
          <RoomAudioRenderer />
          
          <div className="w-full h-96 relative">
             <SimliAvatarWrapper />
          </div>

          <ToolIndicatorWrapper indicator={toolIndicator} />

          <button
            onClick={endCall}
            className="flex items-center gap-2 px-6 py-3 bg-red-500/10 text-red-500 border border-red-500/20 rounded-full hover:bg-red-500 hover:text-white transition-colors font-medium"
          >
            <PhoneOff className="w-5 h-5" /> End Call
          </button>
        </LiveKitRoom>
      )}

      {callSummary && (
        <div className="w-full flex flex-col items-center">
          <CallSummary summary={callSummary} />
          <button 
            onClick={() => setCallSummary(null)}
            className="mt-8 px-6 py-2 text-gray-400 hover:text-white transition-colors"
          >
            Start New Call
          </button>
        </div>
      )}
    </main>
  );
}

// Subcomponents to access LiveKit context safely
function SimliAvatarWrapper() {
  const { localParticipant } = useLocalParticipant();
  // Using microphone state to simulate "speaking" activity simply for UI
  const isSpeaking = localParticipant?.isSpeaking || false;
  return <SimliAvatar isSpeaking={isSpeaking} />;
}

function ToolIndicatorWrapper({ indicator }: { indicator: string }) {
  const [liveIndicator, setLiveIndicator] = useState(indicator);
  
  // Listen for custom data events from the backend agent
  useDataChannel("tools", (msg) => {
    const text = new TextDecoder().decode(msg.payload);
    setLiveIndicator(text);
    setTimeout(() => setLiveIndicator(""), 4000);
  });

  if (!liveIndicator) return null;

  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 px-6 py-3 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-full flex items-center gap-3">
      <Activity className="w-4 h-4 animate-pulse" />
      <span className="font-medium text-sm">{liveIndicator}</span>
    </div>
  );
}
