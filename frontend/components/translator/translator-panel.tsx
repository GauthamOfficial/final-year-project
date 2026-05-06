"use client";

import { useCallback, useState } from "react";
import { ArrowRightLeft, Languages, Loader2, Mic, MicOff, Volume2 } from "lucide-react";
import { api, toApiError } from "@/lib/api";
import {
  useSpeechRecognition,
  useSpeechSynthesis,
  type VoiceRecognitionErrorCode,
} from "@/lib/voice";
import { cn } from "@/lib/utils";

type Lang = "en" | "si" | "ta";

const LANGS: { id: Lang; label: string }[] = [
  { id: "en", label: "English" },
  { id: "si", label: "සිංහල (Sinhala)" },
  { id: "ta", label: "தமிழ் (Tamil)" },
];

export function TranslatorPanel() {
  const [source, setSource] = useState<Lang>("en");
  const [target, setTarget] = useState<Lang>("si");
  const [input, setInput] = useState("");
  const [output, setOutput] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [voiceErr, setVoiceErr] = useState<string | null>(null);
  const [voiceMode, setVoiceMode] = useState(true);
  const speech = useSpeechSynthesis();

  const translate = useCallback(async (text: string) => {
    if (!text.trim()) return;
    setBusy(true);
    setErr(null);
    setOutput("");
    try {
      const { data } = await api.post("/api/v1/translate/", {
        text,
        source,
        target,
      });
      const translated = data?.translation ?? "";
      setOutput(translated);
      if (voiceMode && translated) {
        speech.speak(translated, target);
      }
    } catch (e) {
      setErr(toApiError(e).message || "Translation failed.");
    } finally {
      setBusy(false);
    }
  }, [source, target, voiceMode, speech]);

  const recog = useSpeechRecognition({
    lang: source === "si" ? "si-LK" : source === "ta" ? "ta-IN" : "en-US",
    onResult: (text) => {
      setInput(text);
      void translate(text);
    },
    onError: (message, code: VoiceRecognitionErrorCode) => {
      if (code === "network") {
        setVoiceErr("Temporary voice service issue. Please tap Speak now and try again.");
        return;
      }
      if (code === "no-speech" || code === "aborted") {
        setVoiceErr(null);
        return;
      }
      setVoiceErr(message);
    },
  });

  function onSourceLang(v: Lang) {
    setSource(v);
    setVoiceErr(null);
  }

  function swap() {
    setSource(target);
    setTarget(source);
    setInput(output);
    setOutput(input);
    setVoiceErr(null);
  }

  return (
    <div className="container py-12 md:py-16">
      <header className="mb-8">
        <span className="kicker">
          <Languages className="h-3 w-3" />
          Translator
        </span>
        <h1 className="display mt-3 text-4xl font-medium tracking-tightest text-ink-900 md:text-5xl">
          Real-time voice translation for <em className="text-jade-700 not-italic">English, Sinhala, Tamil</em>.
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-600">
          Speak naturally and get instant translation with optional playback.
          You can still type or paste text when needed.
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-[1fr_auto_1fr]">
        <Pane
          lang={source}
          onLang={onSourceLang}
          value={input}
          onChange={setInput}
          editable
          onSpeak={() => speech.speak(input, source)}
          voiceSupported={recog.supported}
          listening={recog.listening}
          onToggleVoice={recog.toggle}
          busy={busy}
        />
        <button
          onClick={swap}
          className="inline-flex h-10 w-10 items-center justify-center self-center rounded-full border border-border bg-white shadow-soft transition-colors hover:border-jade-300 hover:text-jade-700"
          title="Swap languages"
        >
          <ArrowRightLeft className="h-4 w-4" />
        </button>
        <Pane
          lang={target}
          onLang={setTarget}
          value={output}
          onChange={() => {}}
          editable={false}
          onSpeak={() => speech.speak(output, target)}
          voiceSupported={false}
          listening={false}
          onToggleVoice={() => {}}
          busy={busy}
        />
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <button
          onClick={() => void translate(input)}
          disabled={busy || !input.trim()}
          className="inline-flex items-center gap-2 rounded-full bg-jade-700 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-jade-800 disabled:opacity-60"
        >
          {busy ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Languages className="h-4 w-4" />
          )}
          Translate
        </button>
        <button
          onClick={() => setVoiceMode((v) => !v)}
          className={cn(
            "inline-flex items-center gap-2 rounded-full border px-4 py-2.5 text-sm font-semibold transition-colors",
            voiceMode
              ? "border-jade-700 bg-jade-50 text-jade-700"
              : "border-border bg-white text-ink-700 hover:border-jade-300"
          )}
        >
          <Volume2 className="h-4 w-4" />
          {voiceMode ? "Voice playback on" : "Voice playback off"}
        </button>
        {err && <p className="text-sm text-red-700">{err}</p>}
        {!recog.supported && (
          <p className="text-sm text-amber-700">
            Voice input is not supported in this browser. Try Chrome or Edge.
          </p>
        )}
        {voiceErr && <p className="text-sm text-red-700">{voiceErr}</p>}
      </div>
    </div>
  );
}

function Pane({
  lang,
  onLang,
  value,
  onChange,
  editable,
  onSpeak,
  voiceSupported,
  listening,
  onToggleVoice,
  busy,
}: {
  lang: Lang;
  onLang: (v: Lang) => void;
  value: string;
  onChange: (v: string) => void;
  editable: boolean;
  onSpeak: () => void;
  voiceSupported: boolean;
  listening: boolean;
  onToggleVoice: () => void;
  busy: boolean;
}) {
  return (
    <div className="flex flex-col rounded-3xl border border-border bg-white p-4 shadow-soft">
      <div className="flex items-center justify-between">
        <select
          value={lang}
          onChange={(e) => onLang(e.target.value as Lang)}
          className="rounded-full border border-border bg-white px-3 py-1.5 text-sm font-semibold focus:outline-none"
        >
          {LANGS.map((l) => (
            <option key={l.id} value={l.id}>
              {l.label}
            </option>
          ))}
        </select>
        <button
          onClick={onSpeak}
          disabled={!value.trim()}
          className={cn(
            "rounded-full px-3 py-1 text-xs font-medium transition-colors",
            value.trim()
              ? "text-jade-700 hover:bg-jade-50"
              : "text-ink-400"
          )}
        >
          Read aloud
        </button>
      </div>
      {editable && voiceSupported && (
        <div className="mt-3">
          <button
            type="button"
            onClick={onToggleVoice}
            disabled={busy || !voiceSupported}
            className={cn(
              "inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors",
              listening
                ? "bg-red-600 text-white"
                : voiceSupported
                  ? "bg-saffron-300 text-jade-900 hover:bg-saffron-400"
                  : "bg-muted text-ink-400"
            )}
          >
            {listening ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
            {listening ? "Listening..." : "Speak now"}
          </button>
        </div>
      )}
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        readOnly={!editable}
        rows={10}
        placeholder={
          editable
            ? listening
              ? "Listening... speak your phrase"
              : "Speak, type, or paste text..."
            : "Translation will appear here..."
        }
        className={cn(
          "mt-3 min-h-[200px] resize-none rounded-2xl border border-border bg-white px-3 py-3 text-sm text-ink-900 focus:border-jade-500 focus:outline-none",
          !editable && "bg-jade-50/30"
        )}
      />
      <p className="mt-2 text-xs text-ink-500">{value.length} characters</p>
    </div>
  );
}
