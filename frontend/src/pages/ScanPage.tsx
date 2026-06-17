import { useState, useRef } from "react";
import { aiApi } from "../services/api";
import { Navbar } from "../components/shared/Navbar";

export function ScanPage() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [extractedText, setExtractedText] = useState("");
  const [explanation, setExplanation] = useState("");
  const [loading, setLoading] = useState(false);
  const [explainAlso, setExplainAlso] = useState(true);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Please select an image file (jpg, png, webp).");
      return;
    }
    setError("");
    setImageFile(file);
    setExtractedText("");
    setExplanation("");
    // Generate preview
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleScan = async () => {
    if (!imageFile) return;
    setLoading(true);
    setError("");
    setExtractedText("");
    setExplanation("");
    try {
      const res = await aiApi.ocr(imageFile, explainAlso);
      setExtractedText(res.data.extracted_text || "No text found in image.");
      if (res.data.explanation) setExplanation(res.data.explanation);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to extract text. Try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setImageFile(null);
    setPreview(null);
    setExtractedText("");
    setExplanation("");
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const copyText = () => {
    navigator.clipboard.writeText(extractedText);
  };

  return (
    <div className="page">
      <Navbar />
      <div className="page-content max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6 animate-slide-up">
          <h1 className="text-2xl font-semibold text-slate-100">
            📷 Scan &amp; Solve
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Upload a photo of notes, a textbook page, or a problem — AI extracts the text and explains it
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Left — Upload */}
          <div className="space-y-4">
            {/* Drop zone */}
            <div
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => fileInputRef.current?.click()}
              className="card-hover border-2 border-dashed border-navy-600 hover:border-brand-500/50
                         flex flex-col items-center justify-center py-10 cursor-pointer min-h-[260px]"
            >
              {preview ? (
                <img src={preview} alt="preview" className="max-h-[220px] rounded-lg object-contain" />
              ) : (
                <div className="text-center space-y-3">
                  <div className="w-16 h-16 rounded-2xl bg-navy-800 border-2 border-dashed
                                  border-navy-600 mx-auto flex items-center justify-center">
                    <span className="text-3xl">🖼️</span>
                  </div>
                  <div>
                    <p className="text-sm text-slate-300 font-medium">Drop an image here</p>
                    <p className="text-xs text-slate-500 mt-1">or click to browse — JPG, PNG, WebP</p>
                  </div>
                </div>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              className="hidden"
            />

            {/* Explain toggle */}
            <label className="flex items-center gap-3 cursor-pointer card py-3">
              <input
                type="checkbox"
                checked={explainAlso}
                onChange={(e) => setExplainAlso(e.target.checked)}
                className="w-4 h-4 accent-brand-500"
              />
              <div>
                <p className="text-sm text-slate-200 font-medium">Also explain / solve it</p>
                <p className="text-xs text-slate-500">AICA will explain the extracted content</p>
              </div>
            </label>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={handleScan}
                disabled={!imageFile || loading}
                className="btn-primary flex-1"
              >
                {loading ? "Scanning..." : "✨ Extract Text"}
              </button>
              {imageFile && (
                <button onClick={handleReset} className="btn-secondary">
                  Reset
                </button>
              )}
            </div>
          </div>

          {/* Right — Results */}
          <div className="space-y-4">
            {/* Extracted text */}
            <div className="card min-h-[200px]">
              <div className="flex items-center justify-between mb-3">
                <p className="section-title mb-0">Extracted Text</p>
                {extractedText && (
                  <button onClick={copyText} className="btn-ghost text-xs py-1">
                    📋 Copy
                  </button>
                )}
              </div>
              {loading ? (
                <div className="space-y-2 animate-pulse">
                  <div className="h-3 bg-navy-700 rounded w-full" />
                  <div className="h-3 bg-navy-700 rounded w-5/6" />
                  <div className="h-3 bg-navy-700 rounded w-4/6" />
                </div>
              ) : extractedText ? (
                <pre className="text-sm text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
                  {extractedText}
                </pre>
              ) : (
                <p className="text-sm text-slate-500">
                  Extracted text will appear here after scanning.
                </p>
              )}
            </div>

            {/* AI Explanation */}
            {(explanation || (loading && explainAlso)) && (
              <div className="card border-brand-500/20">
                <p className="section-title flex items-center gap-2">
                  🤖 AICA Explains
                </p>
                {loading ? (
                  <div className="space-y-2 animate-pulse">
                    <div className="h-3 bg-navy-700 rounded w-full" />
                    <div className="h-3 bg-navy-700 rounded w-3/4" />
                  </div>
                ) : (
                  <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
                    {explanation}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}