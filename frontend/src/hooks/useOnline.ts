import { useEffect, useState } from "react";

/** Tracks browser connectivity. navigator.onLine is optimistic: a 3G bundle can be "online" with no throughput,
 *  so callers should still handle request failures by queueing. */
export function useOnline(): boolean {
  const [online, setOnline] = useState<boolean>(typeof navigator === "undefined" ? true : navigator.onLine);
  useEffect(() => {
    const up = () => setOnline(true);
    const down = () => setOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => {
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  }, []);
  return online;
}
