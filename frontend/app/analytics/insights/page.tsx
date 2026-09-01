import { redirect } from "next/navigation";

export default function AnalyticsInsightsPage() {
  redirect("/analytics?view=insights");
}