"use client";

import { useEffect, useRef, useState } from "react";
import { Turnstile } from "next-turnstile";

import {
  revealContact,
  RevealError,
  type ContactRevealResponse,
  type JobPublic,
} from "@/lib/api";
import { getCachedContact, setCachedContact } from "@/lib/contact-cache";
import { mailtoHref, waHref } from "@/lib/contacts";

import { Whatsapp } from "./icons";

/**
 * Reveal the contact behind the Turnstile gate (PUBL-04, UI-SPEC §E, D-10).
 *
 * State machine: `idle → verifying → revealed | error(403|429|404|network|timeout)`.
 * Hard rules enforced here:
 * - no contact value reaches the DOM before `revealed` (not hidden, not in a
 *   `data-*` attribute) — PUBL-05/T-04-13;
 * - the widget mounts only while `verifying`, with `action="reveal"` and a
 *   distinct `id`, and is remounted through a React key after every failure so
 *   a consumed, single-use token is never sent twice (T-04-12);
 * - the revealed contact lives in the module-scope tab cache, never storage
 *   or the URL, and a closing dialog discards a late response.
 */

const TURNSTILE_SITE_KEY =
  process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ||
  (process.env.NODE_ENV === "production" ? "" : "1x00000000000000000000AA");

const NETWORK_COPY =
  "Falha de conexão. Verifique sua internet e tente novamente.";
const TIMEOUT_COPY =
  "Não foi possível concluir a verificação. Tente novamente.";
const MISSING_KEY_COPY =
  "Configuração ausente: defina NEXT_PUBLIC_TURNSTILE_SITE_KEY";
const NO_CONTACT_COPY = "Contato não disponível para esta vaga.";

const PRIMARY_BUTTON =
  "inline-flex h-12 w-full items-center justify-center gap-2 rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft";
const SECONDARY_BUTTON =
  "inline-flex h-12 w-full items-center justify-center gap-2 rounded-lg border border-line-strong bg-transparent px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft";
const DISABLED_BUTTON = `${PRIMARY_BUTTON} cursor-not-allowed opacity-50`;
const ERROR_PANEL =
  "rounded-lg border border-danger bg-[rgba(248,113,113,0.10)] p-3 text-sm leading-relaxed text-danger-soft [overflow-wrap:anywhere]";

type Phase = "idle" | "verifying" | "revealed" | "error";
type ErrorKind = "403" | "429" | "404" | "network" | "timeout";

interface RevealContactProps {
  job: JobPublic;
  /** Closing from the 404 state — the same close path as the dialog X. */
  onClose: () => void;
}

