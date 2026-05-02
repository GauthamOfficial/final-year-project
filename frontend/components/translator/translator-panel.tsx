"use client";

import { useState } from "react";
import { ArrowRightLeft, Languages, Loader2 } from "lucide-react";
import { api, toApiError } from "@/lib/api";
import { useSpeechSynthesis } from "@/lib/voice";
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
  const speech = useSpeechSynthesis();

  async function translate() {
    if (!input.trim()) return;
    setBusy(true);
    setErr(null);
    setOutput("");
    try {
      const { data } = await api.post("/api/v1/translate/", {
        text: input,
        source,
        target,
      });
      setOutput(data?.translation ?? "");
    } catch (e) {
      setErr(toApiError(e).message || "Translation failed.");
    } finally {
      setBusy(false);
    }
  }

  function swap() {
    setSource(target);
    setTarget(source);
    setInput(output);
    setOutput(input);
  }

  return (
    <div className="container py-12 md:py-16">
      <header className="mb-8">
        <span className="kicker">
          <Languages className="h-3 w-3" />
          Translator
        </span>
        <h1 className="display mt-3 text-4xl font-medium tracking-tightest text-ink-900 md:text-5xl">
          Translate any phrase across <em className="text-jade-700 not-italic">English, Sinhala, Tamil</em>.
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-600">
          Powered by the same model that grounds the AI guide. Names, numbers,
          and Markdown formatting are preserved.
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-[1fr_auto_1fr]">
        <Pane
          lang={source}
          onLang={setSource}
          value={input}
          onChange={setInput}
          editable
          onSpeak={() => speech.speak(input, source)}
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
        />
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <button
          onClick={translate}
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
        {err && <p className="text-sm text-red-700">{err}</p>}
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
}: {
  lang: Lang;
  onLang: (v: Lang) => void;
  value: string;
  onChange: (v: string) => void;
  editable: boolean;
  onSpeak: () => void;
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
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        readOnly={!editable}
        rows={10}
        placeholder={editable ? "Type or paste text…" : "Translation will appear here…"}
        className={cn(
          "mt-3 min-h-[200px] resize-none rounded-2xl border border-border bg-white px-3 py-3 text-sm text-ink-900 focus:border-jade-500 focus:outline-none",
          !editable && "bg-jade-50/30"
        )}
      />
      <p className="mt-2 text-xs text-ink-500">{value.length} characters</p>
    </div>
  );
}
