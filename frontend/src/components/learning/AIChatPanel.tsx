import { useState, useRef, useEffect } from "react";
import { aiApi } from "../../services/api";
import { useVoice } from "../../hooks/useVoice";
import type { ChatMessage } from "../../types/index";

export function AIChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hi! I'm AICA, your AI tutor. Ask me anything about Data Science and AI/ML! 🤖" },
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
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    // Add empty assistant message to stream into
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const response = await aiApi.chatStream(text, history);
      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: "assistant", content: fullText };
          return updated;
        });
      }
      // Auto-speak the response
      if (fullText) speak(fullText.slice(0, 500));
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
        };
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoice = async () => {
    if (isRecording) {
      const text = await transcribe();
      if (text) sendMessage(text);
    } else {
      startRecording();
    }
  };

  return (
    <div className="flex flex-col h-full bg-navy-900 rounded-2xl border border-navy-700 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-navy-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-brand-500/20 flex items-center justify-center">
            <span className="text-sm">🤖</span>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-200">AICA</p>
            <p className="text-xs text-slate-500">AI Course Assistant</p>
          </div>
        </div>
        {isSpeaking && (
          <button onClick={stopSpeaking} className="text-xs text-brand-400 hover:text-brand-300">
            ⏹ Stop
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed
              ${msg.role === "user"
                ? "bg-brand-500 text-white rounded-br-sm"
                : "bg-navy-800 text-slate-200 border border-navy-700 rounded-bl-sm"
              }`}>
              {msg.content || (isLoading && i === messages.length - 1 ? (
                <span className="flex gap-1 items-center h-4">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "300ms" }} />
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
            Transcribing your voice...
          </p>
        )}
        <div className="flex gap-2">
          <button
            onClick={handleVoice}
            className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0
              transition-all border ${isRecording
                ? "bg-red-500/20 border-red-500/40 text-red-400 animate-pulse-slow"
                : "bg-navy-800 border-navy-700 text-slate-400 hover:text-slate-200"
              }`}
          >
            {isRecording ? "⏹" : "🎙"}
          </button>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage(input)}
            placeholder="Ask about DS / AI-ML..."
            className="input text-sm py-2"
            disabled={isLoading || isRecording}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={isLoading || !input.trim()}
            className="btn-primary px-3 text-sm flex-shrink-0"
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  );
}