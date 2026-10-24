
import { signIn } from "@/auth";

export default function HomePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-white">
      <section className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
        <div className="mb-8">
          <p className="text-sm font-semibold tracking-[0.25em] text-cyan-400">
            RETURNGUARD
          </p>

          <h1 className="mt-4 text-3xl font-bold tracking-tight">
            Returns, handled intelligently.
          </h1>

          <p className="mt-3 leading-6 text-slate-400">
            A governed AI-powered platform for ecommerce returns,
            refund decisions, and human review.
          </p>
        </div>

        <div className="mb-6 rounded-xl border border-slate-800 bg-slate-950 p-4">
          <p className="font-medium">Secure sign-in</p>
          <p className="mt-1 text-sm text-slate-400">
            Sign in through your organization's identity provider.
          </p>
        </div>

        <form
          action={async () => {
            "use server";
            await signIn("keycloak", {
              redirectTo: "/dashboard",
            });
          }}
        >
          <button
            type="submit"
            className="w-full rounded-lg bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:ring-offset-2 focus:ring-offset-slate-900"
          >
            Sign in with Keycloak
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-500">
          Access is controlled by your assigned permissions.
        </p>
      </section>
    </main>
  );
}
