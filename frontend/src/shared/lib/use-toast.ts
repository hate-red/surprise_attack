"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const TOAST_DURATION_MS = 2800;

export function useToast() {
  const [message, setMessage] = useState("");
  const timerRef = useRef<number | undefined>(undefined);

  const showToast = useCallback((text: string) => {
    window.clearTimeout(timerRef.current);
    setMessage(text);
    timerRef.current = window.setTimeout(() => setMessage(""), TOAST_DURATION_MS);
  }, []);

  useEffect(() => () => window.clearTimeout(timerRef.current), []);

  return { message, showToast };
}
