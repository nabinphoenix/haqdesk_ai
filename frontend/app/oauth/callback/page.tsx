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
      alert(`Authentication error: ${error}`)
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
          
          router.replace("/inbox")
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
    <div className="flex h-screen items-center justify-center bg-gray-100 dark:bg-gray-900">
      <p className="text-lg font-medium text-gray-700 dark:text-gray-200">
        Processing authentication...
      </p>
    </div>
  )
}
