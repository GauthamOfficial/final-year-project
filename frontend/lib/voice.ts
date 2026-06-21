"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const LANG_MAP: Record<string, string> = {
  en: "en-US",
  si: "si-LK",
  ta: "ta-IN",
};

/** Minimal Web Speech API surface for TypeScript without dom-speech types. */
type RecognitionResultChunk = { transcript: string };

type RecognitionEventLike = {
  resultIndex?: number;
  results: ArrayLike<{ 0?: RecognitionResultChunk; isFinal?: boolean }>;
};

type RecognitionErrorEventLike = {
  error?: string;
  message?: string;
};

export type VoiceRecognitionImpl = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((ev: RecognitionEventLike) => void) | null;
  onend: (() => void) | null;
  onerror: ((ev: RecognitionErrorEventLike) => void) | null;
};

type VoiceRecognitionConstructor = new () => VoiceRecognitionImpl;
export type VoiceRecognitionErrorCode =
  | "not-allowed"
  | "no-speech"
  | "audio-capture"
  | "network"
  | "language-not-supported"
  | "aborted"
  | "unknown";

declare global {
  interface Window {
    webkitSpeechRecognition?: VoiceRecognitionConstructor;
    SpeechRecognition?: VoiceRecognitionConstructor;
  }
}

function getRecognitionCtor(): VoiceRecognitionConstructor | null {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export function useSpeechRecognition({
  lang,
  onResult,
  onError,
}: {
  lang: string;
  onResult: (text: string) => void;
  onError?: (message: string, code: VoiceRecognitionErrorCode) => void;
}) {
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const recogRef = useRef<VoiceRecognitionImpl | null>(null);
  const networkRetryRef = useRef(false);

  useEffect(() => {
    setSupported(!!getRecognitionCtor());
  }, []);

  const start = useCallback(async () => {
    const Ctor = getRecognitionCtor();
    if (!Ctor) {
      onError?.("Voice input is not supported in this browser.", "unknown");
      return;
    }
    if (typeof window !== "undefined" && window.isSecureContext === false) {
      onError?.("Voice input requires a secure context (https or localhost).", "unknown");
      return;
    }
    if (typeof navigator !== "undefined" && navigator.mediaDevices?.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach((track) => track.stop());
      } catch {
        onError?.("Microphone permission was denied.", "not-allowed");
        return;
      }
    }
    const r = new Ctor();
    r.lang = lang;
    // Single-utterance mode is more stable across browsers than continuous/interim mode.
    r.continuous = false;
    r.interimResults = false;
    r.onresult = (e: RecognitionEventLike) => {
      const startAt = e.resultIndex ?? 0;
      const finalTranscript: string[] = [];
      for (let i = startAt; i < e.results.length; i += 1) {
        const result = e.results[i];
        if (result?.isFinal) {
          const text = (result[0]?.transcript ?? "").trim();
          if (text) finalTranscript.push(text);
        }
      }
      const transcript = finalTranscript.join(" ").trim();
      if (transcript) onResult(transcript);
    };
    r.onend = () => {
      setListening(false);
      recogRef.current = null;
    };
    r.onerror = (ev: RecognitionErrorEventLike) => {
      setListening(false);
      const errorCode = ev?.error;
      if (errorCode === "network" && !networkRetryRef.current) {
        networkRetryRef.current = true;
        window.setTimeout(() => {
          try {
            r.start();
            setListening(true);
          } catch {
            onError?.("Network issue while processing voice input.", "network");
          }
        }, 450);
        return;
      }
      networkRetryRef.current = false;
      const code: VoiceRecognitionErrorCode =
        errorCode === "not-allowed" ||
        errorCode === "no-speech" ||
        errorCode === "audio-capture" ||
        errorCode === "network" ||
        errorCode === "language-not-supported" ||
        errorCode === "aborted"
          ? errorCode
          : "unknown";
      const mapped =
        code === "not-allowed"
          ? "Microphone permission was denied."
          : code === "no-speech"
            ? "No speech detected. Please try again."
            : code === "audio-capture"
              ? "No microphone was found on this device."
              : code === "language-not-supported"
                ? "Selected language is not supported for voice input in this browser."
                : code === "network"
                  ? "Network issue while processing voice input."
                  : ev?.message || "Voice input failed. Please try again.";
      onError?.(mapped, code);
    };
    recogRef.current = r;
    networkRetryRef.current = false;
    setListening(true);
    try {
      r.start();
    } catch {
      setListening(false);
      onError?.("Voice input could not be started.", "unknown");
    }
  }, [lang, onResult, onError]);

  const stop = useCallback(() => {
    recogRef.current?.stop();
    setListening(false);
  }, []);

  const toggle = useCallback(() => {
    if (listening) stop();
    else {
      void start();
    }
  }, [listening, start, stop]);

  return { supported, listening, start, stop, toggle };
}

export function useSpeechSynthesis() {
  const speak = useCallback((text: string, language: "en" | "si" | "ta") => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    try {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = LANG_MAP[language] ?? "en-US";
      utter.rate = 1.0;
      utter.pitch = 1.0;
      window.speechSynthesis.speak(utter);
    } catch {
      // ignore
    }
  }, []);

  const cancel = useCallback(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
  }, []);

  return { speak, cancel };
}
