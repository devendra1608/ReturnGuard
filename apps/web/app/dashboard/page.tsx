
import { auth } from "@/auth";
import { redirect } from "next/navigation";
import SignOutButton from "@/app/components/sign-out-button";


export const instant = false;

export default async function DashboardPage() {
  const session = await auth();

  if (!session?.user) {
    redirect("/");
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">
      <section className="mx-auto max-w-4xl">
        <div className="flex items-center justify-between gap-4">
          <p className="text-sm font-semibold tracking-[0.25em] text-cyan-400">
            RETURNGUARD
          </p>

          <SignOutButton />
        </div>

        <h1 className="mt-8 text-3xl font-bold">
          Welcome to your dashboard
        </h1>

        <p className="mt-3 text-slate-400">
          You are signed in successfully.
        </p>

        <div className="mt-8 rounded-xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm text-slate-400">Signed in as</p>

          <p className="mt-2 font-medium">
            {session.user.name ??
              session.user.email ??
              "Authenticated user"}
          </p>
        </div>

      </section>
    </main>
  );
}
