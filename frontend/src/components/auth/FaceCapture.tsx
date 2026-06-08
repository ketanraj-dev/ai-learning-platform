import { useEffect, useRef, useState, useCallback } from "react";
import { useWebcam } from "../../hooks/useWebcam";

interface Props {
  onCapture: (blob: Blob) => void;
  onClear: () => void;
  captured: boolean;
  label?: string;
}

export function FaceCapture({
  onCapture,
  onClear,
  captured,
  label = "Add Face Login",
}: Props) {
  // ── hooks must be declared first ──────────────────────────
  const { videoRef, isStreaming, error, startCamera, stopCamera, captureFrame } = useWebcam();
  const [cameraReady, setCameraReady] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Wait 2 seconds after camera opens before allowing capture
  useEffect(() => {
    if (isStreaming) {
      const timer = setTimeout(() => setCameraReady(true), 2000);
      return () => clearTimeout(timer);
    } else {
      setCameraReady(false);
    }
  }, [isStreaming]);

  // Stop camera on unmount
  useEffect(() => {
    return () => stopCamera();
  }, [stopCamera]);

  const handleCapture = useCallback(() => {
    const blob = captureFrame();
    if (!blob) return;
    // Draw snapshot to canvas for preview
    if (canvasRef.current && videoRef.current) {
      const ctx = canvasRef.current.getContext("2d");
      ctx?.drawImage(videoRef.current, 0, 0, 320, 240);
    }
    stopCamera();
    onCapture(blob);
  }, [captureFrame, videoRef, stopCamera, onCapture]);

  const handleClear = useCallback(() => {
    onClear();
    if (canvasRef.current) {
      canvasRef.current.getContext("2d")?.clearRect(0, 0, 320, 240);
    }
  }, [onClear]);

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-400">{label}</p>

      {/* Preview area */}
      <div className="relative w-full aspect-video bg-navy-900 rounded-xl overflow-hidden border border-navy-700 flex items-center justify-center">
        {/* Live stream */}
        <video
          ref={videoRef}
          className={`w-full h-full object-cover ${isStreaming ? "block" : "hidden"}`}
          muted
          playsInline
        />

        {/* Captured snapshot */}
        <canvas
          ref={canvasRef}
          width={320}
          height={240}
          className={`w-full h-full object-cover ${captured && !isStreaming ? "block" : "hidden"}`}
        />

        {/* Idle state */}
        {!isStreaming && !captured && (
          <div className="text-center space-y-2 p-6">
            <div className="w-16 h-16 rounded-full bg-navy-800 border-2 border-dashed border-navy-600 mx-auto flex items-center justify-center">
              <span className="text-2xl">📷</span>
            </div>
            <p className="text-sm text-slate-500">Camera off</p>
          </div>
        )}

        {/* Scanning overlay */}
        {isStreaming && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute inset-4 border-2 border-brand-500/50 rounded-lg" />
            <div className="absolute top-4 left-4 w-6 h-6 border-t-2 border-l-2 border-brand-400 rounded-tl" />
            <div className="absolute top-4 right-4 w-6 h-6 border-t-2 border-r-2 border-brand-400 rounded-tr" />
            <div className="absolute bottom-4 left-4 w-6 h-6 border-b-2 border-l-2 border-brand-400 rounded-bl" />
            <div className="absolute bottom-4 right-4 w-6 h-6 border-b-2 border-r-2 border-brand-400 rounded-br" />
            {/* Warmup indicator */}
            {!cameraReady && (
              <div className="absolute bottom-2 left-0 right-0 text-center">
                <span className="text-xs text-brand-400 bg-navy-900/80 px-2 py-1 rounded-full">
                  Initializing camera...
                </span>
              </div>
            )}
          </div>
        )}

        {/* Captured badge */}
        {captured && !isStreaming && (
          <div className="absolute top-2 right-2 bg-success/90 text-white text-xs px-2 py-1 rounded-full font-medium">
            ✓ Captured
          </div>
        )}
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {/* Controls */}
      <div className="flex gap-2">
        {!isStreaming && !captured && (
          <button type="button" onClick={startCamera} className="btn-secondary text-sm flex-1">
            📷 Open Camera
          </button>
        )}

        {isStreaming && (
          <>
            <button
              type="button"
              onClick={handleCapture}
              disabled={!cameraReady}
              className="btn-primary text-sm flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cameraReady ? "✓ Capture" : "⏳ Camera warming up..."}
            </button>
            <button type="button" onClick={stopCamera} className="btn-secondary text-sm">
              Cancel
            </button>
          </>
        )}

        {captured && (
          <button type="button" onClick={handleClear} className="btn-secondary text-sm flex-1">
            Retake Photo
          </button>
        )}
      </div>
    </div>
  );
}