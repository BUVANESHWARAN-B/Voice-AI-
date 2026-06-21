"use client";

import React from "react";
import { useTracks, VideoTrack, useRemoteParticipants } from "@livekit/components-react";
import { Track } from "livekit-client";

interface SimliAvatarProps {
  isSpeaking: boolean; // You can pass this or we can detect it internally
}

export default function SimliAvatar({ isSpeaking }: SimliAvatarProps) {
  // Reactively fetch video tracks (Camera or Unknown source) to capture Simli's avatar feed
  const tracks = useTracks([
    { source: Track.Source.Camera, withPlaceholder: false },
    { source: Track.Source.Unknown, withPlaceholder: false }
  ]);

  // Find the first remote video track safely
  const agentVideoTrackRef = tracks.find(t => !t.participant.isLocal && t.publication.kind === Track.Kind.Video);

  const remoteParticipants = useRemoteParticipants();

  // Determine if the agent is speaking by finding the participant with audio
  const audioParticipant = remoteParticipants.find(p => !p.isLocal && p.audioTrackPublications.size > 0);
  const agentIsSpeaking = audioParticipant?.isSpeaking || false;

  return (
    <div className="relative flex flex-col items-center justify-center w-full h-full p-4 rounded-xl bg-gray-900 border border-gray-800 shadow-2xl overflow-hidden">
        <div className={`w-48 h-48 rounded-full border-4 ${agentIsSpeaking ? 'border-green-500 animate-pulse' : 'border-gray-700'} bg-gray-800 flex items-center justify-center overflow-hidden transition-all duration-300`}>
            {agentVideoTrackRef ? (
                <VideoTrack trackRef={agentVideoTrackRef} className="w-full h-full object-cover" />
            ) : (
                <span className="text-gray-400 font-medium text-center px-4">
                  Avatar Loading...<br/><span className="text-xs text-gray-500">(Waiting for agent video)</span>
                </span>
            )}
        </div>
        
        <div className="mt-6 text-center">
            <h3 className="text-xl font-semibold text-white">MAVI</h3>
            <p className="text-sm text-gray-400 mt-1">{agentIsSpeaking ? 'Speaking...' : isSpeaking ? 'Listening...' : 'Idle'}</p>
        </div>
    </div>
  );
}
