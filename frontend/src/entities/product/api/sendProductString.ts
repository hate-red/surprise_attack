export async function sendProductString(rawString: string): Promise<any> {
  const response = await fetch("http://127.0.0.1:8000/api/v1/parse-message", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message: rawString }),
  });

  if (!response.ok) {
    throw new Error(
      `Ошибка отправки данных: ${response.status} ${response.statusText}`,
    );
  }

  return response.json();
}