import { Link, Outlet, useLocation } from "react-router-dom";

export default function Layout() {
  const location = useLocation();

  const navLink = (to: string, label: string) => {
    const active = location.pathname === to || (to === "/" && location.pathname === "/");
    return (
      <Link
        to={to}
        className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
          active ? "bg-gray-900 text-white" : "text-gray-700 hover:bg-gray-100"
        }`}
      >
        {label}
      </Link>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-lg font-semibold text-gray-900">
            Secure Code Reviewer
          </Link>
          <nav className="flex gap-2">
            {navLink("/", "Scans")}
            {navLink("/new", "New Scan")}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
