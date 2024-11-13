/**
 * Returns a CSS color class based on a score value
 * @param value Score between 0 and 1, or undefined
 * @returns CSS class name for text color
 */
export const getScoreColor = (value: number | undefined) => {
  if (value === undefined) return "";
  const score = value * 100;
  if (score >= 90) return "text-green-600";
  if (score >= 70) return "text-yellow-600";
  return "text-red-600";
};
