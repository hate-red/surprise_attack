// src/entities/product/api/sendProductString.ts

export async function sendProductString(rawString: string): Promise<any> {
  const response = await fetch("https://api.example.com/products/parse", {
    method: "POST",
    headers: {
      "Content-Type": "text/plain;charset=utf-8",
    },
    body: rawString,
  });

  if (!response.ok) {
    throw new Error(
      `Ошибка отправки данных: ${response.status} ${response.statusText}`,
    );
  }

  // Возвращаем результат (json или текст, в зависимости от вашего API)
  return response.json();
}
