"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function OAuthCallback() {
  const router = useRouter()

  useEffect(() => {
    // Parse query parameters from the URL
    const query = new URLSearchParams(window.location.search)
    const token = query.get("token")
    const role = query.get("role")
    const name = query.get("name")
    const email = query.get("email")
    const businessId = query.get("business_id")
    const error = query.get("error")

    // If an error param is present (e.g., unverified_email), handle it
    if (error) {
      // Show an alert (could be replaced with UI toast later)
      alert(`Authentication error: ${error}`)
      router.replace("/login")
      return
    }

    if (!token) {
      // Missing token – cannot authenticate
      alert("Authentication token missing. Redirecting to login.")
      router.replace("/login")
      return
    }

    // Store auth details in localStorage (same keys as existing login flow)
    localStorage.setItem("token", token)
    if (role) localStorage.setItem("userRole", role)
    if (name) localStorage.setItem("userName", name)
    if (email) localStorage.setItem("userEmail", email)
    if (businessId) localStorage.setItem("userBusinessId", businessId)

    // TODO: Replace localStorage with httpOnly cookie based auth in a future iteration.

    // Redirect to inbox after successful sign‑in
    router.replace("/inbox")
  }, [router])

  // Simple UI while processing – could be a spinner or brand logo
  return (
    <div className="flex h-screen items-center justify-center bg-gray-100 dark:bg-gray-900">
      <p className="text-lg font-medium text-gray-700 dark:text-gray-200">
        Processing authentication...
      </p>
    </div>
  )
}
