import { useState, useRef, useEffect } from "react";
import { aiApi } from "../../services/api";
import { useVoice } from "../../hooks/useVoice";
import type { ChatMessage } from "../../types/index";

function MicIcon({ recording }: { recording: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="5" y="1" width="6" height="9" rx="3"
        fill={recording ? "#EF4444" : "none"}
        stroke={recording ? "#EF4444" : "#6B7280"} strokeWidth="1.5" />
      <path d="M2.5 8a5.5 5.5 0 0011 0" stroke={recording ? "#EF4444" : "#6B7280"}
        strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="8" y1="13.5" x2="8" y2="15.5"
        stroke={recording ? "#EF4444" : "#6B7280"} strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M14 8L2 2l3.5 6L2 14l12-6z" fill="white"/>
    </svg>
  );
}

export function AIChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hi, I'm AICA — your AI tutor. Ask me anything about Data Science and AI/ML." },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const { isRecording, isTranscribing, isSpeaking, startRecording, transcribe, speak, stopSpeaking } = useVoice();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;
    const userMsg: ChatMessage = { role: "user", content: text };
    const history = messages.slice(-10);
    setMessages((prev) => [...prev, userMsg, { role: "assistant", content: "" }]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await aiApi.chatStream(text, history);
      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        fullText += decoder.decode(value, { stream: true });
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: "assistant", content: fullText };
          return updated;
        });
      }
      if (fullText) speak(fullText.slice(0, 500));
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Something went wrong. Please try again.",
        };
        return updated;
      });
    } finally { setIsLoading(false); }
  };

  const handleVoice = async () => {
    if (isRecording) {
      const text = await transcribe();
      if (text) sendMessage(text);
    } else { startRecording(); }
  };

  return (
    <div className="flex flex-col h-full bg-navy-950 rounded-2xl border border-navy-700 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-navy-700 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-brand-500/15 border border-brand-500/25
                          flex items-center justify-center">
            <div className="w-2.5 h-2.5 rounded-full bg-brand-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-200"
               style={{ fontFamily: "Space Grotesk, sans-serif" }}>AICA</p>
            <p className="text-[10px] text-slate-500">AI Course Assistant</p>
          </div>
        </div>
        {isSpeaking && (
          <button onClick={stopSpeaking}
            className="text-xs text-brand-400 hover:text-brand-300 transition-colors">
            Stop
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[88%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed
              ${msg.role === "user"
                ? "bg-brand-500 text-white rounded-br-sm"
                : "bg-navy-800 text-slate-200 border border-navy-700 rounded-bl-sm"
              }`}>
              {msg.content || (isLoading && i === messages.length - 1 ? (
                <span className="flex gap-1 items-center h-4">
                  {[0, 150, 300].map((delay) => (
                    <span key={delay} className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce"
                      style={{ animationDelay: `${delay}ms` }} />
                  ))}
                </span>
              ) : "")}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-navy-700">
        {isTranscribing && (
          <p className="text-xs text-brand-400 mb-2 text-center animate-pulse">
            Transcribing…
          </p>
        )}
        <div className="flex gap-2">
          <button onClick={handleVoice}
            className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0
                        transition-all border ${isRecording
              ? "bg-red-500/15 border-red-500/30 animate-pulse-slow"
              : "bg-navy-800 border-navy-700 hover:border-navy-600"}`}>
            <MicIcon recording={isRecording} />
          </button>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage(input)}
            placeholder="Ask about DS / AI-ML…"
            className="input text-sm py-2"
            disabled={isLoading || isRecording}
          />
          <button onClick={() => sendMessage(input)}
            disabled={isLoading || !input.trim()}
            className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0
                       bg-brand-500 hover:bg-brand-400 disabled:opacity-40
                       disabled:cursor-not-allowed transition-all">
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
}
