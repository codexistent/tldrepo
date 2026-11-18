import { useEffect } from "react";
// import { Button } from "./components/ui/button";
// import { cn } from "./lib/utils";
import { Route, Routes } from "react-router";
import Home from "./pages/HomePage";

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
        <Route path="/" element={<Home />} />
      </Routes>
    </>
  );
}

export default App;
