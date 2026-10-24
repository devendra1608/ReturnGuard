
"use client";

import { signOut } from "next-auth/react";

export default function SignOutButton() {
  async function handleSignOut() {
    // First clear the ReturnGuard/Auth.js session.
    await signOut({ redirect: false });

    // Then end the Keycloak SSO session.
    const logoutUrl = new URL(
      "http://localhost:8080/realms/returnguard/protocol/openid-connect/logout"
    );

    logoutUrl.searchParams.set("client_id", "returnguard-web");
    logoutUrl.searchParams.set(
      "post_logout_redirect_uri",
      window.location.origin
    );

    window.location.assign(logoutUrl.toString());
  }

  return (
    <button
      type="button"
      onClick={handleSignOut}
      className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
    >
      Sign out
    </button>
  );
}
