import { redirect } from "next/navigation";

/**
 * Temporary. The marketing landing page is built in Phase 10; until then
 * the root sends visitors to sign in.
 */
export default function HomePage() {
  redirect("/login");
}
