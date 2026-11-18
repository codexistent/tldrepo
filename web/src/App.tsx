import { useEffect } from "react";
// import { Button } from "./components/ui/button";
// import { cn } from "./lib/utils";
import { Link, Route, Routes } from "react-router";
import HomePage from "./pages/HomePage";
import TourPage from "./pages/TourPage";

function App() {
  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/api/health`)
      .then((res) => res.json())
      .then((data) => console.log("Health status:", data))
      .catch((err) => console.error("Health check failed:", err));
  }, []);

  return (
    <>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/tour/:owner/:repo" element={<TourPage />} />
        <Route
          path="*"
          element={
            <main className="mx-auto max-w-xl px-4 py-16 text-center">
              <p className="mb-4">Page not found.</p>
              <Link to="/" className="underline">
                Back home
              </Link>
            </main>
          }
        ></Route>
      </Routes>
    </>
  );
}

export default App;
