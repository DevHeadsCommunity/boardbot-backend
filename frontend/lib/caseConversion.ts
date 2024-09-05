const snakeToCamel = (str: string) => str.replace(/([-_][a-z])/g, (group) => group.toUpperCase().replace(/[-_]/g, ""));
const camelToSnake = (str: string) => str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
export const deepCamelCase = (obj: any): any => {
  if (Array.isArray(obj)) {
    return obj.map(deepCamelCase);
  } else if (obj !== null && typeof obj === "object") {
    return Object.keys(obj).reduce((result, key) => {
      const camelKey = key.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
      result[camelKey] = deepCamelCase(obj[key]);
      return result;
    }, {} as any);
  }
  return obj;
};

type TransformerName = "snakeToCamel" | "camelToSnake";

const transformers: Record<TransformerName, (str: string) => string> = {
  snakeToCamel,
  camelToSnake,
};

export const transformKeys = <T extends Record<string, any>>(obj: T, transformerName: TransformerName): T => {
  if (typeof obj !== "object" || obj === null) {
    throw new Error("Input must be an object");
  }
  const transformer = transformers[transformerName];
  return Object.fromEntries(Object.entries(obj).map(([key, value]) => [transformer(key), value])) as T;
};
