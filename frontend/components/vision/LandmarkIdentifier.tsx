"use client";

import Link from "next/link";
import { useCallback, useRef, useState } from "react";
import { AlertTriangle, ImagePlus } from "lucide-react";
import { api, toApiError } from "@/lib/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const MAX_BYTES = 10 * 1024 * 1024;
const ALLOWED = new Set(["image/jpeg", "image/jpg", "image/png", "image/webp"]);

export type VisionIdentifyResponse = {
  identified: boolean;
  landmark_name?: string | null;
  district?: string | null;
  confidence?: string;
  reason?: string;
  attraction_slug?: string | null;
  attraction_id?: number | null;
  ai_summary?: string | null;
  sources?: Array<Record<string, unknown>> | null;
  error?: string;
};

function validateFile(file: File): string | null {
  if (file.size > MAX_BYTES) {
    return "File too large. Maximum size is 10MB.";
  }
  const t = file.type.toLowerCase();
  if (!ALLOWED.has(t)) {
    return "Invalid file type. Please upload JPG, PNG, or WEBP.";
  }
  return null;
}

export function LandmarkIdentifier({ className }: { className?: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [clientErr, setClientErr] = useState<string | null>(null);
  const [result, setResult] = useState<VisionIdentifyResponse | null>(null);

  const reset = useCallback(() => {
    setFile(null);
    setPreviewUrl((u) => {
      if (u) URL.revokeObjectURL(u);
      return null;
    });
    setResult(null);
    setClientErr(null);
    setLoading(false);
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  const pickFile = useCallback(
    (f: File | null) => {
      setClientErr(null);
      setResult(null);
      if (!f) return;
      const err = validateFile(f);
      if (err) {
        setClientErr(err);
        return;
      }
      setPreviewUrl((old) => {
        if (old) URL.revokeObjectURL(old);
        return URL.createObjectURL(f);
      });
      setFile(f);
    },
    []
  );

  const onIdentify = async () => {
    if (!file) return;
    setLoading(true);
    setClientErr(null);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("image", file);
      const { data } = await api.post<VisionIdentifyResponse>(
        "/api/v1/vision/identify/",
        fd
      );
      setResult(data);
    } catch (e) {
      setClientErr(toApiError(e).message);
    } finally {
      setLoading(false);
    }
  };

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files?.[0];
      if (f) pickFile(f);
    },
    [pickFile]
  );

  return (
    <div className={cn("mx-auto w-full max-w-lg space-y-6", className)}>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/jpg,image/png,image/webp"
        className="hidden"
        onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
      />

      {!result && !loading && (
        <>
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            className={cn(
              "flex min-h-[200px] w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors",
              dragOver
                ? "border-jade-500 bg-jade-50/50"
                : "border-muted-foreground/25 bg-muted/30 hover:border-jade-400/50 hover:bg-muted/40"
            )}
          >
            <ImagePlus className="mb-3 h-10 w-10 text-muted-foreground" />
            <p className="text-base font-medium text-foreground">
              Upload a photo of a Sri Lanka landmark
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              JPG, PNG or WEBP, max 10MB
            </p>
            <span className="mt-4 text-xs text-muted-foreground">
              Drag and drop or click to choose
            </span>
          </button>

          {previewUrl && file && (
            <div className="space-y-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={previewUrl}
                alt="Selected landmark preview"
                className="max-h-64 w-full rounded-xl object-contain"
              />
            </div>
          )}

          {clientErr && (
            <Alert variant="danger">
              <AlertTitle>Something went wrong</AlertTitle>
              <AlertDescription>{clientErr}</AlertDescription>
            </Alert>
          )}

          <Button
            className="w-full"
            disabled={!file}
            onClick={onIdentify}
          >
            Identify Landmark
          </Button>
        </>
      )}

      {loading && (
        <div className="space-y-4">
          <Skeleton className="h-48 w-full rounded-xl" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
          <p className="text-center text-sm text-muted-foreground">
            Analyzing image…
          </p>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-6">
          {result.error && (
            <Alert variant="danger">
              <AlertTitle>Processing error</AlertTitle>
              <AlertDescription>{result.error}</AlertDescription>
            </Alert>
          )}

          {result.identified ? (
            <div className="space-y-4">
              {result.confidence === "high" ? (
                <Badge className="bg-emerald-600 hover:bg-emerald-600">
                  Confidence: high
                </Badge>
              ) : result.confidence === "medium" ? (
                <Badge className="bg-amber-500 text-amber-950 hover:bg-amber-500">
                  Confidence: medium
                </Badge>
              ) : (
                <Badge variant="secondary">Confidence: low</Badge>
              )}

              <h2 className="text-2xl font-semibold tracking-tight text-foreground">
                {result.landmark_name ?? "Unknown landmark"}
              </h2>

              {result.district ? (
                <p className="text-sm text-muted-foreground">
                  Located in {result.district} district
                </p>
              ) : null}

              {result.reason ? (
                <p className="text-sm italic text-muted-foreground">
                  {result.reason}
                </p>
              ) : null}

              <hr className="border-border" />

              {result.ai_summary ? (
                <div className="space-y-2">
                  <h3 className="text-sm font-semibold text-foreground">
                    About this landmark
                  </h3>
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">
                    {result.ai_summary}
                  </p>
                </div>
              ) : null}

              {Array.isArray(result.sources) && result.sources.length > 0 ? (
                <div className="space-y-2 rounded-xl border border-border bg-muted/20 px-4 py-3">
                  <h3 className="text-sm font-semibold text-foreground">
                    Sources
                  </h3>
                  <ul className="space-y-1.5 text-xs text-muted-foreground">
                    {result.sources.map((s, i) => {
                      const title =
                        typeof s.title === "string"
                          ? s.title
                          : typeof s.doc_id === "string"
                            ? s.doc_id
                            : `Reference ${i + 1}`;
                      const rel = s.relevance;
                      return (
                        <li key={i} className="leading-snug">
                          <span className="text-foreground/80">{title}</span>
                          {typeof rel === "number" ? (
                            <span className="ml-1 text-muted-foreground">
                              (score {rel.toFixed(2)})
                            </span>
                          ) : null}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ) : null}

              {result.attraction_slug ? (
                <Link
                  href={`/explore/${result.attraction_slug}`}
                  className={cn(
                    buttonVariants(),
                    "inline-flex w-full sm:w-auto"
                  )}
                >
                  View full attraction page →
                </Link>
              ) : null}
            </div>
          ) : !result.error ? (
            <Alert variant="warning">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Landmark not recognized</AlertTitle>
              <AlertDescription>
                This image could not be identified as a Sri Lanka landmark. Try a
                clearer photo or search manually.
              </AlertDescription>
            </Alert>
          ) : null}

          <Button variant="outline" className="w-full" onClick={reset}>
            Try another photo
          </Button>
        </div>
      )}
    </div>
  );
}
