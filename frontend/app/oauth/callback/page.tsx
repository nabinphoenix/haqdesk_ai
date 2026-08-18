"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function OAuthCallback() {
  const router = useRouter()

  useEffect(() => {
    // Parse query parameters from the URL
    const query = new URLSearchParams(window.location.search)
    const code = query.get("code")
    const error = query.get("error")

    // If an error param is present (e.g., unverified_email), handle it
    if (error) {
      const messages: Record<string, string> = {
        invite_email_mismatch: "Please choose the Google account that matches the email address in your invitation.",
        invalid_invitation: "This invitation is invalid, revoked, or has already been used.",
        expired_invitation: "This invitation has expired. Ask your business administrator for a new one.",
        email_already_registered: "An account already exists for this email. Sign in instead or ask your administrator for help.",
        unverified_email: "Your Google email address is not verified.",
        oauth_failed: "Google authentication could not be completed.",
      }
      alert(messages[error] || `Authentication error: ${error}`)
      router.replace("/login")
      return
    }

    if (!code) {
      alert("Authentication code missing. Redirecting to login.")
      router.replace("/login")
      return
    }

    // Exchange the code for a token
    const exchangeCode = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const res = await fetch(`${API_URL}/api/v1/auth/oauth/exchange`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code })
        })

        if (res.ok) {
          const data = await res.json()
          
          localStorage.setItem("token", data.access_token)
          if (data.user.role) localStorage.setItem("userRole", data.user.role)
          if (data.user.name) localStorage.setItem("userName", data.user.name)
          if (data.user.email) localStorage.setItem("userEmail", data.user.email)
          if (data.user.business_id) localStorage.setItem("userBusinessId", data.user.business_id)
          
          const role = data.user.role
          if (role === "super_admin") router.replace("/super-admin")
          else if (role === "supervisor") router.replace("/supervisor")
          else if (role === "agent") router.replace("/agent")
          else router.replace("/inbox")
        } else {
          alert("Failed to exchange authentication code.")
          router.replace("/login")
        }
      } catch (err) {
        console.error("Exchange error:", err)
        alert("Network error during authentication.")
        router.replace("/login")
      }
    }

    exchangeCode()
  }, [router])

  // Simple UI while processing – could be a spinner or brand logo
  return (
    <div className="flex h-screen items-center justify-center bg-background dark:bg-surface">
      <p className="text-lg font-medium text-foreground">
        Processing authentication...
      </p>
    </div>
  )
}
