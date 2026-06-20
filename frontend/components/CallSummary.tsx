"use client";

import React from 'react';
import { CheckCircle2, Calendar, Clock, Phone, FileText } from 'lucide-react';

interface CallSummaryProps {
  summary: {
    summary_text: string;
    appointments: any[];
    preferences?: string;
    timestamp: string;
    cost_breakdown?: any;
  };
}

export default function CallSummary({ summary }: CallSummaryProps) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-2xl max-w-2xl w-full mx-auto text-white mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center gap-3 mb-6 border-b border-gray-800 pb-4">
        <CheckCircle2 className="text-green-500 w-8 h-8" />
        <h2 className="text-2xl font-bold">Call Summary</h2>
      </div>

      <div className="space-y-6">
        <div className="bg-gray-800/50 rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-300 flex items-center gap-2 mb-2">
            <FileText className="w-5 h-5 text-blue-400" />
            Conversation Details
          </h3>
          <p className="text-gray-100 leading-relaxed">{summary.summary_text}</p>
        </div>

        {summary.appointments && summary.appointments.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-4">
             <h3 className="text-lg font-medium text-gray-300 flex items-center gap-2 mb-3">
              <Calendar className="w-5 h-5 text-purple-400" />
              Appointments
            </h3>
            <div className="space-y-3">
              {summary.appointments.map((apt, idx) => (
                <div key={idx} className="flex items-center justify-between bg-gray-800 p-3 rounded-md border border-gray-700">
                  <div className="flex items-center gap-3">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span className="font-medium">{apt.date} at {apt.time}</span>
                  </div>
                  <span className="px-3 py-1 bg-green-500/10 text-green-400 text-sm rounded-full font-medium">
                    {apt.status || 'Confirmed'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-between items-center text-sm text-gray-500 border-t border-gray-800 pt-4 mt-6">
           <span className="flex items-center gap-2">
             <Phone className="w-4 h-4" /> Ended at {new Date(summary.timestamp).toLocaleTimeString()}
           </span>
           {summary.cost_breakdown && (
             <span>
               Estimated Cost: <span className="font-medium text-gray-400">{summary.cost_breakdown.llm_tokens} tokens</span>
             </span>
           )}
        </div>
      </div>
    </div>
  );
}
