-- Supabase Schema for Mykare Voice AI Agent

CREATE TABLE IF NOT EXISTS users (
    phone_number TEXT PRIMARY KEY,
    name TEXT,
    preferences TEXT
);

CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_phone TEXT REFERENCES users(phone_number),
    date TEXT,
    time TEXT,
    status TEXT DEFAULT 'scheduled'
);

CREATE TABLE IF NOT EXISTS call_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_phone TEXT REFERENCES users(phone_number),
    intent TEXT,
    summary_text TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cost_breakdown JSONB
);
