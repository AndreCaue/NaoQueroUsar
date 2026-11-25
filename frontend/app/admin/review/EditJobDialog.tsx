"use client";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type RefObject,
} from "react";

import { useToast } from "@/components/admin/ToastProvider";
import { X } from "@/components/admin/icons";
import {
  ApiError,
  generateInstagramSocialDraft,
  generateSocialDraft,
  getInstagramSocialDraft,
  getInstagramSocialStatus,
  getMetaIntegrationStatus,
  getSocialDraft,
  getSocialStatus,
  prepareInstagramMedia,
  retrySocialPost,
  saveInstagramSocialDraft,
  saveSocialDraft,
  updateJob,
  type InstagramMediaPrepareResponse,
  type JobAdmin,
  type JobUpdate,
  type MetaInstagramReadiness,
  type SocialPostDraft,
  type SocialPostStatusItem,
  type SocialPublishMode,
} from "@/lib/api";
import { buildAdminLoginHref } from "@/lib/adminReturnTo";
import { TOKEN_KEY } from "@/lib/auth";
import { CITY_OPTIONS, type CitySlug } from "@/lib/cities";

interface FormState {
  title: string;
  company: string;
  citySlug: CitySlug | "";
  salary: string;
  contact_email: string;
  contact_phone: string;
  activities: string;
  requirements: string;
  benefits: string;
}

type FormErrors = Partial<
  Record<"title" | "city" | "contact" | "email" | "phone", string>
>;

type SocialAction = "load" | "generate" | "save" | null;
type IgAction = "load" | "generate" | "save" | "prepare" | null;

const SITE_PUBLIC_URL_ERROR =
  "Link público indisponível: configure SITE_PUBLIC_URL no servidor para gerar o rascunho com link da vaga.";

function formatBrtDateTime(value: string | null | undefined): string | null {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  const parts = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(d);
  return parts;
}

function slugFromCanonical(canonical: string | null | undefined): CitySlug | "" {
  if (!canonical) return "";
  const target = fold(canonical);
  const match = CITY_OPTIONS.find(
    (option) => fold(option.canonical) === target || option.slug === target,
  );
  return match?.slug ?? "";
}

