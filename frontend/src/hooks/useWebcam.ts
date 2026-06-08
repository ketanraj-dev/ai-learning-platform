import { useRef, useState, useCallback } from "react";

export function useWebcam() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startCamera = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setIsStreaming(true);
      }
    } catch {
      setError("Camera access denied. Please allow camera permissions.");
      setIsStreaming(false);
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach((t) => t.stop());
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
  }, []);

  const captureFrame = useCallback((): Blob | null => {
    if (!videoRef.current || !isStreaming) return null;

    const width = videoRef.current.videoWidth;
    const height = videoRef.current.videoHeight;

    if (width === 0 || height === 0) {
      setError("Camera not ready. Please wait a moment and try again.");
      return null;
    }

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.drawImage(videoRef.current, 0, 0, width, height);

    // Check if frame is black (camera not ready)
    const imageData = ctx.getImageData(0, 0, 20, 20);
    let totalBrightness = 0;
    for (let i = 0; i < imageData.data.length; i += 4) {
      totalBrightness += imageData.data[i] + imageData.data[i+1] + imageData.data[i+2];
    }
    const avgBrightness = totalBrightness / (imageData.data.length / 4 * 3);

    if (avgBrightness < 5) {
      setError("Image too dark. Please ensure good lighting and try again.");
      return null;
    }

    const dataURL = canvas.toDataURL("image/jpeg", 0.92);
    const binary = atob(dataURL.split(",")[1]);
    const array = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) array[i] = binary.charCodeAt(i);
    return new Blob([array], { type: "image/jpeg" });
  }, [isStreaming]);

  return { videoRef, isStreaming, error, startCamera, stopCamera, captureFrame };
}