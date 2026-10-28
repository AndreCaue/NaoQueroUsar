"use client";

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type RefObject,
} from "react";

import { useToast } from "@/components/admin/ToastProvider";
import { X } from "@/components/admin/icons";
import { updateJob, type JobAdmin, type JobUpdate } from "@/lib/api";
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
 * EditJobDialog — modal de edição de vaga (REVW-03, REVW-05).
 *
 * `<dialog>` nativo (foco, ESC, backdrop). Desktop: grid form + snippet
 * sticky; mobile: form empilhado + snippet em accordion. A validação local
 * espelha o backend (título, cidade do conjunto, ao menos um contato).
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
  const { toast } = useToast();
  const [form, setForm] = useState<FormState>(() => toFormState(job));
  const [errors, setErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);

  // Reset on every open, not just when the object identity changes: reopening
  // the same row after "Cancelar" must discard the abandoned edits (CR-01).
  useEffect(() => {
    if (!open) return;
    setForm(toFormState(job));
    setErrors({});
  }, [job, open]);

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

  const close = () => dialogRef.current?.close();

  const validate = (): boolean => {
    const next: FormErrors = {};
    if (!form.title.trim()) next.title = "Título é obrigatório.";
    // A legacy row can carry a city outside CITY_OPTIONS. Keep it editable
    // (payload falls back to job.city) instead of blocking every save.
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

  return (
    <dialog
      ref={dialogRef}
      tabIndex={-1}
      aria-labelledby="edit-job-title"
      onClose={onClose}
      onCancel={(event) => {
        if (saving) event.preventDefault();
      }}
      onClick={(event) => {
        if (saving) return;
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
            disabled={saving}
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
            disabled={saving}
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
  );
}

export default EditJobDialog;
