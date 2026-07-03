import { useState, useRef } from "react";
import { aiApi } from "../services/api";
import { Navbar } from "../components/shared/Navbar";

function UploadIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M10 20l6-6 6 6" stroke="#2A3D57" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M16 14v10" stroke="#2A3D57" strokeWidth="2" strokeLinecap="round"/>
      <path d="M6 24v1a3 3 0 003 3h14a3 3 0 003-3v-1" stroke="#2A3D57" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );
}

export function ScanPage() {
  const [imageFile, setImageFile]     = useState<File | null>(null);
  const [preview, setPreview]         = useState<string | null>(null);
  const [extractedText, setExtractedText] = useState("");
  const [explanation, setExplanation] = useState("");
  const [loading, setLoading]         = useState(false);
  const [explainAlso, setExplainAlso] = useState(true);
  const [error, setError]             = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Please select an image file (JPG, PNG, WebP).");
      return;
    }
    setError(""); setImageFile(file); setExtractedText(""); setExplanation("");
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
    setLoading(true); setError(""); setExtractedText(""); setExplanation("");
    try {
      const res = await aiApi.ocr(imageFile, explainAlso);
      setExtractedText(res.data.extracted_text || "No text found in image.");
      if (res.data.explanation) setExplanation(res.data.explanation);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to extract text. Try again.");
    } finally { setLoading(false); }
  };

  const handleReset = () => {
    setImageFile(null); setPreview(null); setExtractedText("");
    setExplanation(""); setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="page">
      <Navbar />
      <div className="page-content max-w-4xl mx-auto">

        {/* Header */}
        <div className="mb-8 animate-slide-up">
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Scan &amp; solve</h1>
          <p className="text-slate-500 text-sm">
            Upload a photo of notes, a textbook page, or a problem — AI extracts and explains the content
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Left: upload */}
          <div className="space-y-4">
            <div
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => fileInputRef.current?.click()}
              className="bg-navy-800 border-2 border-dashed border-navy-700 hover:border-brand-500/40
                         rounded-2xl flex flex-col items-center justify-center py-10 cursor-pointer
                         transition-all duration-200 min-h-[260px] hover:bg-[#1A2840]"
            >
              {preview ? (
                <img src={preview} alt="preview"
                  className="max-h-[220px] rounded-xl object-contain" />
              ) : (
                <div className="text-center space-y-4">
                  <div className="w-16 h-16 rounded-2xl bg-navy-950 border border-navy-700
                                  mx-auto flex items-center justify-center">
                    <UploadIcon />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-300">Drop an image here</p>
                    <p className="text-xs text-slate-500 mt-1">or click to browse — JPG, PNG, WebP</p>
                  </div>
                </div>
              )}
            </div>

            <input ref={fileInputRef} type="file" accept="image/*"
              onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              className="hidden" />

            {/* Explain toggle */}
            <label className="flex items-center gap-3 cursor-pointer card py-3.5 hover:border-navy-600
                               transition-colors">
              <input type="checkbox" checked={explainAlso}
                onChange={(e) => setExplainAlso(e.target.checked)}
                className="w-4 h-4 accent-brand-500 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-slate-200">Also explain it</p>
                <p className="text-xs text-slate-500 mt-0.5">AICA will explain the extracted content</p>
              </div>
            </label>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3
                              text-red-400 text-sm">{error}</div>
            )}

            <div className="flex gap-2">
              <button onClick={handleScan} disabled={!imageFile || loading}
                className="btn-primary flex-1">
                {loading ? "Scanning…" : "Extract text"}
              </button>
              {imageFile && (
                <button onClick={handleReset} className="btn-secondary">Reset</button>
              )}
            </div>
          </div>

          {/* Right: results */}
          <div className="space-y-4">
            <div className="card min-h-[200px]">
              <div className="flex items-center justify-between mb-4">
                <p className="section-title mb-0">Extracted text</p>
                {extractedText && (
                  <button onClick={() => navigator.clipboard.writeText(extractedText)}
                    className="btn-ghost text-xs py-1">
                    Copy
                  </button>
                )}
              </div>
              {loading ? (
                <div className="space-y-2.5 animate-pulse">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-2.5 bg-navy-700 rounded"
                         style={{ width: `${85 - i * 10}%` }} />
                  ))}
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

            {(explanation || (loading && explainAlso)) && (
              <div className="card border-brand-500/20">
                <p className="section-title mb-3">AICA explains</p>
                {loading ? (
                  <div className="space-y-2.5 animate-pulse">
                    <div className="h-2.5 bg-navy-700 rounded w-full" />
                    <div className="h-2.5 bg-navy-700 rounded w-4/5" />
                    <div className="h-2.5 bg-navy-700 rounded w-3/5" />
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
