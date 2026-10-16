import React, { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, Sparkles, Mic, MicOff, Volume2 } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useSession } from "../context/SessionContext";
import { useVoiceInput, speakText } from "../hooks/useVoiceInput";
import api from "../utils/api";

const SUGGESTIONS = [
  "I'm feeling really tired today",
  "Give me a breathing exercise",
  "How do I reduce eye strain?",
  "Explain my fatigue score",
];

function Message({ msg, dark, onSpeak }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${isUser ? "bg-indigo-600" : "bg-emerald-600"}`}>
        {isUser ? <User size={14} className="text-white" /> : <Bot size={14} className="text-white" />}
      </div>
      <div className={`max-w-[78%] group relative px-4 py-3 rounded-2xl text-sm leading-relaxed
        ${isUser ? "bg-indigo-600 text-white rounded-tr-sm"
          : dark ? "bg-gray-800 text-gray-200 rounded-tl-sm"
          : "bg-white text-gray-800 border border-gray-200 rounded-tl-sm"}`}>
        <p className="whitespace-pre-wrap">{msg.content}</p>
        <div className={`flex items-center gap-2 mt-1.5 ${isUser ? "justify-end" : "justify-start"}`}>
          <span className={`text-xs ${isUser ? "text-indigo-200" : "text-gray-400"}`}>
            {new Date(msg.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
          {!isUser && (
            <button onClick={() => onSpeak(msg.content)}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded text-gray-400 hover:text-emerald-400">
              <Volume2 size={12} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function TypingIndicator({ dark }) {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center shrink-0">
        <Bot size={14} className="text-white" />
      </div>
      <div className={`px-4 py-3 rounded-2xl rounded-tl-sm ${dark ? "bg-gray-800" : "bg-white border border-gray-200"}`}>
        <div className="flex gap-1 items-center h-4">
          {[0, 1, 2].map(i => (
            <span key={i} className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ChatbotPage() {
  const { dark } = useTheme();
  const { fatigueScore, state } = useSession();
  const [messages, setMessages] = useState([{
    role: "assistant",
    content: "Hi! I'm Mentora, your AI wellness coach 🧠\n\nI can see your real-time fatigue data and provide personalised guidance. Tap the mic to speak, or type below. How are you feeling today?",
    ts: Date.now()
  }]);
  const [input, setInput]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [ttsEnabled, setTts]    = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const handleVoiceResult = useCallback((text) => setInput(text), []);
  const { listening, supported, transcript, toggle: toggleVoice } = useVoiceInput(handleVoiceResult);
  useEffect(() => { if (transcript) setInput(transcript); }, [transcript]);

  const send = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    const userMsg = { role: "user", content: msg, ts: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    try {
      const history = messages.slice(-10).map(m => ({ role: m.role, content: m.content }));
      const res = await api.post("/api/v1/chatbot", { message: msg, fatigue_score: fatigueScore, state, history });
      const reply = res.data.reply;
      setMessages(prev => [...prev, { role: "assistant", content: reply, ts: Date.now() }]);
      if (ttsEnabled) speakText(reply);
    } catch {
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I'm having trouble connecting. Please try again.", ts: Date.now() }]);
    } finally { setLoading(false); }
  };

  return (
    <div className={`flex flex-col ${dark ? "text-white" : "text-gray-900"}`} style={{ height: "calc(100vh - 69px)" }}>
      <div className={`px-5 py-4 border-b ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shrink-0`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-600 flex items-center justify-center"><Bot size={18} className="text-white" /></div>
            <div>
              <h2 className="font-bold text-sm">Mentora Wellness Coach</h2>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs text-gray-400">AI-powered · Voice enabled</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {fatigueScore > 0 && (
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${dark ? "bg-gray-800 border-gray-700 text-gray-300" : "bg-gray-100 border-gray-200 text-gray-600"}`}>
                <Sparkles size={11} className="text-indigo-400" />{fatigueScore}/100 · {state}
              </div>
            )}
            <button onClick={() => setTts(t => !t)} title={ttsEnabled ? "Mute" : "Speak responses"}
              className={`p-2 rounded-lg transition-colors ${ttsEnabled ? "bg-emerald-600 text-white" : dark ? "hover:bg-gray-800 text-gray-400" : "hover:bg-gray-100 text-gray-500"}`}>
              <Volume2 size={16} />
            </button>
          </div>
        </div>
      </div>

      <div className={`flex-1 overflow-y-auto p-4 md:p-5 space-y-4 ${dark ? "bg-gray-950" : "bg-gray-50"}`}>
        {messages.map((msg, i) => <Message key={i} msg={msg} dark={dark} onSpeak={speakText} />)}
        {loading && <TypingIndicator dark={dark} />}
        <div ref={bottomRef} />
      </div>

      <div className={`px-4 py-2.5 flex gap-2 overflow-x-auto shrink-0 border-t ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-100"}`}>
        {SUGGESTIONS.map(s => (
          <button key={s} onClick={() => send(s)} disabled={loading}
            className={`shrink-0 text-xs px-3 py-1.5 rounded-full border transition-colors whitespace-nowrap ${dark ? "border-gray-700 text-gray-300 hover:bg-gray-800" : "border-gray-200 text-gray-600 hover:bg-gray-100"}`}>{s}</button>
        ))}
      </div>

      <div className={`px-4 py-3 border-t shrink-0 ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"}`}>
        <div className={`flex items-end gap-2 px-4 py-2.5 rounded-2xl border transition-colors ${listening ? "border-red-500 bg-red-500/5" : dark ? "bg-gray-800 border-gray-700 focus-within:border-indigo-500" : "bg-gray-50 border-gray-200 focus-within:border-indigo-400"}`}>
          <textarea rows={1} value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();}}}
            placeholder={listening ? "Listening…" : "Ask anything about your well-being…"}
            className={`flex-1 resize-none text-sm bg-transparent outline-none max-h-28 leading-relaxed ${dark ? "text-white placeholder-gray-500" : "text-gray-800 placeholder-gray-400"}`}
          />
          {supported && (
            <button onClick={toggleVoice} title={listening ? "Stop" : "Speak to Mentora"}
              className={`p-1.5 rounded-xl transition-colors shrink-0 ${listening ? "bg-red-600 hover:bg-red-700 animate-pulse" : dark ? "hover:bg-gray-700 text-gray-400" : "hover:bg-gray-200 text-gray-500"}`}>
              {listening ? <MicOff size={15} className="text-white" /> : <Mic size={15} />}
            </button>
          )}
          <button onClick={() => send()} disabled={!input.trim() || loading}
            className="p-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 transition-colors shrink-0">
            <Send size={15} className="text-white" />
          </button>
        </div>
        {listening && <p className="text-xs text-red-400 mt-1.5 px-1 animate-pulse">🎙 Recording… speak now</p>}
      </div>
    </div>
  );
}

