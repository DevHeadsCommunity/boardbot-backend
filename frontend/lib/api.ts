const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://192.168.93.59:5678";
import { transformKeys } from "@/lib/caseConversion";

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

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const responseData = await response.json();
  return transformKeys(responseData, "snakeToCamel");
};
