"use client";

import React from "react";
import { useTracks, VideoTrack, useRemoteParticipants } from "@livekit/components-react";
import { Track } from "livekit-client";

interface SimliAvatarProps {
  isSpeaking: boolean; // You can pass this or we can detect it internally
}

export default function SimliAvatar({ isSpeaking }: SimliAvatarProps) {
  // Find the camera video track from any remote participant (the backend agent will publish one for the Avatar)
  const tracks = useTracks([{ source: Track.Source.Camera, withPlaceholder: false }]);
  const agentVideoTrack = tracks.find(t => !t.participant.isLocal);

  // Determine if the agent is speaking by checking remote participants
  const remoteParticipants = useRemoteParticipants();
  const agentParticipant = remoteParticipants.find(p => !p.isLocal);
  const agentIsSpeaking = agentParticipant?.isSpeaking || false;

  return (
    <div className="relative flex flex-col items-center justify-center w-full h-full p-4 rounded-xl bg-gray-900 border border-gray-800 shadow-2xl overflow-hidden">
        <div className={`w-48 h-48 rounded-full border-4 ${agentIsSpeaking ? 'border-green-500 animate-pulse' : 'border-gray-700'} bg-gray-800 flex items-center justify-center overflow-hidden transition-all duration-300`}>
            {agentVideoTrack ? (
                <VideoTrack trackRef={agentVideoTrack} className="w-full h-full object-cover" />
            ) : (
                <span className="text-gray-400 font-medium text-center px-4">
                  Avatar Loading...<br/><span className="text-xs text-gray-500">(Waiting for agent video)</span>
                </span>
            )}
        </div>
        
        <div className="mt-6 text-center">
            <h3 className="text-xl font-semibold text-white">Healthcare Assistant</h3>
            <p className="text-sm text-gray-400 mt-1">{agentIsSpeaking ? 'Speaking...' : isSpeaking ? 'Listening...' : 'Idle'}</p>
        </div>
    </div>
  );
}
