import { transformKeys } from "@/lib/caseConversion";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;
if (!API_BASE_URL) {
  throw new Error("Missing env variable NEXT_PUBLIC_API_BASE_URL");
}

export const apiCall = async (method: string, endpoint: string, data?: any) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const options: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
    },
  };

  if (data) {
    options.body = JSON.stringify(transformKeys(data, "camelToSnake"));
  }

  const response = await fetch(url, options);

  let responseData;
  try {
    responseData = await response.json();
  } catch (error) {
    responseData = null;
  }

  if (!response.ok) {
    const errorMessage = responseData?.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return transformKeys(responseData, "snakeToCamel");
};
