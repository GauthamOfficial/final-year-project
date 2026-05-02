"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/lib/auth";
import {
  Calendar,
  Check,
  ChevronLeft,
  ChevronRight,
  Compass,
  Loader2,
  MapPin,
  Mountain,
  Palmtree,
  Share2,
  Sparkles,
  Tent,
  TreePine,
  UtensilsCrossed,
  Users,
} from "lucide-react";
import { api, toApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { MapView } from "@/components/maps/map-view";
import { WeatherCard } from "@/components/weather/weather-card";
import { Download } from "lucide-react";

// ─────────────────────────── Types ──────────────────────────────────────
type District = {
  id: number;
  name: string;
  province: string;
  attraction_count: number;
};

type Stop = {
  id: number;
  stop_order: number;
  attraction_id: number;
  name: string;
  slug: string;
  lat: string | null;
  lng: string | null;
  arrival_time: string | null;
  duration_mins: number | null;
  tip: string;
};

type Day = {
  id: number;
  day_number: number;
  district: number | null;
  district_name: string | null;
  district_slug?: string | null;
  notes: string;
  stops: Stop[];
};

type Itinerary = {
  id: number;
  title: string;
  start_date: string;
  end_date: string;
  budget_lkr: string;
  group_size: number;
  group_type: string;
  status: string;
  share_token: string;
  days: Day[];
};

type InterestId =
  | "beach"
  | "wildlife"
  | "cultural"
  | "adventure"
  | "food"
  | "religious";

const INTERESTS: Array<{ id: InterestId; label: string; icon: React.ElementType; tone: string }> = [
  { id: "beach", label: "Beach", icon: Palmtree, tone: "from-sky-100 text-sky-900" },
  { id: "wildlife", label: "Wildlife", icon: TreePine, tone: "from-emerald-100 text-emerald-900" },
  { id: "cultural", label: "Cultural", icon: Mountain, tone: "from-saffron-100 text-saffron-700" },
  { id: "adventure", label: "Adventure", icon: Tent, tone: "from-rose-100 text-rose-900" },
  { id: "food", label: "Food", icon: UtensilsCrossed, tone: "from-orange-100 text-orange-900" },
  { id: "religious", label: "Religious", icon: Sparkles, tone: "from-violet-100 text-violet-900" },
];

const GROUP_TYPES = [
  { id: "solo", label: "Solo", emoji: "𓂃" },
  { id: "couple", label: "Couple", emoji: "𓂀" },
  { id: "family", label: "Family", emoji: "𓊝" },
  { id: "group", label: "Group", emoji: "𓂀𓂀" },
];

const STEPS = [
  { key: "dates", label: "Dates", helper: "When are you going?" },
  { key: "interests", label: "Interests", helper: "What gets you out of bed?" },
  { key: "districts", label: "Regions", helper: "Where do you want to roam?" },
  { key: "budget", label: "Budget", helper: "How loose are the purse-strings?" },
  { key: "group", label: "Group", helper: "Who's going?" },
] as const;

type StepKey = (typeof STEPS)[number]["key"];

function todayPlus(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

// ─────────────────────────── Component ──────────────────────────────────
export function ItineraryWizard() {
  const router = useRouter();
  const { user, hydrated } = useAuth();
  const [step, setStep] = useState<StepKey>("dates");
  const [start, setStart] = useState(todayPlus(14));
  const [end, setEnd] = useState(todayPlus(20));
  const [budget, setBudget] = useState(50000);
  const [interests, setInterests] = useState<Set<InterestId>>(
    () => new Set<InterestId>(["cultural"])
  );
  const [districtIds, setDistrictIds] = useState<Set<number>>(new Set());
  const [groupType, setGroupType] = useState("couple");
  const [groupSize, setGroupSize] = useState(2);

  const [districts, setDistricts] = useState<District[]>([]);
  const [districtError, setDistrictError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (hydrated && !user) {
      router.replace("/login?next=/itinerary");
    }
  }, [hydrated, user, router]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get("/api/v1/attractions/districts/");
        if (cancelled) return;
        const list: District[] = data.results ?? data;
        setDistricts(list);
      } catch (err) {
        if (!cancelled) setDistrictError(toApiError(err).message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const stepIndex = STEPS.findIndex((s) => s.key === step);
  const canPrev = stepIndex > 0;
  const canNext = stepIndex < STEPS.length - 1;
  const ready =
    interests.size > 0 && districtIds.size > 0 && start && end && start <= end;

  function next() {
    if (canNext) setStep(STEPS[stepIndex + 1].key);
  }
  function prev() {
    if (canPrev) setStep(STEPS[stepIndex - 1].key);
  }

  async function submit() {
    if (!ready) return;
    setSubmitting(true);
    setError(null);
    try {
      const { data } = await api.post("/api/v1/itinerary/generate/", {
        start_date: start,
        end_date: end,
        budget_lkr: budget,
        interests: Array.from(interests),
        district_ids: Array.from(districtIds),
        group_type: groupType,
        group_size: groupSize,
      });
      setItinerary(data);
      // scroll to top so the result hero is visible
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setError(toApiError(err).message);
    } finally {
      setSubmitting(false);
    }
  }

  if (hydrated && !user) {
    return null;
  }

  if (itinerary) {
    return (
      <ItineraryResult
        itinerary={itinerary}
        onStartOver={() => {
          setItinerary(null);
          setStep("dates");
        }}
      />
    );
  }

  return (
    <div className="container py-12 md:py-16">
      {/* Hero header */}
      <header className="mb-12 max-w-3xl reveal">
        <span className="kicker">
          <Compass className="h-3 w-3" />
          Itinerary studio
        </span>
        <h1 className="display mt-4 text-5xl font-medium tracking-tightest text-ink-900 md:text-7xl">
          Let&apos;s draft your{" "}
          <em className="text-jade-700 not-italic">trip</em>.
        </h1>
        <p className="mt-5 text-base leading-relaxed text-ink-600 md:text-lg">
          Five quick decisions and the AI will hand you back a day-by-day
          plan grounded in real seasonal data. Swap, regenerate, share.
        </p>
      </header>

      <div className="grid gap-8 lg:grid-cols-[280px_1fr_320px]">
        {/* ── Vertical stepper ── */}
        <nav className="lg:sticky lg:top-28 lg:self-start">
          <ol className="flex flex-row gap-2 overflow-x-auto lg:flex-col lg:gap-1">
            {STEPS.map((s, i) => {
              const isActive = step === s.key;
              const isDone = i < stepIndex;
              return (
                <li key={s.key} className="lg:flex lg:items-stretch">
                  <button
                    onClick={() => setStep(s.key)}
                    className={cn(
                      "group flex w-full items-center gap-4 rounded-2xl border px-4 py-3 text-left transition-all lg:py-4",
                      isActive
                        ? "border-jade-700 bg-jade-700 text-white shadow-glow"
                        : isDone
                          ? "border-jade-200 bg-jade-50 text-jade-700"
                          : "border-border bg-white text-ink-700 hover:border-jade-200"
                    )}
                  >
                    <span
                      className={cn(
                        "grid h-8 w-8 shrink-0 place-items-center rounded-full text-xs font-semibold",
                        isActive
                          ? "bg-white text-jade-900"
                          : isDone
                            ? "bg-jade-600 text-white"
                            : "bg-muted text-ink-500"
                      )}
                    >
                      {isDone ? <Check className="h-4 w-4" /> : i + 1}
                    </span>
                    <span className="flex-1">
                      <span className="block text-sm font-semibold">
                        {s.label}
                      </span>
                      <span
                        className={cn(
                          "block text-[11px]",
                          isActive ? "text-white/75" : "text-ink-500"
                        )}
                      >
                        {s.helper}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
        </nav>

        {/* ── Step body ── */}
        <section className="rounded-3xl border border-border bg-white p-6 shadow-soft md:p-10 reveal reveal-1">
          <div className="mb-8 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-kicker text-ink-500">
              Step {stepIndex + 1} of {STEPS.length}
            </span>
            <span className="text-xs text-ink-500">
              {STEPS[stepIndex].helper}
            </span>
          </div>

          {step === "dates" && (
            <StepDates
              start={start}
              end={end}
              onStartChange={setStart}
              onEndChange={setEnd}
            />
          )}
          {step === "interests" && (
            <StepInterests value={interests} onChange={setInterests} />
          )}
          {step === "districts" && (
            <StepDistricts
              districts={districts}
              error={districtError}
              value={districtIds}
              onChange={setDistrictIds}
            />
          )}
          {step === "budget" && (
            <StepBudget value={budget} onChange={setBudget} />
          )}
          {step === "group" && (
            <StepGroup
              groupType={groupType}
              setGroupType={setGroupType}
              groupSize={groupSize}
              setGroupSize={setGroupSize}
            />
          )}

          {/* Footer controls */}
          <div className="mt-10 flex items-center justify-between border-t border-border pt-6">
            <button
              onClick={prev}
              disabled={!canPrev}
              className="inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium text-ink-700 transition-colors hover:text-jade-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
              Back
            </button>
            {canNext ? (
              <button
                onClick={next}
                className="inline-flex items-center gap-1.5 rounded-full bg-jade-700 px-6 py-3 text-sm font-semibold text-white shadow-soft transition-all hover:bg-jade-800 hover:shadow-lift"
              >
                Continue
                <ChevronRight className="h-4 w-4" />
              </button>
            ) : (
              <button
                onClick={submit}
                disabled={!ready || submitting}
                className="inline-flex items-center gap-2 rounded-full bg-saffron-400 px-7 py-3 text-sm font-semibold text-jade-900 shadow-glow transition-all hover:bg-saffron-300 disabled:cursor-not-allowed disabled:bg-ink-300 disabled:text-white disabled:shadow-none"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Drafting…
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Generate itinerary
                  </>
                )}
              </button>
            )}
          </div>

          {error && (
            <div className="mt-4 rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
              {error}
            </div>
          )}
        </section>

        {/* ── Live summary ── */}
        <aside className="lg:sticky lg:top-28 lg:self-start">
          <SummaryCard
            start={start}
            end={end}
            budget={budget}
            interests={interests}
            districtIds={districtIds}
            districts={districts}
            groupType={groupType}
            groupSize={groupSize}
          />
        </aside>
      </div>
    </div>
  );
}

// ─────────────────────────── Step components ────────────────────────────
function StepDates({
  start,
  end,
  onStartChange,
  onEndChange,
}: {
  start: string;
  end: string;
  onStartChange: (v: string) => void;
  onEndChange: (v: string) => void;
}) {
  const days = useMemo(() => calcDays(start, end), [start, end]);
  return (
    <div className="space-y-6">
      <h2 className="display text-3xl font-medium tracking-tightest text-ink-900">
        When are you on the island?
      </h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <DateField label="Arrival" value={start} onChange={onStartChange} />
        <DateField label="Departure" value={end} onChange={onEndChange} />
      </div>
      <div className="flex items-center gap-3 rounded-2xl border border-jade-100 bg-jade-50 px-4 py-3 text-sm text-jade-800">
        <Calendar className="h-4 w-4 text-jade-700" />
        <span className="font-semibold">{days} day{days === 1 ? "" : "s"} on the ground</span>
        <span className="text-jade-700/70">
          · {new Date(start).toLocaleDateString("en-GB", { weekday: "short" })} →
          {" "}
          {new Date(end).toLocaleDateString("en-GB", { weekday: "short" })}
        </span>
      </div>
    </div>
  );
}

function StepInterests({
  value,
  onChange,
}: {
  value: Set<InterestId>;
  onChange: (v: Set<InterestId>) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="display text-3xl font-medium tracking-tightest text-ink-900">
        What gets you out of bed?
      </h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {INTERESTS.map((it) => {
          const selected = value.has(it.id);
          const Icon = it.icon;
          return (
            <button
              key={it.id}
              type="button"
              onClick={() => {
                const next = new Set(value);
                if (selected) next.delete(it.id);
                else next.add(it.id);
                onChange(next);
              }}
              className={cn(
                "group relative flex flex-col items-start gap-3 overflow-hidden rounded-2xl border p-5 text-left transition-all",
                selected
                  ? "border-jade-700 bg-jade-700 text-white shadow-glow"
                  : "border-border bg-white text-ink-900 hover:border-jade-300 hover:shadow-soft"
              )}
            >
              <span
                className={cn(
                  "grid h-10 w-10 place-items-center rounded-xl",
                  selected ? "bg-white/15 text-white" : "bg-jade-50 text-jade-700"
                )}
              >
                <Icon className="h-5 w-5" />
              </span>
              <div>
                <span className="display block text-lg font-medium tracking-tightest">
                  {it.label}
                </span>
              </div>
              {selected && (
                <span className="absolute right-4 top-4 grid h-6 w-6 place-items-center rounded-full bg-saffron-400 text-jade-900">
                  <Check className="h-3.5 w-3.5" />
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function StepDistricts({
  districts,
  error,
  value,
  onChange,
}: {
  districts: District[];
  error: string | null;
  value: Set<number>;
  onChange: (v: Set<number>) => void;
}) {
  return (
    <div className="space-y-5">
      <h2 className="display text-3xl font-medium tracking-tightest text-ink-900">
        Where do you want to roam?
      </h2>
      {error ? (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error}
        </div>
      ) : (
        <div className="grid max-h-[420px] grid-cols-1 gap-2 overflow-y-auto pr-2 sm:grid-cols-2">
          {districts.map((d) => {
            const selected = value.has(d.id);
            return (
              <button
                key={d.id}
                onClick={() => {
                  const next = new Set(value);
                  if (selected) next.delete(d.id);
                  else next.add(d.id);
                  onChange(next);
                }}
                className={cn(
                  "group flex items-start gap-3 rounded-xl border p-4 text-left transition-colors",
                  selected
                    ? "border-jade-700 bg-jade-50 text-jade-900"
                    : "border-border bg-white hover:border-jade-300"
                )}
              >
                <span
                  className={cn(
                    "mt-1 grid h-5 w-5 shrink-0 place-items-center rounded-md border",
                    selected
                      ? "border-jade-700 bg-jade-700 text-white"
                      : "border-border"
                  )}
                >
                  {selected && <Check className="h-3 w-3" />}
                </span>
                <div className="flex-1">
                  <p className="text-sm font-semibold">{d.name}</p>
                  <p className="text-[11px] uppercase tracking-kicker text-ink-500">
                    {d.province} · {d.attraction_count} place
                    {d.attraction_count === 1 ? "" : "s"}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function StepBudget({
  value,
  onChange,
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="space-y-8">
      <h2 className="display text-3xl font-medium tracking-tightest text-ink-900">
        Daily budget
      </h2>
      <div className="rounded-3xl border border-jade-100 bg-jade-50/50 p-8 text-center">
        <div className="display text-6xl font-medium leading-none tracking-tightest text-jade-700 md:text-7xl">
          LKR {value.toLocaleString()}
        </div>
        <p className="mt-3 text-xs uppercase tracking-kicker text-ink-500">
          Per person · per day
        </p>
      </div>
      <input
        type="range"
        min={5000}
        max={500000}
        step={1000}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-jade-700"
      />
      <div className="grid grid-cols-3 gap-2 text-center text-xs text-ink-500">
        <BudgetTier label="Backpacker" range="< 25k" active={value < 25000} />
        <BudgetTier
          label="Mid-range"
          range="25k–80k"
          active={value >= 25000 && value < 80000}
        />
        <BudgetTier label="Luxury" range="80k+" active={value >= 80000} />
      </div>
    </div>
  );
}

function BudgetTier({
  label,
  range,
  active,
}: {
  label: string;
  range: string;
  active: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border p-3 transition-colors",
        active
          ? "border-jade-700 bg-jade-700 text-white"
          : "border-border bg-white"
      )}
    >
      <p className="text-sm font-semibold">{label}</p>
      <p className={cn("text-[10px] uppercase tracking-kicker", active && "text-white/75")}>
        {range}
      </p>
    </div>
  );
}

function StepGroup({
  groupType,
  setGroupType,
  groupSize,
  setGroupSize,
}: {
  groupType: string;
  setGroupType: (v: string) => void;
  groupSize: number;
  setGroupSize: (v: number) => void;
}) {
  return (
    <div className="space-y-8">
      <h2 className="display text-3xl font-medium tracking-tightest text-ink-900">
        Who&apos;s travelling?
      </h2>
      <div>
        <span className="kicker">Group type</span>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {GROUP_TYPES.map((g) => (
            <button
              key={g.id}
              onClick={() => setGroupType(g.id)}
              className={cn(
                "flex flex-col items-center gap-2 rounded-2xl border px-4 py-5 transition-colors",
                groupType === g.id
                  ? "border-jade-700 bg-jade-700 text-white shadow-glow"
                  : "border-border bg-white text-ink-700 hover:border-jade-300"
              )}
            >
              <Users className="h-5 w-5" />
              <span className="text-sm font-semibold">{g.label}</span>
            </button>
          ))}
        </div>
      </div>
      <div>
        <span className="kicker">Headcount</span>
        <div className="mt-3 flex items-center gap-4">
          <button
            onClick={() => setGroupSize(Math.max(1, groupSize - 1))}
            className="grid h-11 w-11 place-items-center rounded-full border border-border bg-white text-lg font-semibold text-ink-700 hover:border-jade-300"
          >
            −
          </button>
          <div className="display flex-1 text-center text-5xl font-medium tracking-tightest text-jade-700">
            {groupSize}
          </div>
          <button
            onClick={() => setGroupSize(Math.min(50, groupSize + 1))}
            className="grid h-11 w-11 place-items-center rounded-full border border-border bg-white text-lg font-semibold text-ink-700 hover:border-jade-300"
          >
            +
          </button>
        </div>
      </div>
    </div>
  );
}

function DateField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="kicker">{label}</span>
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-2 h-12 w-full rounded-xl border border-border bg-white px-4 text-base font-medium text-ink-900 shadow-soft focus:border-jade-400 focus:outline-none focus:ring-2 focus:ring-jade-100"
      />
    </label>
  );
}

// ─────────────────────────── Summary ────────────────────────────────────
function SummaryCard({
  start,
  end,
  budget,
  interests,
  districtIds,
  districts,
  groupType,
  groupSize,
}: {
  start: string;
  end: string;
  budget: number;
  interests: Set<InterestId>;
  districtIds: Set<number>;
  districts: District[];
  groupType: string;
  groupSize: number;
}) {
  const days = useMemo(() => calcDays(start, end), [start, end]);
  const districtNames = useMemo(
    () => districts.filter((d) => districtIds.has(d.id)).map((d) => d.name),
    [districtIds, districts]
  );

  return (
    <div className="space-y-3">
      <div className="rounded-3xl border border-jade-700 bg-jade-900 p-6 text-jade-50 shadow-glow">
        <span className="kicker text-saffron-300 before:bg-saffron-300/60">
          <MapPin className="h-3 w-3" />
          Trip in progress
        </span>
        <p className="display mt-3 text-3xl font-medium leading-tight text-white">
          {days}-day {Array.from(interests).join(", ") || "Sri Lanka"} trip
        </p>
        <div className="mt-5 grid grid-cols-3 gap-3 text-center">
          <Stat number={String(days)} label="days" />
          <Stat number={String(districtIds.size)} label="districts" />
          <Stat number={String(groupSize)} label={groupType} />
        </div>
      </div>

      <div className="rounded-3xl border border-border bg-white p-5 shadow-soft">
        <div className="space-y-3 text-sm">
          <Row label="Daily budget">
            LKR {budget.toLocaleString()}
          </Row>
          <Row label="Districts">
            {districtNames.length
              ? districtNames.slice(0, 3).join(", ") +
                (districtNames.length > 3 ? ` + ${districtNames.length - 3}` : "")
              : "—"}
          </Row>
          <Row label="Themes">
            {interests.size
              ? Array.from(interests).join(", ")
              : "Pick at least one"}
          </Row>
        </div>
      </div>
    </div>
  );
}

function Stat({ number, label }: { number: string; label: string }) {
  return (
    <div>
      <div className="display text-3xl font-medium leading-none text-saffron-300">
        {number}
      </div>
      <div className="mt-1 text-[10px] uppercase tracking-kicker text-jade-100/70">
        {label}
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-border/60 pb-2 last:border-none last:pb-0">
      <span className="text-[10px] font-semibold uppercase tracking-kicker text-ink-500">
        {label}
      </span>
      <span className="text-right text-sm font-semibold text-ink-900">
        {children}
      </span>
    </div>
  );
}

function calcDays(start: string, end: string) {
  const s = new Date(start);
  const e = new Date(end);
  return Math.max(1, Math.round((+e - +s) / (1000 * 60 * 60 * 24)) + 1);
}

function DayEta({
  stops,
}: {
  stops: Array<{ id: number | string; name: string; lat: number; lng: number }>;
}) {
  const [eta, setEta] = useState<{
    duration_min_estimated: number;
    distance_km: number;
    congestion_label: string;
  } | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (stops.length < 2) return;
    const a = stops[0];
    const b = stops[stops.length - 1];
    let cancelled = false;
    api
      .get(`/api/v1/routing/eta/?from=${a.lat},${a.lng}&to=${b.lat},${b.lng}`)
      .then(({ data }) => {
        if (!cancelled) setEta(data);
      })
      .catch((e) => {
        if (!cancelled) setErr(e?.response?.data?.detail || "ETA unavailable");
      });
    return () => {
      cancelled = true;
    };
  }, [stops]);

  if (stops.length < 2) return null;
  if (err)
    return (
      <div className="rounded-2xl border border-dashed border-border bg-muted px-4 py-3 text-xs text-ink-500">
        {err}
      </div>
    );
  if (!eta) return null;
  const hours = Math.floor(eta.duration_min_estimated / 60);
  const mins = eta.duration_min_estimated % 60;
  return (
    <div className="rounded-2xl border border-border bg-white px-4 py-3 text-xs shadow-soft">
      <p className="text-[10px] font-semibold uppercase tracking-kicker text-ink-500">
        Day drive · estimated
      </p>
      <p className="mt-1 text-sm font-semibold text-ink-900">
        {hours > 0 ? `${hours}h ` : ""}
        {mins}m · {eta.distance_km} km
      </p>
      <p className="text-[11px] text-ink-500">
        {eta.congestion_label} traffic between first and last stop
      </p>
    </div>
  );
}

// ─────────────────────────── Result view ───────────────────────────────
function ItineraryResult({
  itinerary,
  onStartOver,
}: {
  itinerary: Itinerary;
  onStartOver: () => void;
}) {
  const [openDay, setOpenDay] = useState<number>(itinerary.days[0]?.day_number ?? 1);
  return (
    <div className="container py-12 md:py-16">
      <div className="rounded-[2.5rem] bg-jade-900 p-10 text-white shadow-lift md:p-14">
        <span className="kicker text-saffron-300 before:bg-saffron-300/60">
          <Sparkles className="h-3 w-3" />
          Your trip is ready
        </span>
        <h1 className="display mt-4 text-4xl font-medium tracking-tightest text-white md:text-6xl">
          {itinerary.title}
        </h1>
        <p className="mt-4 text-sm text-white/75">
          {itinerary.start_date} → {itinerary.end_date} ·{" "}
          {itinerary.group_type} of {itinerary.group_size} ·{" "}
          {itinerary.days.length} day
          {itinerary.days.length === 1 ? "" : "s"}
        </p>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/itinerary/${itinerary.id}/pdf/`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full bg-saffron-400 px-5 py-2.5 text-sm font-semibold text-jade-900 transition-colors hover:bg-saffron-300"
          >
            <Download className="h-4 w-4" />
            Download PDF
          </a>
          <button
            onClick={() => navigator.clipboard?.writeText(itinerary.share_token)}
            className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-white/20"
          >
            <Share2 className="h-4 w-4" />
            Copy share token
          </button>
          <button
            onClick={onStartOver}
            className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white backdrop-blur transition-colors hover:bg-white/20"
          >
            Plan another
          </button>
          <code className="rounded-md bg-white/10 px-3 py-1 text-xs text-saffron-200">
            {itinerary.share_token}
          </code>
        </div>
      </div>

      {/* Day-by-day timeline */}
      <div className="mt-12 grid gap-6 lg:grid-cols-[260px_1fr]">
        <nav className="lg:sticky lg:top-28 lg:self-start">
          <ol className="flex flex-row gap-2 overflow-x-auto lg:flex-col lg:gap-1">
            {itinerary.days.map((d) => {
              const active = openDay === d.day_number;
              return (
                <li key={d.id}>
                  <button
                    onClick={() => setOpenDay(d.day_number)}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-2xl border px-4 py-3 text-left transition-all",
                      active
                        ? "border-jade-700 bg-jade-700 text-white shadow-glow"
                        : "border-border bg-white text-ink-700 hover:border-jade-300"
                    )}
                  >
                    <span className="display text-2xl font-medium">
                      {String(d.day_number).padStart(2, "0")}
                    </span>
                    <span className="flex-1">
                      <span className="block text-sm font-semibold">
                        {d.district_name ?? "Unassigned"}
                      </span>
                      <span
                        className={cn(
                          "text-[11px]",
                          active ? "text-white/75" : "text-ink-500"
                        )}
                      >
                        {d.stops.length} stop{d.stops.length === 1 ? "" : "s"}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
        </nav>

        <div className="space-y-6">
          {itinerary.days.map((d) => (
            <section
              key={d.id}
              className={cn(
                "rounded-3xl border bg-white p-6 transition-all md:p-8",
                openDay === d.day_number
                  ? "border-jade-700 shadow-lift"
                  : "border-border opacity-60"
              )}
            >
              <header className="mb-6 flex items-center justify-between gap-3">
                <div>
                  <span className="kicker">Day {d.day_number}</span>
                  <h3 className="display mt-1 text-3xl font-medium tracking-tightest text-ink-900">
                    {d.district_name ?? "Free day"}
                  </h3>
                </div>
                <span className="hidden text-xs uppercase tracking-kicker text-ink-500 md:inline">
                  {d.stops.length} stop{d.stops.length === 1 ? "" : "s"}
                </span>
              </header>
              {d.notes && (
                <p className="mb-6 rounded-2xl bg-jade-50 px-4 py-3 text-xs italic text-jade-800">
                  {d.notes}
                </p>
              )}
              {(() => {
                const stopsWithCoords = d.stops
                  .filter((s) => s.lat && s.lng)
                  .map((s) => ({
                    id: s.id,
                    name: s.name,
                    lat: Number(s.lat),
                    lng: Number(s.lng),
                  }));
                if (stopsWithCoords.length === 0) return null;
                return (
                  <div className="mb-6 grid gap-4 lg:grid-cols-[1fr_280px]">
                    <MapView stops={stopsWithCoords} height={280} zoom={9} />
                    <div className="space-y-3">
                      {d.district && <WeatherCard districtId={d.district} />}
                      <DayEta stops={stopsWithCoords} />
                    </div>
                  </div>
                );
              })()}
              <ol className="space-y-3">
                {d.stops.map((stop) => (
                  <li
                    key={stop.id}
                    className="group flex gap-4 rounded-2xl border border-border p-4 transition-colors hover:border-jade-300"
                  >
                    <div className="flex flex-col items-center">
                      <span className="display text-xl font-medium text-jade-700">
                        {stop.arrival_time?.slice(0, 5) ?? "—"}
                      </span>
                      <span className="my-1 h-full w-px flex-1 bg-jade-100" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-baseline justify-between gap-2">
                        <h4 className="text-base font-semibold text-ink-900">
                          {stop.name}
                        </h4>
                        <span className="text-[11px] uppercase tracking-kicker text-ink-500">
                          {stop.duration_mins ?? "?"} min
                        </span>
                      </div>
                      {stop.tip && (
                        <p className="mt-1 text-sm text-ink-600">{stop.tip}</p>
                      )}
                      <Link
                        href={`/explore/${stop.slug}`}
                        className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-jade-700 hover:text-jade-800"
                      >
                        View attraction →
                      </Link>
                    </div>
                  </li>
                ))}
              </ol>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
