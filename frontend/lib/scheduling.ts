/**
 * Client-side mirror of the API's scheduling rules
 * (backend/app/services/scheduling_rules.py).
 *
 * The API is the authority and rejects anything that breaks a rule; these
 * helpers only stop the UI from offering actions or dates the API would
 * refuse. Keep the numbers in step with the backend.
 */

import type { Appointment, AppointmentStatus } from "@/types/api";

const HOUR_MS = 60 * 60 * 1000;

/** A booking may start up to an hour ago (walk-ins). */
export const BOOKING_GRACE_MS = HOUR_MS;

/** A visit may be marked completed up to an hour before its booked start. */
export const EARLY_COMPLETION_GRACE_MS = HOUR_MS;

/** Finished appointments keep their date, time and type; notes stay editable. */
export const LOCKED_STATUSES: ReadonlySet<AppointmentStatus> = new Set([
  "completed",
  "cancelled",
  "no_show",
]);

export function isLocked(appointment: Appointment): boolean {
  return LOCKED_STATUSES.has(appointment.status);
}

/**
 * Whether moving to this status agrees with when the visit is booked.
 * Completed and no-show assert the visit has happened, so they are not
 * offered for a visit still in the future.
 */
export function statusAllowedNow(
  appointment: Appointment,
  status: AppointmentStatus,
  now = Date.now(),
): boolean {
  const startsAt = new Date(appointment.scheduled_at).getTime();
  if (status === "completed") return startsAt <= now + EARLY_COMPLETION_GRACE_MS;
  if (status === "no_show") return startsAt <= now;
  return true;
}

const pad = (n: number) => String(n).padStart(2, "0");

/** A Date as the value a datetime-local input expects, in local time. */
export function toLocalDateTimeValue(date: Date): string {
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

/** Earliest bookable moment, as a datetime-local `min`. */
export function minBookingValue(now = new Date()): string {
  return toLocalDateTimeValue(new Date(now.getTime() - BOOKING_GRACE_MS));
}

/** Today's local date, as a date input `min` (not UTC's date). */
export function todayValue(now = new Date()): string {
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}
