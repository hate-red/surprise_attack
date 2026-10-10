"use client";

import { sendProductString } from "@/entities/product/api/sendProductString";
import { useState } from "react";

export default function Input() {
  const [inputValue, setInputValue] = useState("");

  const handleSubmit = async () => {
    try {
      const result = await sendProductString(inputValue);
      console.log("Успешный ответ от бэкенда:", result);
    } catch (error) {
      console.error("Ошибка при отправке:", error);
    }
  };

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
        onClick={handleSubmit}
      >
        отправить
      </button>
    </>
  );
}
