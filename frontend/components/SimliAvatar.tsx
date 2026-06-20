"use client";

import React, { useEffect, useRef } from "react";

interface SimliAvatarProps {
  audioTrack?: MediaStreamTrack;
  isSpeaking: boolean;
}

export default function SimliAvatar({ audioTrack, isSpeaking }: SimliAvatarProps) {
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (audioTrack && audioRef.current) {
        // Create a MediaStream containing the audio track and attach it
        const stream = new MediaStream([audioTrack]);
        audioRef.current.srcObject = stream;
        audioRef.current.play().catch(e => console.error("Audio play error", e));
    }
  }, [audioTrack]);

  return (
    <div className="relative flex flex-col items-center justify-center w-full h-full p-4 rounded-xl bg-gray-900 border border-gray-800 shadow-2xl overflow-hidden">
        {/* Placeholder for the actual Simli WebRTC Video Stream */}
        <div className={`w-48 h-48 rounded-full border-4 ${isSpeaking ? 'border-green-500 animate-pulse' : 'border-gray-700'} bg-gray-800 flex items-center justify-center overflow-hidden transition-all duration-300`}>
            {/* Real implementation would render a <video> element here with Simli's SDK */}
            <span className="text-gray-400 font-medium">Avatar Stream</span>
        </div>
        
        {/* Hidden audio element to actually play the LiveKit incoming audio */}
        <audio ref={audioRef} autoPlay className="hidden" />

        <div className="mt-6 text-center">
            <h3 className="text-xl font-semibold text-white">Healthcare Assistant</h3>
            <p className="text-sm text-gray-400 mt-1">{isSpeaking ? 'Listening / Speaking...' : 'Idle'}</p>
        </div>
    </div>
  );
}
