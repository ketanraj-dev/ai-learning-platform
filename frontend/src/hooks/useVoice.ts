/**
 * useVoice — microphone recording + browser TTS playback.
 * Records audio via MediaRecorder, sends to Whisper, speaks response.
 */
import { useState, useRef, useCallback } from "react";
import { aiApi } from "../services/api";

export function useVoice() {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks.current = [];
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      recorder.ondataavailable = (e) => chunks.current.push(e.data);
      recorder.start();
      mediaRecorder.current = recorder;
      setIsRecording(true);
    } catch {
      setError("Microphone access denied.");
    }
  }, []);

  const stopRecording = useCallback((): Promise<Blob> => {
    return new Promise((resolve) => {
      if (!mediaRecorder.current) return;
      mediaRecorder.current.onstop = () => {
        const blob = new Blob(chunks.current, { type: "audio/webm" });
        mediaRecorder.current?.stream.getTracks().forEach((t) => t.stop());
        resolve(blob);
      };
      mediaRecorder.current.stop();
      setIsRecording(false);
    });
  }, []);

  const transcribe = useCallback(async (): Promise<string> => {
    setIsTranscribing(true);
    try {
      const audioBlob = await stopRecording();
      const res = await aiApi.transcribe(audioBlob);
      return res.data.text || "";
    } catch {
      setError("Transcription failed. Please try again.");
      return "";
    } finally {
      setIsTranscribing(false);
    }
  }, [stopRecording]);

  const speak = useCallback((text: string) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, []);

  const stopSpeaking = useCallback(() => {
    window.speechSynthesis?.cancel();
    setIsSpeaking(false);
  }, []);

  return {
    isRecording, isTranscribing, isSpeaking, error,
    startRecording, stopRecording, transcribe, speak, stopSpeaking,
  };
}