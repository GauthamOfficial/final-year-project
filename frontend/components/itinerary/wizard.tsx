"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Loader2, MapPin, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { api, toApiError } from "@/lib/api";

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
  arrival_time: string | null;
  duration_mins: number | null;
  tip: string;
};

type Day = {
  id: number;
  day_number: number;
  district: number | null;
  district_name: string | null;
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

const INTERESTS = [
  { id: "beach", label: "Beach" },
  { id: "wildlife", label: "Wildlife" },
  { id: "cultural", label: "Cultural" },
  { id: "adventure", label: "Adventure" },
  { id: "food", label: "Food" },
  { id: "religious", label: "Religious" },
];

const GROUP_TYPES = [
  { id: "solo", label: "Solo" },
  { id: "couple", label: "Couple" },
  { id: "family", label: "Family" },
  { id: "group", label: "Group" },
];

const STEPS = ["dates", "budget", "interests", "districts", "group"] as const;
type Step = (typeof STEPS)[number];

function todayPlus(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

// ─────────────────────────── Component ──────────────────────────────────
export function ItineraryWizard() {
  const [step, setStep] = useState<Step>("dates");
  const [start, setStart] = useState(todayPlus(14));
  const [end, setEnd] = useState(todayPlus(20));
  const [budget, setBudget] = useState(50000);
  const [interests, setInterests] = useState<Set<string>>(new Set(["cultural"]));
  const [districtIds, setDistrictIds] = useState<Set<number>>(new Set());
  const [groupType, setGroupType] = useState("couple");
  const [groupSize, setGroupSize] = useState(2);

  const [districts, setDistricts] = useState<District[]>([]);
  const [districtError, setDistrictError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load districts on mount
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

  const stepIndex = STEPS.indexOf(step);
  const canPrev = stepIndex > 0;
  const canNext = stepIndex < STEPS.length - 1;
  const ready =
    interests.size > 0 && districtIds.size > 0 && start && end && start <= end;

  function next() {
    if (canNext) setStep(STEPS[stepIndex + 1]);
  }
  function prev() {
    if (canPrev) setStep(STEPS[stepIndex - 1]);
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
    } catch (err) {
      setError(toApiError(err).message);
    } finally {
      setSubmitting(false);
    }
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
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_280px]">
      <Card>
        <CardHeader>
          <CardTitle>Step {stepIndex + 1} of {STEPS.length}</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={step} onValueChange={(v) => setStep(v as Step)}>
            <TabsList className="mb-6 flex-wrap gap-1">
              <TabsTrigger value="dates">1 · Dates</TabsTrigger>
              <TabsTrigger value="budget">2 · Budget</TabsTrigger>
              <TabsTrigger value="interests">3 · Interests</TabsTrigger>
              <TabsTrigger value="districts">4 · Districts</TabsTrigger>
              <TabsTrigger value="group">5 · Group</TabsTrigger>
            </TabsList>

            <TabsContent value="dates">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Start date">
                  <Input
                    type="date"
                    value={start}
                    onChange={(e) => setStart(e.target.value)}
                  />
                </Field>
                <Field label="End date">
                  <Input
                    type="date"
                    value={end}
                    onChange={(e) => setEnd(e.target.value)}
                  />
                </Field>
              </div>
              <p className="mt-3 text-xs text-muted-foreground">
                Plan up to 30 days at a time.
              </p>
            </TabsContent>

            <TabsContent value="budget">
              <div className="space-y-4">
                <div className="flex items-end justify-between">
                  <span className="text-sm font-medium">Daily budget</span>
                  <span className="text-2xl font-semibold">
                    LKR {budget.toLocaleString()}
                  </span>
                </div>
                <Slider
                  value={budget}
                  min={5000}
                  max={500000}
                  step={1000}
                  onValueChange={setBudget}
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>LKR 5,000</span>
                  <span>LKR 500,000+</span>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="interests">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {INTERESTS.map((interest) => {
                  const checked = interests.has(interest.id);
                  return (
                    <label
                      key={interest.id}
                      className={`flex cursor-pointer items-center gap-2 rounded-md border p-3 text-sm transition-colors ${
                        checked
                          ? "border-primary bg-primary/5"
                          : "hover:bg-accent/10"
                      }`}
                    >
                      <Checkbox
                        checked={checked}
                        onCheckedChange={(c) => {
                          const next = new Set(interests);
                          if (c) next.add(interest.id);
                          else next.delete(interest.id);
                          setInterests(next);
                        }}
                      />
                      <span>{interest.label}</span>
                    </label>
                  );
                })}
              </div>
            </TabsContent>

            <TabsContent value="districts">
              {districtError ? (
                <Alert variant="danger">
                  <AlertTitle>Couldn&apos;t load districts</AlertTitle>
                  <AlertDescription>{districtError}</AlertDescription>
                </Alert>
              ) : (
                <div className="grid max-h-[420px] grid-cols-2 gap-2 overflow-y-auto pr-2 sm:grid-cols-3">
                  {districts.map((d) => {
                    const checked = districtIds.has(d.id);
                    return (
                      <label
                        key={d.id}
                        className={`flex cursor-pointer items-start gap-2 rounded-md border p-3 text-sm transition-colors ${
                          checked
                            ? "border-primary bg-primary/5"
                            : "hover:bg-accent/10"
                        }`}
                      >
                        <Checkbox
                          checked={checked}
                          onCheckedChange={(c) => {
                            const next = new Set(districtIds);
                            if (c) next.add(d.id);
                            else next.delete(d.id);
                            setDistrictIds(next);
                          }}
                        />
                        <div className="flex-1">
                          <div className="font-medium">{d.name}</div>
                          <div className="text-xs text-muted-foreground">
                            {d.province} · {d.attraction_count} attractions
                          </div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              )}
            </TabsContent>

            <TabsContent value="group">
              <div className="space-y-4">
                <Field label="Group type">
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                    {GROUP_TYPES.map((g) => (
                      <button
                        key={g.id}
                        type="button"
                        onClick={() => setGroupType(g.id)}
                        className={`rounded-md border px-3 py-2 text-sm transition-colors ${
                          groupType === g.id
                            ? "border-primary bg-primary/5 font-medium"
                            : "hover:bg-accent/10"
                        }`}
                      >
                        {g.label}
                      </button>
                    ))}
                  </div>
                </Field>
                <Field label="Group size">
                  <Input
                    type="number"
                    min={1}
                    max={50}
                    value={groupSize}
                    onChange={(e) => setGroupSize(Number(e.target.value) || 1)}
                  />
                </Field>
              </div>
            </TabsContent>
          </Tabs>

          <div className="mt-8 flex items-center justify-between">
            <Button variant="ghost" onClick={prev} disabled={!canPrev}>
              <ChevronLeft className="mr-1 h-4 w-4" /> Back
            </Button>
            {canNext ? (
              <Button onClick={next}>
                Next <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            ) : (
              <Button onClick={submit} disabled={!ready || submitting}>
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating…
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate itinerary
                  </>
                )}
              </Button>
            )}
          </div>
          {error && (
            <Alert variant="danger" className="mt-4">
              <AlertTitle>Generation failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Live preferences summary */}
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
    </div>
  );
}

// ─────────────────────────── Sub-components ─────────────────────────────
function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-1">
      <span className="text-sm font-medium">{label}</span>
      {children}
    </label>
  );
}

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
  interests: Set<string>;
  districtIds: Set<number>;
  districts: District[];
  groupType: string;
  groupSize: number;
}) {
  const days = useMemo(() => {
    const s = new Date(start);
    const e = new Date(end);
    return Math.max(1, Math.round((+e - +s) / (1000 * 60 * 60 * 24)) + 1);
  }, [start, end]);

  const districtsLabel = useMemo(() => {
    if (districtIds.size === 0) return "No districts selected";
    return districts
      .filter((d) => districtIds.has(d.id))
      .map((d) => d.name)
      .join(", ");
  }, [districtIds, districts]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <MapPin className="h-4 w-4 text-accent" />
          Trip summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <SummaryRow label="Duration" value={`${days} day${days === 1 ? "" : "s"}`} />
        <SummaryRow
          label="Daily budget"
          value={`LKR ${budget.toLocaleString()}`}
        />
        <SummaryRow
          label="Group"
          value={`${groupType} · ${groupSize}`}
        />
        <SummaryRow label="Districts" value={districtsLabel} />
        <div>
          <div className="mb-1 text-xs text-muted-foreground">Interests</div>
          <div className="flex flex-wrap gap-1">
            {Array.from(interests).length === 0 ? (
              <span className="text-xs text-muted-foreground">none</span>
            ) : (
              Array.from(interests).map((i) => (
                <Badge key={i} variant="secondary">
                  {i}
                </Badge>
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <span className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="text-right font-medium">{value}</span>
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
  return (
    <div className="space-y-6">
      <Alert variant="info">
        <AlertTitle>Itinerary ready</AlertTitle>
        <AlertDescription>
          Saved as <code>{itinerary.share_token}</code>. Share with travel partners
          using the read-only by-share endpoint.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>{itinerary.title}</span>
            <Button variant="outline" onClick={onStartOver} size="sm">
              Plan another
            </Button>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            {itinerary.start_date} → {itinerary.end_date} · {itinerary.group_type}
            {" · "}
            {itinerary.days.length} day{itinerary.days.length === 1 ? "" : "s"}
          </p>
        </CardHeader>
        <CardContent>
          <Accordion type="multiple" defaultValue={[`day-${itinerary.days[0]?.day_number}`]}>
            {itinerary.days.map((day) => (
              <AccordionItem key={day.id} value={`day-${day.day_number}`}>
                <AccordionTrigger>
                  <span className="flex items-center gap-2">
                    <Badge variant="amber">Day {day.day_number}</Badge>
                    <span className="font-medium">
                      {day.district_name ?? "Unassigned"}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {day.stops.length} stop{day.stops.length === 1 ? "" : "s"}
                    </span>
                  </span>
                </AccordionTrigger>
                <AccordionContent>
                  {day.notes && (
                    <p className="mb-3 text-xs italic text-muted-foreground">
                      {day.notes}
                    </p>
                  )}
                  <ul className="space-y-2">
                    {day.stops.map((stop) => (
                      <li
                        key={stop.id}
                        className="rounded-md border bg-card p-3 text-sm"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">
                            {stop.stop_order}. {stop.name}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {stop.arrival_time?.slice(0, 5) ?? "—"} ·{" "}
                            {stop.duration_mins ?? "?"} min
                          </span>
                        </div>
                        {stop.tip && (
                          <p className="mt-1 text-xs text-muted-foreground">
                            {stop.tip}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </CardContent>
      </Card>
    </div>
  );
}
