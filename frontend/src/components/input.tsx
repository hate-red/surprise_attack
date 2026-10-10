"use client";

import { sendProductString } from "@/entities/product/api/sendProductString";
import { useState } from "react";

export default function Input() {
  const [inputValue, setInputValue] = useState("");

  return (
    <>
      <textarea
        className="bg-red-300"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
      />

      <button
        className="bg-blue-200 cursor-pointer"
        type="submit"
        onClick={() => sendProductString(inputValue)}
      >
        отправить
      </button>
    </>
  );
}