/** Case- and accent-insensitive comparison key. */
function fold(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function toFormState(job: JobAdmin | null): FormState {
  return {
    title: job?.title ?? "",
    company: job?.company ?? "",
    citySlug: slugFromCanonical(job?.city),
    salary: job?.salary ?? "",
    contact_email: job?.contact_email ?? "",
    contact_phone: job?.contact_phone ?? "",
    activities: job?.activities ?? "",
    requirements: job?.requirements ?? "",
    benefits: job?.benefits ?? "",
  };
}

function isoToBrtDateTime(iso: string | null | undefined): {
  date: string;
  time: string;
} {
  if (!iso) return { date: "", time: "" };
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return { date: "", time: "" };
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Sao_Paulo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(d);
  const get = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((p) => p.type === type)?.value ?? "";
  return {
    date: `${get("year")}-${get("month")}-${get("day")}`,
    time: `${get("hour")}:${get("minute")}`,
  };
}

function Field({
  label,
  value,
  onChange,
  error,
  placeholder,
  type = "text",
  disabled = false,
  maxLength,
  inputRef,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  placeholder?: string;
  type?: string;
  disabled?: boolean;
  maxLength?: number;
  inputRef?: RefObject<HTMLInputElement | null>;
}) {
  const id = `field-${label.toLowerCase().replace(/\s+/g, "-")}`;
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-[14px] text-fg-muted">
        {label}
      </label>
      <input
        id={id}
        ref={inputRef}
        type={type}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        maxLength={maxLength}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 w-full rounded-lg border border-line-strong bg-canvas px-3 text-base text-fg placeholder:text-fg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
      />
      {error ? (
        <p role="alert" className="mt-1 text-[14px] text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}

function Textarea({
  label,
  value,
  onChange,
  placeholder,
  disabled = false,
  maxLength,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  maxLength?: number;
}) {
  const id = `field-${label.toLowerCase().replace(/\s+/g, "-")}`;
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-[14px] text-fg-muted">
        {label}
      </label>
      <textarea
        id={id}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        maxLength={maxLength}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-24 w-full resize-y rounded-lg border border-line-strong bg-canvas px-3 py-2 text-base text-fg placeholder:text-fg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
      />
    </div>
  );
}

/** Read-only source snippet used for grounding during review (REVW-05). */
function SnippetPanel({ snippet }: { snippet: string | null }) {
  const hasSnippet = Boolean(snippet && snippet.trim());
  return (
    <div className="rounded-lg border border-line bg-canvas p-3">
      <h3 className="mb-2 text-[14px] font-semibold text-fg">Texto-fonte</h3>
      {hasSnippet ? (
        <pre className="max-h-[60vh] overflow-y-auto whitespace-pre-wrap text-[14px] leading-relaxed text-fg-muted [overflow-wrap:anywhere]">
          {snippet}
        </pre>
      ) : (
        <p className="text-[14px] italic text-fg-muted">
          Sem texto-fonte disponível
        </p>
      )}
    </div>
  );
}

export interface EditJobDialogProps {
  job: JobAdmin | null;
  token: string | null;
  open: boolean;
  onClose: () => void;
  onSaved: (job: JobAdmin) => void;
}

/**
 * EditJobDialog — modal de edição de vaga (REVW-03, REVW-05) + seção social (POST-03..06).
 */
export function EditJobDialog({
  job,
  token,
  open,
  onClose,
  onSaved,
}: EditJobDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleRef = useRef<HTMLInputElement>(null);
  const regenDialogRef = useRef<HTMLDialogElement>(null);
  const { toast } = useToast();
  const [form, setForm] = useState<FormState>(() => toFormState(job));
  const [errors, setErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);

  // Social draft state
  const [socialDraft, setSocialDraft] = useState<SocialPostDraft | null>(null);
  const [socialText, setSocialText] = useState("");
  const [socialPublishMode, setSocialPublishMode] =
    useState<SocialPublishMode>("publish_now");
  const [socialDate, setSocialDate] = useState("");
  const [socialTime, setSocialTime] = useState("");
  const [socialAction, setSocialAction] = useState<SocialAction>(null);
  const [socialLoadError, setSocialLoadError] = useState<string | null>(null);
  const [socialActionError, setSocialActionError] = useState<string | null>(null);
  const [socialFallbackWarning, setSocialFallbackWarning] = useState(false);
  const [socialSaved, setSocialSaved] = useState(false);
  const [showRegenConfirm, setShowRegenConfirm] = useState(false);
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [lastSavedSnapshot, setLastSavedSnapshot] = useState({
    text: "",
    publishMode: "publish_now" as SocialPublishMode,
    date: "",
    time: "",
  });

  // Social publication status (Phase 17)
  const [socialStatus, setSocialStatus] = useState<SocialPostStatusItem | null>(null);
  const [socialStatusLoading, setSocialStatusLoading] = useState(false);
  const [socialStatusError, setSocialStatusError] = useState<string | null>(null);
  const [retryingSocial, setRetryingSocial] = useState(false);
  const retryInFlightRef = useRef(false);
  const [retryingInstagram, setRetryingInstagram] = useState(false);
  const retryInstagramInFlightRef = useRef(false);

  // Instagram review state (Phase 30)
  const [igReadiness, setIgReadiness] = useState<MetaInstagramReadiness | null | undefined>(
    undefined,
  );
  const [igReadinessError, setIgReadinessError] = useState<string | null>(null);
  const [igEnabled, setIgEnabled] = useState(false);
  const [igDraft, setIgDraft] = useState<SocialPostDraft | null>(null);
  const [igCaption, setIgCaption] = useState("");
  const [igStatus, setIgStatus] = useState<SocialPostStatusItem | null>(null);
  const [igStatusLoading, setIgStatusLoading] = useState(false);
  const [igAction, setIgAction] = useState<IgAction>(null);
  const [igActionError, setIgActionError] = useState<string | null>(null);
  const [igLoadError, setIgLoadError] = useState<string | null>(null);
  const [igSaved, setIgSaved] = useState(false);
  const [igMedia, setIgMedia] = useState<InstagramMediaPrepareResponse | null>(null);
  const [igMediaLoading, setIgMediaLoading] = useState(false);
  const [igMediaError, setIgMediaError] = useState<string | null>(null);
  const igPrepareInFlightRef = useRef(false);

  const resetIgState = () => {
    setIgReadiness(undefined);
    setIgReadinessError(null);
    setIgEnabled(false);
    setIgDraft(null);
    setIgCaption("");
    setIgStatus(null);
    setIgStatusLoading(false);
    setIgAction(null);
    setIgActionError(null);
    setIgLoadError(null);
    setIgSaved(false);
    setIgMedia(null);
    setIgMediaLoading(false);
    setIgMediaError(null);
    igPrepareInFlightRef.current = false;
    setRetryingInstagram(false);
    retryInstagramInFlightRef.current = false;
  };

  const resetSocialState = () => {
    setSocialDraft(null);
    setSocialText("");
    setSocialPublishMode("publish_now");
    setSocialDate("");
    setSocialTime("");
    setSocialAction(null);
    setSocialLoadError(null);
    setSocialActionError(null);
    setSocialFallbackWarning(false);
    setSocialSaved(false);
    setShowRegenConfirm(false);
    setScheduleError(null);
    setLastSavedSnapshot({ text: "", publishMode: "publish_now", date: "", time: "" });
    setSocialStatus(null);
    setSocialStatusLoading(false);
    setSocialStatusError(null);
    setRetryingSocial(false);
    retryInFlightRef.current = false;
  };

  const applyDraft = (draft: SocialPostDraft | null) => {
    if (!draft) {
      resetSocialState();
      return;
    }
    const mode: SocialPublishMode =
      draft.publish_mode ?? (draft.scheduled_at ? "schedule" : "publish_now");
    const brt = isoToBrtDateTime(draft.scheduled_at);
    setSocialDraft(draft);
    setSocialText(draft.text ?? "");
    setSocialPublishMode(mode);
    setSocialDate(mode === "schedule" ? brt.date : "");
    setSocialTime(mode === "schedule" ? brt.time : "");
    setSocialSaved(Boolean(draft.saved));
    setSocialFallbackWarning(draft.origin === "template_fallback");
    setSocialActionError(null);
    setScheduleError(null);
    setLastSavedSnapshot({
      text: draft.text ?? "",
      publishMode: mode,
      date: mode === "schedule" ? brt.date : "",
      time: mode === "schedule" ? brt.time : "",
    });
  };

  // Reset on every open, not just when the object identity changes.
  useEffect(() => {
    if (!open) return;
    setForm(toFormState(job));
    setErrors({});
    resetSocialState();
    resetIgState();
  }, [job, open]);

  const handleAuthExpired = () => {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      // ignore
    }
    window.location.replace(
      buildAdminLoginHref(`${window.location.pathname}${window.location.search}`),
    );
  };

  const loadSocialStatus = async (jobId: string, authToken: string) => {
    setSocialStatusLoading(true);
    setSocialStatusError(null);
    try {
      const status = await getSocialStatus(authToken, jobId);
      setSocialStatus(status);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        handleAuthExpired();
        return;
      }
      setSocialStatusError(
        "Não foi possível carregar o status das publicações. Tente novamente em alguns instantes.",
      );
    } finally {
      setSocialStatusLoading(false);
    }
  };

  // Load social draft and status when dialog opens for a job.
  useEffect(() => {
    if (!open || !job || !token) return;
    let cancelled = false;
    setSocialAction("load");
    setSocialLoadError(null);
    setSocialStatusLoading(true);
    setSocialStatusError(null);

    Promise.all([
      getSocialDraft(token, job.id)
        .then((draft) => {
          if (!cancelled) applyDraft(draft);
        })
        .catch((err) => {
          if (cancelled) return;
          if (err instanceof ApiError && err.status === 401) {
            handleAuthExpired();
            return;
          }
          const message =
            err instanceof ApiError
              ? err.message
              : "Não foi possível carregar o rascunho social.";
          setSocialLoadError(message);
        }),
      getSocialStatus(token, job.id)
        .then((status) => {
          if (!cancelled) setSocialStatus(status);
        })
        .catch((err) => {
          if (cancelled) return;
          if (err instanceof ApiError && err.status === 401) {
            handleAuthExpired();
            return;
          }
          setSocialStatusError(
            "Não foi possível carregar o status das publicações. Tente novamente em alguns instantes.",
          );
        }),
    ]).finally(() => {
      if (!cancelled) {
        setSocialAction(null);
        setSocialStatusLoading(false);
      }
    });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, job?.id, token]);

  const prepareIgMedia = async (authToken: string, jobId: string) => {
    if (igPrepareInFlightRef.current) return;
    igPrepareInFlightRef.current = true;
    setIgMediaLoading(true);
    setIgMediaError(null);
    try {
      const media = await prepareInstagramMedia(authToken, jobId);
      setIgMedia(media);
      if (!media.validation?.valid) {
        setIgMediaError(
          media.validation?.message ??
            "A imagem do Instagram é inválida ou não está disponível. Corrija antes de publicar no Instagram.",
        );
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        handleAuthExpired();
        return;
      }
      setIgMedia(null);
      setIgMediaError("Não foi possível preparar a imagem do Instagram. Tente novamente.");
    } finally {
      setIgMediaLoading(false);
      igPrepareInFlightRef.current = false;
    }
  };

  // Load Instagram readiness/draft/status when dialog opens.
  useEffect(() => {
    if (!open || !job || !token) return;
    let cancelled = false;
    setIgAction("load");
    setIgLoadError(null);
    setIgReadinessError(null);
    setIgStatusLoading(true);

    Promise.all([
      getMetaIntegrationStatus(token)
        .then((status) => {
          if (cancelled) return;
          setIgReadiness(status.instagram ?? null);
        })
        .catch((err) => {
          if (cancelled) return;
          if (err instanceof ApiError && err.status === 401) {
            handleAuthExpired();
            return;
          }
          setIgReadiness(null);
          setIgReadinessError(
            "Não foi possível carregar a prontidão do Instagram. Tente novamente em alguns instantes.",
          );
        }),
      getInstagramSocialDraft(token, job.id)
        .then((draft) => {
          if (cancelled) return;
          if (draft) {
            setIgDraft(draft);
            setIgCaption(draft.text ?? "");
            setIgEnabled(Boolean(draft.publish_enabled));
            setIgSaved(Boolean(draft.saved));
          } else {
            setIgDraft(null);
            setIgCaption("");
            setIgEnabled(false);
            setIgSaved(false);
          }
        })
        .catch((err) => {
          if (cancelled) return;
          if (err instanceof ApiError && err.status === 401) {
            handleAuthExpired();
            return;
          }
          setIgLoadError(
            err instanceof ApiError
              ? err.message
              : "Não foi possível carregar o rascunho do Instagram.",
          );
        }),
      getInstagramSocialStatus(token, job.id)
        .then((status) => {
          if (cancelled) return;
          setIgStatus(status);
        })
        .catch((err) => {
          if (cancelled) return;
          if (err instanceof ApiError && err.status === 401) {
            handleAuthExpired();
            return;
          }
          setIgStatus(null);
        }),
    ]).finally(() => {
      if (cancelled) return;
      setIgAction(null);
      setIgStatusLoading(false);
    });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, job?.id, token]);

  // D-06: auto-prepare when dialog opens with IG enabled+ready, or when toggled on.
  useEffect(() => {
    if (!open || !job || !token) return;
    if (!igEnabled) return;
    if (igReadiness?.state !== "ready") return;
    if (igMedia || igMediaLoading || igPrepareInFlightRef.current) return;
    void prepareIgMedia(token, job.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, job?.id, token, igEnabled, igReadiness?.state]);

  const handleRetrySocial = async () => {
    if (!token || !job || !socialStatus?.can_retry) return;
    if (retryInFlightRef.current) return;
    retryInFlightRef.current = true;
    setRetryingSocial(true);
    try {
      const res = await retrySocialPost(token, job.id);
      const item = res.item ?? (await getSocialStatus(token, job.id));
      if (item) setSocialStatus(item);
      const outcome = res.outcome;
      if (outcome === "noop" || outcome === "not_eligible") {
        toast(res.message || "Nenhuma nova tentativa foi necessária. Status atualizado.", "success");
      } else {
        toast(res.message || "Nova tentativa iniciada.", "success");
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        handleAuthExpired();
        return;
      }
      toast(
        "Não foi possível iniciar a nova tentativa. Tente novamente em alguns instantes.",
        "error",
      );
      await loadSocialStatus(job.id, token);
    } finally {
      setRetryingSocial(false);
      retryInFlightRef.current = false;
    }
  };

  const handleRetryInstagram = async () => {
    if (!token || !job || !igStatus?.can_retry) return;
    if (retryInstagramInFlightRef.current) return;
    retryInstagramInFlightRef.current = true;
    setRetryingInstagram(true);
    try {
      const res = await retrySocialPost(token, job.id, "instagram");
      const item = res.item ?? (await getInstagramSocialStatus(token, job.id));
      if (item) setIgStatus(item);
      const outcome = res.outcome;
      if (outcome === "noop" || outcome === "not_eligible") {
        toast(res.message || "Nenhuma nova tentativa foi necessária. Status atualizado.", "success");
      } else {
        toast(res.message || "Nova tentativa iniciada.", "success");
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        handleAuthExpired();
        return;
      }
      toast(
        "Não foi possível iniciar a nova tentativa. Tente novamente em alguns instantes.",
        "error",
      );
      try {
        const refreshed = await getInstagramSocialStatus(token, job.id);
        if (refreshed) setIgStatus(refreshed);
      } catch {
        // ignore refresh failure; status card keeps last known state
      }
    } finally {
      setRetryingInstagram(false);
      retryInstagramInFlightRef.current = false;
    }
  };

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      titleRef.current?.focus();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  // Lock document scroll while open.
  useEffect(() => {
    if (!open) return;
    const root = document.documentElement;
    const previous = root.style.overflow;
    root.style.overflow = "hidden";
    return () => {
      root.style.overflow = previous;
    };
  }, [open]);

  // Regen confirm dialog control
  useEffect(() => {
    const dialog = regenDialogRef.current;
    if (!dialog) return;
    if (showRegenConfirm && !dialog.open) {
      dialog.showModal();
    } else if (!showRegenConfirm && dialog.open) {
      dialog.close();
    }
  }, [showRegenConfirm]);

  const frozen = Boolean(socialDraft?.frozen || (socialDraft && socialDraft.status !== "draft"));
  const busy = socialAction !== null;
  const siteUrlIssue = /SITE_PUBLIC_URL|Link público indisponível/i.test(
    `${socialActionError ?? ""} ${socialLoadError ?? ""}`,
  );

  const hasSocialDraftContent = socialText.trim().length > 0 || socialDraft !== null;
  const isDirty = useMemo(() => {
    if (!socialDraft && !hasSocialDraftContent) return false;
    return (
      socialText !== lastSavedSnapshot.text ||
      socialPublishMode !== lastSavedSnapshot.publishMode ||
      socialDate !== lastSavedSnapshot.date ||
      socialTime !== lastSavedSnapshot.time
    );
  }, [
    socialDraft,
    hasSocialDraftContent,
    socialText,
    socialPublishMode,
    socialDate,
    socialTime,
    lastSavedSnapshot,
  ]);

  const countHashtags = (text: string) => (text.match(/(?:^|\s)#[^\s#]+/g) ?? []).length;
  const igCharCount = igCaption.length;
  const igOverLimit = igCharCount > 2200;
  const igHashtagCount = countHashtags(igCaption);
  const igHashtagWarning = igHashtagCount > 30;
  const igReady = igReadiness?.state === "ready";
  const igFrozen = Boolean(igDraft?.frozen || (igDraft && igDraft.status !== "draft"));
  const igImageInvalid = igEnabled && (!igMedia || !igMedia.validation?.valid || !igMedia.image_url);
  const igBusy = igAction !== null;
  const igCanSave = igReady && igEnabled && !igOverLimit && !igImageInvalid && !busy && !igFrozen && !igBusy;

  const close = () => {
    if (showRegenConfirm) return;
    dialogRef.current?.close();
  };

  const validate = (): boolean => {
    const next: FormErrors = {};
    if (!form.title.trim()) next.title = "Título é obrigatório.";
    if (!form.citySlug && !job?.city) next.city = "Selecione uma cidade.";
    const email = form.contact_email.trim();
    const phone = form.contact_phone.trim();
    if (!email && !phone) {
      next.contact = "Informe ao menos um contato (e-mail ou telefone).";
    }
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      next.email = "E-mail inválido.";
    }
    if (phone && phone.replace(/\D/g, "").length < 8) {
      next.phone = "Telefone inválido.";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (saving || !job) return;
    if (!validate()) return;

    if (!token) {
      toast("Sessão expirada. Entre novamente.", "error");
      return;
    }

    const canonicalCity =
      CITY_OPTIONS.find((option) => option.slug === form.citySlug)?.canonical ??
      job.city;

    const payload: JobUpdate = {
      title: form.title.trim(),
      company: form.company.trim() || null,
      city: canonicalCity,
      salary: form.salary.trim() || null,
      contact_email: form.contact_email.trim() || null,
      contact_phone: form.contact_phone.trim() || null,
      activities: form.activities.trim() || null,
      requirements: form.requirements.trim() || null,
      benefits: form.benefits.trim() || null,
    };

    setSaving(true);
    try {
      const updated = await updateJob(token, job.id, payload);
      toast("Vaga atualizada.", "success");
      onSaved(updated);
      close();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao salvar";
      toast(`Erro: ${message}`, "error");
    } finally {
      setSaving(false);
    }
  };

  const buildSocialPayload = () => ({
    publish_mode: socialPublishMode,
    ...(socialPublishMode === "schedule"
      ? { scheduled_date: socialDate, scheduled_time: socialTime }
      : {}),
  });

  const validateSchedule = (): boolean => {
    if (socialPublishMode !== "schedule") {
      setScheduleError(null);
      return true;
    }
    if (!socialDate || !socialTime) {
      setScheduleError("Escolha uma data e hora válidas para agendar.");
      return false;
    }
    const parsed = new Date(`${socialDate}T${socialTime}:00`);
    if (Number.isNaN(parsed.getTime())) {
      setScheduleError("Escolha uma data e hora válidas para agendar.");
      return false;
    }
    setScheduleError(null);
    return true;
  };

  const handleGenerate = async (isRegenerate: boolean) => {
    if (!token || !job || frozen || busy) return;
    if (isRegenerate) {
      setShowRegenConfirm(false);
    }
    if (!validateSchedule()) return;
    setSocialAction("generate");
    setSocialActionError(null);
    setSocialFallbackWarning(false);
    try {
      const draft = await generateSocialDraft(token, job.id, buildSocialPayload());
      applyDraft(draft);
      if (draft.origin === "template_fallback") {
        setSocialFallbackWarning(true);
      }
      setSocialSaved(Boolean(draft.saved));
    } catch (err) {
      const raw = err instanceof ApiError ? err.message : "Não foi possível gerar o rascunho.";
      const message =
        raw.includes("SITE_PUBLIC_URL") || raw.includes("Link público indisponível")
          ? SITE_PUBLIC_URL_ERROR
          : raw;
      setSocialActionError(message);
      if (/SITE_PUBLIC_URL|Link público indisponível/i.test(raw)) {
        setSocialActionError(SITE_PUBLIC_URL_ERROR);
      }
      if (!/SITE_PUBLIC_URL|Link público indisponível/i.test(message)) {
        toast(`Erro: ${message}`, "error");
      }
    } finally {
      setSocialAction(null);
    }
  };

  const handleSaveDraft = async () => {
    if (!token || !job || frozen || busy) return;
    if (!validateSchedule()) return;
    if (!socialText.trim()) {
      setSocialActionError("Texto do rascunho é obrigatório.");
      return;
    }
    setSocialAction("save");
    setSocialActionError(null);
    try {
      const draft = await saveSocialDraft(token, job.id, {
        ...buildSocialPayload(),
        text: socialText,
      });
      applyDraft(draft);
      setSocialSaved(true);
      toast("Rascunho salvo.", "success");
    } catch (err) {
      const raw = err instanceof ApiError ? err.message : "Não foi possível salvar o rascunho.";
      const message =
        raw.includes("SITE_PUBLIC_URL") || raw.includes("Link público indisponível")
          ? SITE_PUBLIC_URL_ERROR
          : raw;
      setSocialActionError(message);
      toast(`Erro: ${message}`, "error");
    } finally {
      setSocialAction(null);
    }
  };

  const handleIgGenerate = async (publishEnabledOverride?: boolean) => {
    if (!token || !job || !igReady || igFrozen || busy || igBusy) return;
    const publishEnabled = publishEnabledOverride ?? igEnabled;
    setIgAction("generate");
    setIgActionError(null);
    try {
      const draft = await generateInstagramSocialDraft(token, job.id, {
        publish_mode: "publish_now",
        publish_enabled: publishEnabled,
      });
      setIgDraft(draft);
      setIgCaption(draft.text ?? "");
      setIgEnabled(Boolean(draft.publish_enabled));
      setIgSaved(Boolean(draft.saved));
      if (draft.publish_enabled) {
        await prepareIgMedia(token, job.id);
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        handleAuthExpired();
        return;
      }
      setIgActionError(
        err instanceof ApiError
          ? err.message
          : "Não foi possível gerar a legenda do Instagram.",
      );
    } finally {
      setIgAction(null);
    }
  };

  const handleIgSave = async () => {
    if (!token || !job || !igReady || igFrozen || busy || igBusy) return;
    if (igOverLimit) {
      setIgActionError("A legenda do Instagram deve ter no máximo 2200 caracteres.");
      return;
    }
    if (igEnabled && igImageInvalid) {
      setIgActionError(
        "Corrija a legenda ou a imagem do Instagram antes de salvar/publicar com Instagram ativado. O Facebook e o site não são bloqueados.",
      );
      return;
    }
    setIgAction("save");
    setIgActionError(null);
    try {
      const draft = await saveInstagramSocialDraft(token, job.id, {
        text: igCaption,
        publish_mode: "publish_now",
        publish_enabled: igEnabled,
      });
      setIgDraft(draft);
      setIgCaption(draft.text ?? "");
      setIgEnabled(Boolean(draft.publish_enabled));
      setIgSaved(Boolean(draft.saved));
      toast("Rascunho salvo.", "success");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        handleAuthExpired();
        return;
      }
      setIgActionError(
        err instanceof ApiError
          ? err.message
          : "Não foi possível salvar o rascunho do Instagram.",
      );
    } finally {
      setIgAction(null);
    }
  };

  const handleIgToggle = async (nextEnabled: boolean) => {
    if (!token || !job || !igReady || igFrozen || busy || igBusy) return;
    setIgActionError(null);

    if (nextEnabled) {
      setIgEnabled(true);
      setIgSaved(false);
      if (!igDraft && !igCaption.trim()) {
        await handleIgGenerate(true);
        return;
      }
      if (igDraft) {
        setIgAction("save");
        try {
          const draft = await saveInstagramSocialDraft(token, job.id, {
            text: igCaption || igDraft.text,
            publish_mode: "publish_now",
            publish_enabled: true,
          });
          setIgDraft(draft);
          setIgCaption(draft.text ?? "");
          setIgEnabled(Boolean(draft.publish_enabled));
          setIgSaved(Boolean(draft.saved));
        } catch (err) {
          if (err instanceof ApiError && err.status === 401) {
            handleAuthExpired();
            return;
          }
          setIgEnabled(false);
          setIgActionError(
            err instanceof ApiError
              ? err.message
              : "Não foi possível ativar a publicação no Instagram.",
          );
          return;
        } finally {
          setIgAction(null);
        }
      }
      if (!igMedia && !igMediaLoading && !igPrepareInFlightRef.current) {
        void prepareIgMedia(token, job.id);
      }
      return;
    }

    // Toggle off: persist durably when draft exists (D-04/Plan 30-02 Task 2)
    setIgEnabled(false);
    setIgSaved(false);
    setIgMedia(null);
    setIgMediaError(null);
    if (igDraft) {
      setIgAction("save");
      try {
        const draft = await saveInstagramSocialDraft(token, job.id, {
          text: igCaption || igDraft.text,
          publish_mode: "publish_now",
          publish_enabled: false,
        });
        setIgDraft(draft);
        setIgCaption(draft.text ?? "");
        setIgEnabled(Boolean(draft.publish_enabled));
        setIgSaved(Boolean(draft.saved));
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          handleAuthExpired();
          return;
        }
        setIgEnabled(true);
        setIgActionError(
          err instanceof ApiError
            ? err.message
            : "Não foi possível desativar a publicação no Instagram. Tente novamente.",
        );
      } finally {
        setIgAction(null);
      }
    }
  };

  const previewLinkBase =
    (process.env.NEXT_PUBLIC_SITE_PUBLIC_URL ||
      process.env.NEXT_PUBLIC_PUBLIC_SITE_URL ||
      "").replace(/\/+$/, "");
  const previewLink = job
    ? previewLinkBase
      ? `${previewLinkBase}/?vaga=${job.id}`
      : `/?vaga=${job.id}`
    : "";

  const originChip =
    socialDraft?.origin === "llm"
      ? "Gerado por IA"
      : socialDraft?.origin === "template_fallback"
        ? "Modelo padrão (fallback)"
        : null;

  const controlsDisabled = frozen || busy || socialAction === "load";
  const generateLabel = hasSocialDraftContent && socialDraft ? "Regenerar com IA" : "Gerar rascunho";
  const isGenerating = socialAction === "generate";
  const isSaving = socialAction === "save";

  return (
    <>
      <dialog
        ref={dialogRef}
        tabIndex={-1}
        aria-labelledby="edit-job-title"
        onClose={onClose}
        onCancel={(event) => {
          if (saving || showRegenConfirm) event.preventDefault();
        }}
        onClick={(event) => {
          if (saving || showRegenConfirm) return;
          if (event.target === dialogRef.current) close();
        }}
        className="mb-0 mt-auto max-h-[92dvh] w-full max-w-none flex-col overflow-hidden rounded-t-[16px] border-0 bg-surface p-0 pb-[env(safe-area-inset-bottom)] text-fg backdrop:bg-[rgba(5,2,12,.72)] open:flex sm:mb-auto sm:mt-auto sm:max-h-[88dvh] sm:max-w-[880px] sm:rounded-[16px]"
      >
        <header className="shrink-0 border-b border-line bg-surface px-4 pb-3 pt-2 sm:px-6 sm:pt-4">
          <div
            aria-hidden="true"
            className="mx-auto mb-2 h-1 w-8 rounded-full bg-line-strong sm:hidden"
          />
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <h2
                id="edit-job-title"
                className="text-xl font-semibold leading-tight [overflow-wrap:anywhere]"
              >
                Editar vaga
              </h2>
              {job ? (
                <p className="mt-1 truncate text-sm text-fg-muted">{job.title}</p>
              ) : null}
            </div>
            <button
              type="button"
              aria-label="Fechar"
              onClick={close}
              disabled={saving || showRegenConfirm}
              className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-fg-muted transition-colors hover:bg-[rgba(167,139,250,0.08)] hover:text-fg disabled:opacity-50"
            >
              <X size={20} />
            </button>
          </div>
        </header>

        <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
          <div className="grid min-h-0 flex-1 gap-6 overflow-y-auto overscroll-contain p-4 sm:p-6 md:grid-cols-[minmax(0,1fr)_320px]">
            <div className="space-y-4">
              <Field
                label="Título"
                value={form.title}
                inputRef={titleRef}
                maxLength={200}
                onChange={(value) => setForm((prev) => ({ ...prev, title: value }))}
                error={errors.title}
                placeholder="Título da vaga"
                disabled={saving}
              />
              <Field
                label="Empresa"
                value={form.company}
                maxLength={150}
                onChange={(value) => setForm((prev) => ({ ...prev, company: value }))}
                placeholder="Nome da empresa (opcional)"
                disabled={saving}
              />

              <div>
                <label
                  htmlFor="field-cidade"
                  className="mb-1 block text-[14px] text-fg-muted"
                >
                  Cidade
                </label>
                <select
                  id="field-cidade"
                  value={form.citySlug}
                  disabled={saving}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      citySlug: event.target.value as CitySlug | "",
                    }))
                  }
                  className="min-h-11 w-full rounded-lg border border-line-strong bg-canvas px-3 text-base text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">Selecione uma cidade</option>
                  {CITY_OPTIONS.map((option) => (
                    <option key={option.slug} value={option.slug}>
                      {option.label}
                    </option>
                  ))}
                </select>
                {errors.city ? (
                  <p role="alert" className="mt-1 text-[14px] text-danger">
                    {errors.city}
                  </p>
                ) : null}
              </div>

              <Field
                label="Salário"
                value={form.salary}
                maxLength={80}
                onChange={(value) => setForm((prev) => ({ ...prev, salary: value }))}
                placeholder="Ex.: R$ 2.500 ou A combinar"
                disabled={saving}
              />
              <Field
                label="E-mail de contato"
                value={form.contact_email}
                maxLength={254}
                onChange={(value) =>
                  setForm((prev) => ({ ...prev, contact_email: value }))
                }
                error={errors.email ?? errors.contact}
                placeholder="contato@empresa.com"
                type="email"
                disabled={saving}
              />
              <Field
                label="Telefone de contato"
                value={form.contact_phone}
                maxLength={30}
                onChange={(value) =>
                  setForm((prev) => ({ ...prev, contact_phone: value }))
                }
                error={errors.phone}
                placeholder="+55 11 99999-9999"
                type="tel"
                disabled={saving}
              />
              <Textarea
                label="Atividades"
                value={form.activities}
                onChange={(value) =>
                  setForm((prev) => ({ ...prev, activities: value }))
                }
                placeholder="Descreva as atividades"
                disabled={saving}
              />
              <Textarea
                label="Requisitos"
                value={form.requirements}
                onChange={(value) =>
                  setForm((prev) => ({ ...prev, requirements: value }))
                }
                placeholder="Requisitos (opcional)"
                disabled={saving}
              />
              <Textarea
                label="Benefícios"
                value={form.benefits}
                maxLength={255}
                onChange={(value) =>
                  setForm((prev) => ({ ...prev, benefits: value }))
                }
                placeholder="Benefícios (opcional)"
                disabled={saving}
              />

              <details className="rounded-lg border border-line p-3 md:hidden">
                <summary className="cursor-pointer text-[14px] font-semibold text-fg">
                  Texto-fonte
                </summary>
                <div className="mt-3">
                  <SnippetPanel snippet={job?.source_snippet ?? null} />
                </div>
              </details>

              {/* Post para Facebook */}
              <section className="mt-6 border-t border-line pt-6">
                <h3 className="text-[20px] font-semibold leading-tight text-fg">
                  Post para Facebook
                </h3>

                <div className="mt-4 rounded-lg border border-line bg-canvas p-4">
                  <h4 className="text-[16px] font-semibold text-fg">
                    Status da publicação no Facebook
                  </h4>

                  {socialStatusLoading ? (
                    <p className="mt-2 text-[14px] text-fg-muted">Carregando...</p>
                  ) : socialStatusError ? (
                    <p role="alert" className="mt-2 text-[14px] text-danger-soft">
                      {socialStatusError}
                    </p>
                  ) : !socialStatus ? (
                    <div className="mt-2 space-y-2">
                      <span className="inline-flex items-center rounded-full border border-line bg-canvas px-3 py-1 text-[14px] text-fg-muted">
                        Sem rascunho
                      </span>
                      <p className="text-[14px] text-fg-muted">
                        Nenhum post social registrado para esta vaga.
                      </p>
                    </div>
                  ) : (
                    <div className="mt-2 space-y-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-[14px] ${
                            socialStatus.status === "failed"
                              ? "border border-danger bg-[rgba(248,113,113,0.12)] text-danger-soft"
                              : socialStatus.status === "published"
                                ? "border border-accent bg-[rgba(139,92,246,0.12)] text-fg"
                                : socialStatus.status === "publishing"
                                  ? "border border-accent/40 bg-[rgba(139,92,246,0.08)] text-fg"
                                  : socialStatus.status === "scheduled"
                                    ? "border border-accent/40 bg-[rgba(139,92,246,0.08)] text-fg"
                                    : "border border-line bg-canvas text-fg-muted"
                          }`}
                        >
                          {socialStatus.status === "publishing" ? (
                            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-accent-soft border-t-transparent" aria-hidden="true" />
                          ) : null}
                          {socialStatus.status_label}
                        </span>
                      </div>

                      {socialStatus.status === "scheduled" ? (
                        <p className="text-[14px] text-fg-muted">
                          {socialStatus.scheduled_at
                            ? `Publicação agendada para ${formatBrtDateTime(socialStatus.scheduled_at)} (America/Sao_Paulo).`
                            : "Publicação agendada."}
                        </p>
                      ) : null}

                      {socialStatus.status === "publishing" ? (
                        <p className="text-[14px] text-fg-muted">
                          Publicação em andamento. Atualize em instantes para ver o resultado.
                        </p>
                      ) : null}

                      {socialStatus.status === "published" ? (
                        <div className="space-y-1">
                          <p className="text-[14px] text-fg">Publicado no Facebook.</p>
                          {socialStatus.published_url ? (
                            <a
                              href={socialStatus.published_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex min-h-11 items-center text-[14px] font-medium text-accent-soft underline-offset-4 hover:text-accent hover:underline"
                            >
                              Ver post no Facebook
                            </a>
                          ) : (
                            <p className="text-[14px] text-fg-muted">
                              Publicado no Facebook. Link indisponível.
                            </p>
                          )}
                        </div>
                      ) : null}

                      {socialStatus.status === "failed" ? (
                        <p className="text-[14px] text-danger-soft">
                          {socialStatus.last_error ||
                            "Não foi possível publicar este post. Tente novamente quando estiver disponível."}
                        </p>
                      ) : null}

                      {socialStatus.status !== "failed" &&
                      socialStatus.status !== "published" &&
                      socialStatus.status !== "publishing" &&
                      socialStatus.status !== "scheduled" &&
                      socialStatus.status === "draft" ? (
                        <p className="text-[14px] text-fg-muted">
                          Rascunho salvo. Aprove a vaga para agendar ou publicar.
                        </p>
                      ) : null}

                      {socialStatus.retry_block_reason ? (
                        <p className="text-[14px] text-fg-muted">
                          {socialStatus.retry_block_reason}
                        </p>
                      ) : null}

                      {socialStatus.retry_block_reason &&
                      /reconect/i.test(socialStatus.retry_block_reason) ? (
                        <a
                          href="/admin/integracoes"
                          className="inline-flex min-h-11 items-center rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft"
                        >
                          Abrir Integrações
                        </a>
                      ) : null}

                      {socialStatus.can_retry ? (
                        <button
                          type="button"
                          onClick={() => void handleRetrySocial()}
                          disabled={retryingSocial}
                          className="inline-flex min-h-11 items-center justify-center rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover disabled:opacity-50"
                        >
                          {retryingSocial ? "Tentando novamente..." : "Tentar novamente"}
                        </button>
                      ) : null}
                    </div>
                  )}
                </div>

                {socialAction === "load" ? (
                  <p className="mt-3 text-[14px] text-fg-muted">Carregando rascunho...</p>
                ) : null}

                {socialLoadError ? (
                  <p role="alert" className="mt-3 text-[14px] text-danger-soft">
                    {socialLoadError}
                  </p>
                ) : null}

                {!hasSocialDraftContent && socialAction !== "load" ? (
                  <div className="mt-4 rounded-lg border border-line bg-canvas p-4">
                    <h4 className="text-[16px] font-semibold text-fg">Nenhum rascunho gerado</h4>
                    <p className="mt-2 text-[14px] text-fg-muted">
                      Gere um rascunho com IA para revisar o texto antes de aprovar. Se a IA falhar, um modelo padrão será usado.
                    </p>
                    <button
                      type="button"
                      onClick={() => void handleGenerate(false)}
                      disabled={controlsDisabled || !token}
                      className="mt-4 min-h-11 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover disabled:opacity-50"
                    >
                      {isGenerating ? "Gerando rascunho..." : "Gerar rascunho"}
                    </button>
                  </div>
                ) : null}

                {hasSocialDraftContent ? (
                  <div className="mt-4 space-y-4">
                    <div className="flex flex-wrap gap-2">
                      {originChip ? (
                        <span className="rounded-full border border-line bg-canvas px-3 py-1 text-[14px] text-fg-muted">
                          {originChip}
                        </span>
                      ) : null}
                      {socialSaved && !isDirty ? (
                        <span className="rounded-full border border-line bg-canvas px-3 py-1 text-[14px] text-fg-muted">
                          Rascunho salvo
                        </span>
                      ) : null}
                      {isDirty ? (
                        <span className="rounded-full border border-line bg-canvas px-3 py-1 text-[14px] text-fg-muted">
                          Alterações não salvas
                        </span>
                      ) : null}
                      {frozen ? (
                        <span className="rounded-full border border-line bg-canvas px-3 py-1 text-[14px] text-fg-muted">
                          Texto bloqueado após aprovação
                        </span>
                      ) : null}
                    </div>

                    {socialFallbackWarning || socialDraft?.origin === "template_fallback" ? (
                      <p className="rounded-lg border border-accent bg-[rgba(139,92,246,0.12)] p-3 text-[14px] text-fg">
                        Não foi possível gerar com IA. Usamos um modelo padrão — revise o texto antes de aprovar.
                      </p>
                    ) : null}

                    {frozen ? (
                      <p className="rounded-lg border border-accent bg-[rgba(139,92,246,0.12)] p-3 text-[14px] text-fg">
                        Texto aprovado e bloqueado para envio. Este conteúdo não pode ser editado.
                      </p>
                    ) : null}

                    {siteUrlIssue ? (
                      <p role="alert" className="text-[14px] text-danger-soft">
                        {SITE_PUBLIC_URL_ERROR}
                      </p>
                    ) : socialActionError ? (
                      <p role="alert" className="text-[14px] text-danger-soft">
                        {socialActionError}
                      </p>
                    ) : null}

                    <div>
                      <label
                        htmlFor="social-post-text"
                        className="mb-1 block text-[14px] font-semibold text-fg"
                      >
                        Texto do post
                      </label>
                      <textarea
                        id="social-post-text"
                        value={socialText}
                        disabled={controlsDisabled}
                        onChange={(e) => {
                          setSocialText(e.target.value);
                          setSocialSaved(false);
                          setSocialActionError(null);
                        }}
                        className="min-h-40 w-full resize-y rounded-lg border border-line-strong bg-canvas px-3 py-2 text-base text-fg placeholder:text-fg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
                      />
                      <div className="mt-1 flex flex-wrap items-center justify-between gap-2 text-[14px]">
                        <span className="text-fg-muted">Meta: até ~700 caracteres.</span>
                        <span
                          className={socialText.length > 700 ? "text-danger-soft" : "text-fg-muted"}
                        >
                          {socialText.length}/700 caracteres
                        </span>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <p className="text-[14px] font-semibold text-fg">Modo de publicação</p>
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          disabled={controlsDisabled}
                          onClick={() => setSocialPublishMode("publish_now")}
                          className={`min-h-11 rounded-lg border px-4 text-sm font-semibold transition-colors disabled:opacity-50 ${
                            socialPublishMode === "publish_now"
                              ? "border-accent bg-accent-strong text-white"
                              : "border-line-strong bg-canvas text-fg"
                          }`}
                        >
                          Publicar agora
                        </button>
                        <button
                          type="button"
                          disabled={controlsDisabled}
                          onClick={() => setSocialPublishMode("schedule")}
                          className={`min-h-11 rounded-lg border px-4 text-sm font-semibold transition-colors disabled:opacity-50 ${
                            socialPublishMode === "schedule"
                              ? "border-accent bg-accent-strong text-white"
                              : "border-line-strong bg-canvas text-fg"
                          }`}
                        >
                          Agendar publicação
                        </button>
                      </div>
                      {socialPublishMode === "schedule" ? (
                        <div className="grid gap-3 sm:grid-cols-2">
                          <div>
                            <label htmlFor="social-schedule-date" className="mb-1 block text-[14px] text-fg-muted">
                              Data
                            </label>
                            <input
                              id="social-schedule-date"
                              type="date"
                              value={socialDate}
                              disabled={controlsDisabled}
                              onChange={(e) => {
                                setSocialDate(e.target.value);
                                setSocialSaved(false);
                              }}
                              className="min-h-11 w-full rounded-lg border border-line-strong bg-canvas px-3 text-base text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:opacity-50"
                            />
                          </div>
                          <div>
                            <label htmlFor="social-schedule-time" className="mb-1 block text-[14px] text-fg-muted">
                              Hora
                            </label>
                            <input
                              id="social-schedule-time"
                              type="time"
                              value={socialTime}
                              disabled={controlsDisabled}
                              onChange={(e) => {
                                setSocialTime(e.target.value);
                                setSocialSaved(false);
                              }}
                              className="min-h-11 w-full rounded-lg border border-line-strong bg-canvas px-3 text-base text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:opacity-50"
                            />
                          </div>
                          <p className="text-[14px] text-fg-muted sm:col-span-2">
                            Horário em America/Sao_Paulo.
                          </p>
                          {scheduleError ? (
                            <p role="alert" className="text-[14px] text-danger sm:col-span-2">
                              {scheduleError}
                            </p>
                          ) : null}
                        </div>
                      ) : null}
                    </div>

                    <div className="flex flex-wrap gap-3">
                      <button
                        type="button"
                        onClick={() => void handleSaveDraft()}
                        disabled={controlsDisabled || !token}
                        className="min-h-11 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover disabled:opacity-50"
                      >
                        {isSaving ? "Salvando rascunho..." : "Salvar rascunho"}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          if (socialText.trim()) {
                            setShowRegenConfirm(true);
                          } else {
                            void handleGenerate(false);
                          }
                        }}
                        disabled={controlsDisabled || !token}
                        className="min-h-11 rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft disabled:opacity-50"
                      >
                        {isGenerating ? "Regenerando rascunho..." : "Regenerar com IA"}
                      </button>
                    </div>

                    {isDirty ? (
                      <p className="text-[14px] text-fg-muted">
                        Salve o rascunho para usar este texto na aprovação.
                      </p>
                    ) : null}

                    <div>
                      <h4 className="mb-2 text-[14px] font-semibold text-fg">Prévia do post</h4>
                      <div className="rounded-lg border border-line bg-canvas p-3">
                        <p className="whitespace-pre-wrap text-base text-fg [overflow-wrap:anywhere]">
                          {socialText || "—"}
                        </p>
                        {previewLink ? (
                          <p className="mt-3 whitespace-pre-wrap text-[14px] text-accent-soft [overflow-wrap:anywhere]">
                            {previewLink}
                          </p>
                        ) : null}
                      </div>
                    </div>
                  </div>
                ) : null}

                {!hasSocialDraftContent && socialActionError && !siteUrlIssue ? (
                  <p role="alert" className="mt-3 text-[14px] text-danger-soft">
                    {socialActionError}
                  </p>
                ) : null}
                {!hasSocialDraftContent && siteUrlIssue ? (
                  <p role="alert" className="mt-3 text-[14px] text-danger-soft">
                    {SITE_PUBLIC_URL_ERROR}
                  </p>
                ) : null}
              </section>

              {/* Post para Instagram (Phase 30, REVW-01..04, D-01..D-09) */}
              <section className="mt-6 border-t border-line pt-6">
                <h3 className="text-[20px] font-semibold leading-tight text-fg">
                  Post para Instagram
                </h3>

                {igAction === "load" ? (
                  <p className="mt-3 text-[14px] text-fg-muted">Carregando...</p>
                ) : null}

                {igLoadError ? (
                  <p role="alert" className="mt-3 text-[14px] text-danger-soft">
                    {igLoadError}
                  </p>
                ) : null}

                {!igReady ? (
                  <div className="mt-4 rounded-lg border border-line bg-canvas p-4">
                    <p className="text-[14px] font-semibold text-fg">
                      {igReadiness === undefined
                        ? "Verificando prontidão do Instagram"
                        : igReadiness?.state === "missing_linkage"
                          ? "Instagram não vinculado"
                          : igReadiness?.state === "missing_permissions"
                            ? "Permissões do Instagram ausentes"
                            : igReadiness?.state === "needs_reconnect"
                              ? "Reconexão necessária para o Instagram"
                              : "Instagram não está pronto para publicação"}
                    </p>
                    <p className="mt-2 text-[14px] text-fg-muted">
                      A seção está visível, mas a publicação no Instagram fica desabilitada até a integração estar pronta.
                    </p>
                    <p className="mt-2 text-[14px] text-fg-muted">
                      {igReadiness === undefined
                        ? "Carregando status da integração do Instagram..."
                        : igReadinessError ??
                          igReadiness?.message ??
                          "Não foi possível confirmar a prontidão do Instagram agora."}
                    </p>
                    <a
                      href="/admin/integracoes"
                      className="mt-2 inline-flex min-h-11 items-center text-[14px] font-medium text-accent-soft underline underline-offset-4 hover:text-accent"
                    >
                      Abrir Integrações
                    </a>
                  </div>
                ) : (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-lg border border-line bg-canvas p-4">
                      <h4 className="text-[16px] font-semibold text-fg">
                        Status da publicação no Instagram
                      </h4>

                      {igStatusLoading ? (
                        <p className="mt-2 text-[14px] text-fg-muted">Carregando...</p>
                      ) : !igStatus ? (
                        <div className="mt-2 space-y-2">
                          <span className="inline-flex items-center rounded-full border border-line bg-canvas px-3 py-1 text-[14px] text-fg-muted">
                            Sem rascunho
                          </span>
                          <p className="text-[14px] text-fg-muted">
                            Nenhum post social registrado para esta vaga.
                          </p>
                        </div>
                      ) : (
                        <div className="mt-2 space-y-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <span
                              className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-[14px] ${
                                igStatus.status === "failed"
                                  ? "border border-danger bg-[rgba(248,113,113,0.12)] text-danger-soft"
                                  : igStatus.status === "published"
                                    ? "border border-accent bg-[rgba(139,92,246,0.12)] text-fg"
                                    : igStatus.status === "publishing"
                                      ? "border border-accent/40 bg-[rgba(139,92,246,0.08)] text-fg"
                                      : igStatus.status === "scheduled"
                                        ? "border border-accent/40 bg-[rgba(139,92,246,0.08)] text-fg"
                                        : "border border-line bg-canvas text-fg-muted"
                              }`}
                            >
                              {igStatus.status === "publishing" ? (
                                <span
                                  className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-accent-soft border-t-transparent"
                                  aria-hidden="true"
                                />
                              ) : null}
                              {igStatus.status_label}
                            </span>
                          </div>

                          <p className="text-[14px] text-fg-muted">Tentativas: {igStatus.attempts}</p>

                          {igStatus.status === "scheduled" ? (
                            <p className="text-[14px] text-fg-muted">
                              {igStatus.scheduled_at
                                ? `Publicação agendada para ${formatBrtDateTime(igStatus.scheduled_at)} (America/Sao_Paulo).`
                                : "Publicação agendada."}
                            </p>
                          ) : null}

                          {igStatus.status === "publishing" ? (
                            <p className="text-[14px] text-fg-muted">
                              Publicação em andamento. Atualize em instantes para ver o resultado.
                            </p>
                          ) : null}

                          {igStatus.status === "published" ? (
                            <div className="space-y-1">
                              <p className="text-[14px] text-fg">Publicado no Instagram.</p>
                              {igStatus.published_at ? (
                                <p className="text-[14px] text-fg-muted">
                                  Publicado em {formatBrtDateTime(igStatus.published_at)} (America/Sao_Paulo).
                                </p>
                              ) : null}
                              {igStatus.published_permalink || igStatus.published_url ? (
                                <a
                                  href={(igStatus.published_permalink || igStatus.published_url) ?? "#"}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex min-h-11 items-center text-[14px] font-medium text-accent-soft underline-offset-4 hover:text-accent hover:underline"
                                >
                                  Ver post no Instagram
                                </a>
                              ) : (
                                <p className="text-[14px] text-fg-muted">
                                  Publicado no Instagram. Link indisponível.
                                </p>
                              )}
                            </div>
                          ) : null}

                          {igStatus.status === "failed" ? (
                            <p className="text-[14px] text-danger-soft">
                              {igStatus.last_error ||
                                "Não foi possível publicar este post. Tente novamente quando estiver disponível."}
                            </p>
                          ) : null}

                          {igStatus.status !== "failed" &&
                          igStatus.status !== "published" &&
                          igStatus.status !== "publishing" &&
                          igStatus.status !== "scheduled" &&
                          igStatus.status === "draft" ? (
                            <p className="text-[14px] text-fg-muted">
                              Rascunho salvo. Aprove a vaga para agendar ou publicar.
                            </p>
                          ) : null}

                          {igStatus.retry_block_reason ? (
                            <p className={igStatus.reconciliation_required ? "text-[14px] text-accent-soft" : "text-[14px] text-fg-muted"}>
                              {igStatus.retry_block_reason}
                            </p>
                          ) : null}

                          {igStatus.reconciliation_required ? (
                            <p className="text-[14px] text-fg-muted">
                              Reconciliação necessária: ao tentar novamente, o sistema verifica status/IDs conhecidos no Instagram antes de qualquer nova publicação.
                            </p>
                          ) : null}

                          {igStatus.external_post_id ? (
                            <p className="text-[14px] text-fg-muted [overflow-wrap:anywhere]">ID externo: {igStatus.external_post_id}</p>
                          ) : null}
                          {igStatus.ig_container_id ? (
                            <p className="text-[14px] text-fg-muted [overflow-wrap:anywhere]">Container IG: {igStatus.ig_container_id}</p>
                          ) : null}
                          {igStatus.ig_media_id ? (
                            <p className="text-[14px] text-fg-muted [overflow-wrap:anywhere]">Mídia IG: {igStatus.ig_media_id}</p>
                          ) : null}
                          {igStatus.ig_last_reconciled_at ? (
                            <p className="text-[14px] text-fg-muted">
                              Última reconciliação IG: {formatBrtDateTime(igStatus.ig_last_reconciled_at)} (America/Sao_Paulo).
                            </p>
                          ) : null}

                          {igStatus.can_retry ? (
                            <button
                              type="button"
                              onClick={() => void handleRetryInstagram()}
                              disabled={retryingInstagram}
                              className="inline-flex min-h-11 items-center justify-center rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover disabled:opacity-50"
                            >
                              {retryingInstagram ? "Tentando novamente..." : "Tentar novamente"}
                            </button>
                          ) : null}
                        </div>
                      )}
                    </div>

                    <div className="rounded-lg border border-line bg-canvas p-4">
                      <label className="flex min-h-11 cursor-pointer items-start gap-3">
                        <input
                          type="checkbox"
                          checked={igEnabled}
                          disabled={busy || igBusy || igFrozen}
                          onChange={(e) => {
                            void handleIgToggle(e.target.checked);
                          }}
                          className="mt-1 h-5 w-5 rounded border-line-strong bg-canvas text-accent-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
                        />
                        <span>
                          <span className="block text-[14px] font-semibold text-fg">
                            Publicar no Instagram desta vaga
                          </span>
                          <span className="mt-1 block text-[14px] text-fg-muted">
                            {igEnabled
                              ? "Revise a legenda e a imagem do Instagram antes de aprovar com Instagram ativado."
                              : "Ative para editar a legenda e revisar a imagem do Instagram desta vaga."}
                          </span>
                        </span>
                      </label>
                      {igFrozen ? (
                        <p className="mt-3 text-[14px] text-fg-muted">
                          Texto bloqueado após aprovação. Este conteúdo não pode ser editado.
                        </p>
                      ) : null}
                    </div>

                    {igEnabled ? (
                      <>
                        <div>
                          <label
                            htmlFor="ig-caption"
                            className="mb-1 block text-[14px] font-semibold text-fg"
                          >
                            Legenda do Instagram
                          </label>
                          <textarea
                            id="ig-caption"
                            value={igCaption}
                            disabled={busy || igBusy || igFrozen}
                            onChange={(e) => {
                              setIgCaption(e.target.value);
                              setIgSaved(false);
                              setIgActionError(null);
                            }}
                            className="min-h-40 w-full resize-y rounded-lg border border-line-strong bg-canvas px-3 py-2 text-base text-fg placeholder:text-fg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
                          />
                          <div className="mt-1 flex flex-wrap items-center justify-between gap-2 text-[14px]">
                            <span className="text-fg-muted">
                              {/* Acceptance: Links na legenda não são clicáveis. Use "link na bio" como CTA. */}
                              Links na legenda não são clicáveis. Use &quot;link na bio&quot; como CTA.
                            </span>
                            <span className={igOverLimit ? "text-danger-soft" : "text-fg-muted"}>
                              {igCharCount}/2200 caracteres
                            </span>
                          </div>
                          {igOverLimit ? (
                            <p role="alert" className="mt-2 text-[14px] text-danger-soft">
                              A legenda do Instagram deve ter no máximo 2200 caracteres.
                            </p>
                          ) : null}
                          {igHashtagWarning ? (
                            <p className="mt-2 rounded-lg border border-accent/40 bg-[rgba(139,92,246,0.08)] p-3 text-[14px] text-fg-muted">
                              Você usou mais de 30 hashtags. Considere reduzir para melhorar a clareza da publicação.
                            </p>
                          ) : null}
                        </div>

                        <div className="flex flex-wrap gap-3">
                          <button
                            type="button"
                            onClick={() => void handleIgSave()}
                            disabled={!igCanSave}
                            className="min-h-11 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover disabled:opacity-50"
                          >
                            {igAction === "save" ? "Salvando rascunho..." : "Salvar rascunho"}
                          </button>
                          <button
                            type="button"
                            onClick={() => void handleIgGenerate()}
                            disabled={!igReady || busy || igBusy || igFrozen}
                            className="min-h-11 rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft disabled:opacity-50"
                          >
                            {igAction === "generate"
                              ? "Gerando legenda..."
                              : igDraft
                                ? "Regenerar legenda"
                                : "Gerar legenda"}
                          </button>
                        </div>

                        {igSaved && !igActionError ? (
                          <p className="text-[14px] text-fg-muted">Rascunho salvo.</p>
                        ) : null}

                        {igActionError ? (
                          <p role="alert" className="text-[14px] text-danger-soft">
                            {igActionError}
                          </p>
                        ) : null}

                        <div>
                          <h4 className="mb-2 text-[14px] font-semibold text-fg">
                            Prévia da imagem do Instagram
                          </h4>
                          <div className="rounded-lg border border-line bg-canvas p-3">
                            {igMediaLoading ? (
                              <p className="text-[14px] text-fg-muted">
                                Preparando imagem do Instagram...
                              </p>
                            ) : igMediaError ? (
                              <p role="alert" className="text-[14px] text-danger-soft">
                                {igMediaError}
                              </p>
                            ) : igMedia?.validation?.valid && igMedia.image_url ? (
                              <img
                                src={igMedia.image_url}
                                alt="Prévia da imagem do Instagram"
                                className="h-auto w-full max-w-[360px] rounded-lg border border-line"
                              />
                            ) : (
                              <p className="text-[14px] text-fg-muted">
                                Nenhuma prévia disponível. Ative a publicação no Instagram para preparar a imagem.
                              </p>
                            )}
                          </div>
                        </div>

                        {igEnabled && igImageInvalid ? (
                          <p role="alert" className="text-[14px] text-danger-soft">
                            Corrija a legenda ou a imagem do Instagram antes de salvar/publicar com Instagram ativado. O Facebook e o site não são bloqueados.
                          </p>
                        ) : null}

                        {igEnabled && (igOverLimit || igImageInvalid) ? (
                          <p className="text-[14px] text-fg-muted">
                            Corrija a legenda ou a imagem do Instagram antes de aprovar com Instagram ativado, ou desative a publicação no Instagram desta vaga. O Facebook e o site não são bloqueados.
                          </p>
                        ) : null}
                      </>
                    ) : null}
                  </div>
                )}
              </section>
            </div>

            <aside className="hidden md:block">
              <div className="sticky top-0">
                <SnippetPanel snippet={job?.source_snippet ?? null} />
              </div>
            </aside>
          </div>

          <footer className="flex shrink-0 items-center justify-end gap-3 border-t border-line p-4">
            <button
              type="button"
              onClick={close}
              disabled={saving || showRegenConfirm}
              className="min-h-11 rounded-lg border border-line-strong px-4 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="min-h-11 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover disabled:opacity-50"
            >
              {saving ? "Salvando..." : "Salvar alterações"}
            </button>
          </footer>
        </form>
      </dialog>

      <dialog
        ref={regenDialogRef}
        aria-labelledby="regen-dialog-title"
        onClose={() => setShowRegenConfirm(false)}
        onCancel={(e) => {
          e.preventDefault();
          setShowRegenConfirm(false);
        }}
        onClick={(event) => {
          if (event.target === regenDialogRef.current) setShowRegenConfirm(false);
        }}
        className="w-[min(92vw,520px)] rounded-[16px] border border-line bg-surface p-0 text-fg backdrop:bg-[rgba(5,2,12,.72)]"
      >
        <div className="space-y-4 p-6">
          <h3 id="regen-dialog-title" className="text-xl font-semibold">
            Regenerar rascunho
          </h3>
          <p className="text-[14px] text-fg-muted">
            Isso vai substituir o texto atual do rascunho. Deseja continuar?
          </p>
          <div className="flex flex-wrap justify-end gap-3">
            <button
              type="button"
              onClick={() => setShowRegenConfirm(false)}
              className="min-h-11 rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft"
            >
              Manter rascunho atual
            </button>
            <button
              type="button"
              onClick={() => void handleGenerate(true)}
              className="min-h-11 rounded-lg border border-danger bg-[rgba(248,113,113,0.12)] px-4 text-sm font-semibold text-danger-soft transition-colors hover:bg-[rgba(248,113,113,0.2)]"
            >
              Regenerar
            </button>
          </div>
        </div>
      </dialog>
    </>
  );
}

export default EditJobDialog;
