export async function sendProductString(rawString: string): Promise<any> {
  const url = new URL("http://localhost:8000/kgru-positions/parse");
  url.searchParams.append("user_input", rawString);

  try {
    const response = await fetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    console.log(response);

    if (!response.ok) {
      throw new Error(
        `Ошибка отправки данных: ${response.status} ${response.statusText}`
      );
    }

    return await response.json();
  } catch (error) {
    console.error("Произошла ошибка при запросе:", error);
    throw error; 
  }
}