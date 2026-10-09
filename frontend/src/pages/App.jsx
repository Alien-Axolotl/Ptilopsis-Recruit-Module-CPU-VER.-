import { useState, useEffect, useRef } from 'react'
import { API_BASE } from "../api";

function App() {

  const [health, setHealth] = useState('Unknown');
  const [working, setWorking] = useState(false);

  const scanController = useRef(null);

  const runScans = async (signal) => {
    while (!signal.aborted) {
      try {
        const response = await fetch(`${API_BASE}/scan`, { method: 'GET', cache: 'no-store', signal });

        if (!response.ok) {
          throw new Error(`Backend returned status: ${response.status}`);
        }

        const result = await response.json();
        if (signal.aborted) return;

        window.overlay?.update(result);
      } catch (error) {
        if (signal.aborted) return;
        console.error("Scan failed:", error);
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
    }
  };

  const toggleModule = () => {
    if (scanController.current) {
      scanController.current.abort();
      scanController.current = null;
      window.overlay?.close();
      setWorking(false);
    } else {
      scanController.current = new AbortController();
      runScans(scanController.current.signal);
      setWorking(true);
    }
  };

  const handleHealthCheck = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);

      if (!response.ok) {
        console.error(`Backend returned status: ${response.status}`);
        setHealth('Bad');
        return;
      }

      const data = await response.json();
      console.log("Backend is online:", data);
      setHealth('Good');

    } catch (error) {
      console.error("Couldn't reach the backend server:", error);
      setHealth('Bad');
    }
  };

  useEffect(() => {
    handleHealthCheck();

    const intervalId = setInterval(() => {
      handleHealthCheck();
    }, 5000);

    return () => {
      clearInterval(intervalId);
      scanController.current?.abort();
      scanController.current = null;
      window.overlay?.close();
    };
  }, []);

  return (
    <div className="flex flex-col items-center text-white gap-6 mt-3">

      <div className={`flex items-center justify-center h-32 w-96 px-4 text-2xl font-extrabold rounded-sm transition-all duration-300 ${
        health === 'Good' ? 'bg-green-300/20 ' : 'bg-red-900/40'
      }`}>
        {health === 'Good' ? 'Module Online, Doctor!' : 'Module Is Offline, Activating Sleep Mode :<'}
      </div>

      <div className="flex items-center justify-center h-32 w-96 px-4 text-2xl font-extrabold rounded-sm">
        <button onClick={toggleModule}>{working ? 'Module Working!' : 'Start Recruitment'}</button>
      </div>

    </div>
  )
}

export default App;