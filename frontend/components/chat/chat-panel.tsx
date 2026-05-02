"use client";

import { useEffect, useReducer, useRef, useState } from "react";
import {
  ArrowUp,
  Bot,
  Compass,
  Globe2,
  Loader2,
  MapPin,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { api, toApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

// ─────────────────────────── Types ─────────────────────────────────────
type Source = {
  doc_id: string;
  title: string;
  relevance: number;
  attraction_id?: number | null;
  district_id?: number | null;
  category?: string | null;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  pending?: boolean;
};

type Action =
  | { type: "append"; message: Message }
  | { type: "patch"; id: string; patch: Partial<Message> }
  | { type: "reset" };

function reducer(state: Message[], action: Action): Message[] {
  switch (action.type) {
    case "append":
      return [...state, action.message];
    case "patch":
      return state.map((m) =>
        m.id === action.id ? { ...m, ...action.patch } : m
      );
    case "reset":
      return [];
    default:
      return state;
  }
}

const STARTERS: Array<{ q: string; tag: string }> = [
  { q: "When is the best time to visit Sigiriya?", tag: "Cultural" },
  { q: "Plan a 5-day trip across the southern coast.", tag: "Itinerary" },
  { q: "Where will I see leopards at Yala?", tag: "Wildlife" },
  { q: "What's the train route from Kandy to Ella like?", tag: "Travel" },
];

const LANGS = [
  { id: "en", label: "English" },
  { id: "si", label: "සිංහල" },
  { id: "ta", label: "தமிழ்" },
];

// ─────────────────────────── Component ─────────────────────────────────
export function ChatPanel() {
  const [messages, dispatch] = useReducer(reducer, []);
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState<"en" | "si" | "ta">("en");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem("lankaguide.chat_session_id");
    if (stored) setSessionId(Number(stored));
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  async function send(text: string) {
    if (!text.trim() || busy) return;
    setError(null);
    const userId = `u-${crypto.randomUUID()}`;
    const assistantId = `a-${crypto.randomUUID()}`;
    dispatch({ type: "append", message: { id: userId, role: "user", content: text } });
    dispatch({
      type: "append",
      message: { id: assistantId, role: "assistant", content: "", pending: true },
    });
    setInput("");
    setBusy(true);
    try {
      const { data } = await api.post("/api/v1/chat/message/", {
        message: text,
        language,
        session_id: sessionId,
      });
      if (data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id);
        localStorage.setItem("lankaguide.chat_session_id", String(data.session_id));
      }
      dispatch({
        type: "patch",
        id: assistantId,
        patch: {
          content: data.response,
          sources: data.sources ?? [],
          pending: false,
        },
      });
    } catch (err) {
      const apiErr = toApiError(err);
      dispatch({
        type: "patch",
        id: assistantId,
        patch: {
          pending: false,
          content:
            "Sorry — the AI service is unavailable right now. Please try again in a moment.",
        },
      });
      setError(apiErr.message);
    } finally {
      setBusy(false);
    }
  }

  function newSession() {
    setSessionId(null);
    localStorage.removeItem("lankaguide.chat_session_id");
    dispatch({ type: "reset" });
  }

  return (
    <div className="container py-10 md:py-14">
      <header className="mb-8 flex flex-col gap-6 md:mb-12 md:flex-row md:items-end md:justify-between">
        <div className="max-w-2xl reveal">
          <span className="kicker">
            <Bot className="h-3 w-3" />
            The AI guide
          </span>
          <h1 className="display mt-3 text-4xl font-medium tracking-tightest text-ink-900 md:text-6xl">
            Ask anything about{" "}
            <em className="text-jade-700 not-italic">Sri Lanka</em>.
          </h1>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-ink-600 md:text-base">
            Every answer is grounded in a curated atlas of 25 districts.
            When the guide isn&apos;t sure, it tells you — no hallucinations
            sold as facts.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <LanguagePicker value={language} onChange={setLanguage} />
          <button
            onClick={newSession}
            className="inline-flex items-center gap-2 rounded-full border border-border bg-white px-4 py-2 text-sm font-medium text-ink-700 shadow-soft transition-colors hover:border-jade-300 hover:text-jade-700"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            New chat
          </button>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        {/* ── Chat thread ── */}
        <section className="relative isolate flex h-[72vh] flex-col overflow-hidden rounded-3xl border border-border bg-white/60 shadow-soft backdrop-blur">
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto px-5 py-8 md:px-10 md:py-12"
          >
            {messages.length === 0 ? (
              <EmptyState onPick={send} />
            ) : (
              <div className="mx-auto flex max-w-3xl flex-col gap-8">
                {messages.map((m) => (
                  <MessageBubble key={m.id} message={m} />
                ))}
              </div>
            )}
          </div>

          <div className="border-t border-border/70 bg-white/80 px-5 py-4 md:px-10 md:py-5">
            {error && (
              <p className="mb-2 text-xs text-destructive">{error}</p>
            )}
            <Composer
              value={input}
              onChange={setInput}
              onSend={() => send(input)}
              busy={busy}
            />
          </div>
        </section>

        {/* ── Side rail ── */}
        <aside className="space-y-4 lg:sticky lg:top-28 lg:self-start">
          <PromptDeck onPick={send} />
          <TipCard />
        </aside>
      </div>
    </div>
  );
}

// ─────────────────────────── Sub-components ────────────────────────────
function EmptyState({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center justify-center py-16 text-center">
      <div className="grid h-14 w-14 place-items-center rounded-2xl bg-jade-600 text-white shadow-glow">
        <Sparkles className="h-6 w-6" />
      </div>
      <h2 className="display mt-6 text-3xl font-medium tracking-tightest text-ink-900">
        Where shall we start?
      </h2>
      <p className="mt-3 max-w-md text-sm text-ink-600">
        Ask about cultural sites, monsoons, food, train routes — or have
        the guide draft a full itinerary for you.
      </p>
      <div className="mt-8 grid w-full max-w-xl gap-2 sm:grid-cols-2">
        {STARTERS.map((s, i) => (
          <button
            key={s.q}
            type="button"
            onClick={() => onPick(s.q)}
            className="group reveal flex flex-col gap-2 rounded-2xl border border-border bg-white px-5 py-4 text-left text-sm text-ink-700 shadow-soft transition-all hover:border-jade-300 hover:shadow-lift"
            style={{ animationDelay: `${i * 70}ms` }}
          >
            <span className="text-[10px] font-semibold uppercase tracking-kicker text-saffron-600">
              {s.tag}
            </span>
            <span className="leading-snug text-ink-900 group-hover:text-jade-700">
              {s.q}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div
      className={cn("flex gap-3 reveal", isUser && "flex-row-reverse")}
    >
      <div
        className={cn(
          "grid h-9 w-9 shrink-0 place-items-center rounded-full text-xs font-semibold shadow-soft",
          isUser
            ? "bg-saffron-400 text-jade-900"
            : "bg-jade-600 text-white"
        )}
      >
        {isUser ? "You" : <Bot className="h-4 w-4" />}
      </div>
      <div
        className={cn(
          "max-w-[88%] rounded-3xl border px-5 py-4 text-sm leading-relaxed shadow-soft",
          isUser
            ? "rounded-tr-md border-saffron-200 bg-saffron-50 text-ink-900"
            : "rounded-tl-md border-border bg-white text-ink-900"
        )}
      >
        {message.pending ? (
          <ThinkingDots />
        ) : isUser ? (
          message.content
        ) : (
          <div className="space-y-3 [&_a]:text-jade-700 [&_a]:underline [&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_h1]:font-display [&_h1]:text-lg [&_h1]:font-medium [&_h2]:font-display [&_h2]:text-base [&_h2]:font-medium [&_li]:ml-5 [&_li]:list-disc [&_p]:leading-relaxed">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <div className="mt-4 border-t border-border pt-3">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-kicker text-ink-500">
              Sourced from
            </p>
            <div className="flex flex-wrap gap-1.5">
              {message.sources.slice(0, 5).map((s) => (
                <span
                  key={s.doc_id}
                  className="inline-flex items-center gap-1.5 rounded-full bg-jade-50 px-2.5 py-1 text-[11px] font-medium text-jade-700 ring-1 ring-jade-100"
                  title={`Relevance ${Math.round(s.relevance * 100)}%`}
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-jade-500" />
                  {s.title.replace(/-/g, " ")}
                  <span className="text-jade-500/80">
                    {Math.round(s.relevance * 100)}%
                  </span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ThinkingDots() {
  return (
    <span className="inline-flex items-center gap-1.5 text-ink-500">
      <span className="text-xs font-medium uppercase tracking-kicker">Thinking</span>
      <span className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 animate-pulse rounded-full bg-jade-600"
            style={{ animationDelay: `${i * 120}ms` }}
          />
        ))}
      </span>
    </span>
  );
}

function Composer({
  value,
  onChange,
  onSend,
  busy,
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  busy: boolean;
}) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSend();
      }}
      className="flex items-end gap-2 rounded-2xl border border-border bg-white p-2 shadow-soft transition-shadow focus-within:border-jade-400 focus-within:shadow-glow"
    >
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend();
          }
        }}
        placeholder="Type your question — Enter to send · Shift + Enter for newline"
        rows={2}
        disabled={busy}
        className="min-h-[60px] flex-1 resize-none bg-transparent px-3 py-2 text-sm text-ink-900 placeholder:text-ink-500 focus:outline-none"
      />
      <button
        type="submit"
        disabled={busy || !value.trim()}
        className="grid h-11 w-11 place-items-center rounded-xl bg-jade-600 text-white shadow-soft transition-all hover:bg-jade-700 hover:shadow-lift disabled:cursor-not-allowed disabled:bg-ink-300"
      >
        {busy ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <ArrowUp className="h-4 w-4" />
        )}
      </button>
    </form>
  );
}

function LanguagePicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: "en" | "si" | "ta") => void;
}) {
  return (
    <div className="inline-flex items-center gap-1 rounded-full border border-border bg-white p-1 shadow-soft">
      <Globe2 className="ml-2 h-3.5 w-3.5 text-ink-500" />
      {LANGS.map((l) => (
        <button
          key={l.id}
          onClick={() => onChange(l.id as "en" | "si" | "ta")}
          className={cn(
            "rounded-full px-3 py-1 text-xs font-medium transition-colors",
            value === l.id
              ? "bg-jade-600 text-white shadow-soft"
              : "text-ink-600 hover:text-ink-900"
          )}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}

function PromptDeck({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="rounded-3xl border border-border bg-white/80 p-5 shadow-soft backdrop-blur">
      <span className="kicker">
        <Compass className="h-3 w-3" />
        Try one of these
      </span>
      <div className="mt-4 flex flex-col gap-2">
        {STARTERS.map((s) => (
          <button
            key={s.q}
            onClick={() => onPick(s.q)}
            className="group flex flex-col items-start gap-1 rounded-2xl border border-transparent bg-jade-50/60 px-4 py-3 text-left transition-colors hover:border-jade-200 hover:bg-jade-50"
          >
            <span className="text-[10px] font-semibold uppercase tracking-kicker text-saffron-600">
              {s.tag}
            </span>
            <span className="text-sm font-medium text-ink-900 group-hover:text-jade-700">
              {s.q}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

function TipCard() {
  return (
    <div className="rounded-3xl border border-jade-700 bg-jade-900 p-5 text-jade-50 shadow-glow">
      <span className="kicker text-saffron-300 before:bg-saffron-300/60">
        <MapPin className="h-3 w-3" />
        Pro tip
      </span>
      <p className="mt-3 text-sm leading-relaxed text-jade-100/90">
        After a great answer, jump straight to the{" "}
        <span className="font-semibold text-saffron-300">Itinerary</span>{" "}
        builder — your conversation context will inform the trip plan.
      </p>
    </div>
  );
}
