export type UserRole = "admin" | "staff";

export type Gender = "male" | "female" | "other" | "undisclosed";

export type AppointmentStatus =
  | "scheduled"
  | "confirmed"
  | "completed"
  | "cancelled"
  | "no_show";

export type AppointmentType =
  | "consultation"
  | "check_up"
  | "follow_up"
  | "other";

export type FollowUpStatus = "upcoming" | "completed";

export interface Clinic {
  id: number;
  name: string;
}

export interface User {
  id: number;
  clinic_id: number;
  full_name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface Patient {
  id: number;
  clinic_id: number;
  full_name: string;
  date_of_birth: string | null;
  gender: Gender | null;
  phone: string | null;
  email: string | null;
  created_at: string;
}

export interface PatientSummary {
  id: number;
  full_name: string;
  phone: string | null;
}

export interface Appointment {
  id: number;
  clinic_id: number;
  patient_id: number;
  scheduled_at: string;
  appointment_type: AppointmentType;
  status: AppointmentStatus;
  notes: string | null;
  created_at: string;
  patient?: PatientSummary;
}

export interface FollowUp {
  id: number;
  clinic_id: number;
  patient_id: number;
  appointment_id: number | null;
  follow_up_date: string;
  reason: string;
  status: FollowUpStatus;
  is_overdue: boolean;
  is_due_today: boolean;
  created_at: string;
  patient?: PatientSummary;
}

export interface GroupedFollowUps {
  overdue: FollowUp[];
  due_today: FollowUp[];
  upcoming: FollowUp[];
  completed: FollowUp[];
}

export interface DashboardMetrics {
  total_patients: number;
  appointments_today: number;
  upcoming_appointments: number;
  follow_ups_overdue: number;
  follow_ups_due_today: number;
  follow_ups_needing_attention: number;
}

export interface DashboardData {
  metrics: DashboardMetrics;
  today_schedule: Appointment[];
  weekly_activity: { date: string; count: number }[];
  attention_follow_ups: FollowUp[];
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export type ApiSuccess<T> = {
  success: true;
  data: T;
  message?: string;
  meta?: PaginationMeta;
};

export type ApiFailure = {
  success: false;
  message: string;
  errors?: Record<string, string>;
};

export type ApiResponse<T> = ApiSuccess<T> | ApiFailure;

export interface AuthPayload {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  clinic?: Clinic;
}

export interface Session {
  user: User;
  clinic: Clinic;
}