export function RevealContact({ job, onClose }: RevealContactProps) {
  const cached = getCachedContact(job.id);

  const [phase, setPhase] = useState<Phase>(cached ? "revealed" : "idle");
  const [contact, setContact] = useState<ContactRevealResponse | null>(cached);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorKind, setErrorKind] = useState<ErrorKind | null>(null);
  const [cooldown, setCooldown] = useState(0);
  // Bumped on every failure: next-turnstile has no reset API, so a new React
  // key is what discards the consumed token (D-10/T-04-12).
  const [revealKey, setRevealKey] = useState(0);

  const previousJobId = useRef(job.id);
  // Cancellation guard: the fetch has its own timeout, but a dialog closed
  // mid-verification must not resurrect a contact (UI-SPEC §D).
  const requestRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const jobChanged = previousJobId.current !== job.id;
    previousJobId.current = job.id;

    const nextCached = getCachedContact(job.id);
    setContact(nextCached);
    setPhase(nextCached ? "revealed" : "idle");
    setErrorMessage(null);
    setErrorKind(null);
    setCooldown(0);
    if (jobChanged) {
      setRevealKey((key) => key + 1);
    }
  }, [job.id]);

  useEffect(() => {
    return () => {
      requestRef.current?.abort();
    };
  }, []);

  const cooling = cooldown > 0;

  useEffect(() => {
    if (!cooling) {
      return;
    }
    const timer = window.setInterval(() => {
      setCooldown((value) => (value <= 1 ? 0 : value - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [cooling]);

  const startVerification = () => {
    setErrorMessage(null);
    setErrorKind(null);
    setCooldown(0);
    setPhase("verifying");
  };

  /** Turnstile expired/errored, or the 15 s token budget ran out. */
  const failVerification = () => {
    requestRef.current?.abort();
    setErrorMessage(TIMEOUT_COPY);
    setErrorKind("timeout");
    setRevealKey((key) => key + 1);
    setPhase("error");
  };

  const handleVerify = async (token: string) => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;

    try {
      const response = await revealContact(job.id, token);
      if (controller.signal.aborted) {
        return;
      }
      // A swapped response is treated as a failed round-trip and never cached
      // (UI-SPEC §E).
      if (response.job_id !== job.id) {
        throw new RevealError("network", {
          status: 0,
          kind: "network",
          retryAfter: null,
        });
      }
      setCachedContact(job.id, response);
      setContact(response);
      setPhase("revealed");
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }
      const revealError =
        error instanceof RevealError
          ? error
          : new RevealError("network", {
              status: 0,
              kind: "network",
              retryAfter: null,
            });

      if (revealError.kind === "timeout") {
        setErrorMessage(TIMEOUT_COPY);
        setErrorKind("timeout");
        setRevealKey((key) => key + 1);
        setPhase("error");
        return;
      }
      if (revealError.kind === "network") {
        setErrorMessage(NETWORK_COPY);
        setErrorKind("network");
        setRevealKey((key) => key + 1);
        setPhase("error");
        return;
      }

      // HTTP failures: the backend `detail` is rendered verbatim (pt-BR).
      switch (revealError.status) {
        case 403:
          setErrorMessage(revealError.message);
          setErrorKind("403");
          setRevealKey((key) => key + 1);
          break;
        case 429:
          setErrorMessage(revealError.message);
          setErrorKind("429");
          setCooldown(revealError.retryAfter ?? 10);
          break;
        case 404:
          setErrorMessage(revealError.message);
          setErrorKind("404");
          break;
        default:
          // Unexpected status: keep the verbatim detail and offer a retry.
          setErrorMessage(revealError.message);
          setErrorKind("network");
          setRevealKey((key) => key + 1);
          break;
      }
      setPhase("error");
    }
  };

  if (phase === "revealed") {
    const phone = contact?.contact_phone?.trim() ? contact.contact_phone : null;
    const email = contact?.contact_email?.trim() ? contact.contact_email : null;
    const phoneHref = phone ? waHref(phone, job.title) : null;
    const emailHref = email ? mailtoHref(email, job.title) : null;

    if (!phoneHref && !emailHref && !phone && !email) {
      return (
        <p className="text-sm leading-relaxed text-fg-muted">
          {NO_CONTACT_COPY}
        </p>
      );
    }

    return (
      <div className="flex flex-col gap-2">
        <div className="flex flex-col gap-1">
          {phone ? (
            <p className="text-base font-semibold text-accent-soft [overflow-wrap:anywhere]">
              {phone}
            </p>
          ) : null}
          {email ? (
            <p className="text-base font-semibold text-accent-soft [overflow-wrap:anywhere]">
              {email}
            </p>
          ) : null}
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          {phoneHref ? (
            <a
              href={phoneHref}
              target="_blank"
              rel="noopener noreferrer"
              className={PRIMARY_BUTTON}
            >
              <Whatsapp size={20} />
              WhatsApp
            </a>
          ) : null}
          {emailHref ? (
            <a href={emailHref} className={SECONDARY_BUTTON}>
              Enviar e-mail
            </a>
          ) : null}
        </div>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="flex flex-col gap-2">
        <p role="alert" className={ERROR_PANEL}>
          {errorMessage ?? NETWORK_COPY}
        </p>
        {errorKind === "404" ? (
          <button type="button" onClick={onClose} className={SECONDARY_BUTTON}>
            Fechar
          </button>
        ) : errorKind === "429" ? (
          <button type="button" disabled className={DISABLED_BUTTON}>
            Aguarde {cooldown}s
          </button>
        ) : (
          <button
            type="button"
            onClick={startVerification}
            className={SECONDARY_BUTTON}
          >
            Tentar novamente
          </button>
        )}
      </div>
    );
  }

  if (phase === "verifying") {
    return (
      <div className="flex flex-col gap-2">
        <button type="button" disabled className={DISABLED_BUTTON}>
          Verificando...
        </button>
        {TURNSTILE_SITE_KEY ? (
          <div
            className="w-full"
            style={{ minWidth: 300, maxWidth: "100%" }}
          >
            <Turnstile
              key={revealKey}
              siteKey={TURNSTILE_SITE_KEY}
              action="reveal"
              theme="dark"
              appearance="interaction-only"
              id="turnstile-reveal"
              onVerify={handleVerify}
              onExpire={failVerification}
              onError={failVerification}
            />
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <p role="alert" className={ERROR_PANEL}>
              {MISSING_KEY_COPY}
            </p>
            <button
              type="button"
              onClick={() => setPhase("idle")}
              className={SECONDARY_BUTTON}
            >
              Voltar
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <button type="button" onClick={startVerification} className={PRIMARY_BUTTON}>
      Mostrar contato
    </button>
  );
}
